"""
Twitter data collector using Twitter API v2.
Collects tweets, user data, and engagement metrics.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import tweepy
from tweepy import Client

from .base_collector import BaseCollector


class TwitterCollector(BaseCollector):
    """Collector for Twitter data using Twitter API v2."""
    
    def __init__(self, bearer_token: str, api_key: str, api_secret: str, 
                 access_token: str, access_token_secret: str):
        super().__init__(name="twitter", rate_limit_delay=1.0, max_retries=3)
        
        # Twitter API credentials
        self.bearer_token = bearer_token
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        
        # Initialize Twitter client
        self.client = Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )
        
        # Rate limiting settings
        self.rate_limit_remaining = 300  # Default rate limit
        self.rate_limit_reset = None
        
    async def collect_data(self, query: str = None, user_id: str = None, 
                          limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """Collect Twitter data based on query or user ID."""
        try:
            if query:
                return await self._search_tweets(query, limit)
            elif user_id:
                return await self._get_user_tweets(user_id, limit)
            else:
                # Default to trending topics
                return await self._get_trending_tweets(limit)
                
        except Exception as e:
            self.logger.error(f"Error collecting Twitter data: {e}")
            raise
    
    async def _search_tweets(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search for tweets using a query string."""
        tweets = []
        
        try:
            # Use asyncio to run the synchronous Twitter API call
            loop = asyncio.get_event_loop()
            # Ensure limit is at least 10 (Twitter API requirement)
            actual_limit = max(min(limit, 100), 10)
            
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.search_recent_tweets(
                    query=query,
                    max_results=actual_limit,  # Twitter API v2 max is 100 per request
                    tweet_fields=['created_at', 'public_metrics', 'author_id', 'context_annotations'],
                    user_fields=['username', 'name', 'verified', 'public_metrics'],
                    expansions=['author_id'],  # Removed referenced_tweets as it's not in allowed list
                    place_fields=['country', 'country_code']
                )
            )
            
            if response.data:
                for tweet in response.data:
                    tweet_data = tweet._json
                    
                    # Get user data if available
                    user_data = {}
                    if response.includes and 'users' in response.includes:
                        user = next((u for u in response.includes['users'] if u.id == tweet.author_id), None)
                        if user:
                            user_data = user._json
                    
                    # Combine tweet and user data
                    combined_data = {
                        'tweet': tweet_data,
                        'user': user_data,
                        'source': 'twitter',
                        'collected_at': datetime.utcnow().isoformat()
                    }
                    
                    tweets.append(combined_data)
            
            self.logger.info(f"Collected {len(tweets)} tweets for query: {query}")
            
        except tweepy.TooManyRequests as e:
            self.logger.warning(f"Rate limit exceeded: {e}")
            # Wait for rate limit reset
            if self.rate_limit_reset:
                wait_time = self.rate_limit_reset - datetime.utcnow()
                if wait_time.total_seconds() > 0:
                    await asyncio.sleep(wait_time.total_seconds())
            raise
            
        except Exception as e:
            self.logger.error(f"Error searching tweets: {e}")
            raise
            
        return tweets
    
    async def _get_user_tweets(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get tweets from a specific user."""
        tweets = []
        
        try:
            loop = asyncio.get_event_loop()
            # Ensure limit is at least 10 (Twitter API requirement)
            actual_limit = max(min(limit, 100), 10)
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_users_tweets(
                    id=user_id,
                    max_results=actual_limit,
                    tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                    expansions=[]  # Removed referenced_tweets as it's not in allowed list
                )
            )
            
            if response.data:
                for tweet in response.data:
                    tweet_data = tweet._json
                    tweet_data['source'] = 'twitter'
                    tweet_data['collected_at'] = datetime.utcnow().isoformat()
                    tweets.append(tweet_data)
            
            self.logger.info(f"Collected {len(tweets)} tweets from user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error getting user tweets: {e}")
            raise
            
        return tweets
    
    async def _get_trending_tweets(self, limit: int) -> List[Dict[str, Any]]:
        """Get trending tweets (using a default query)."""
        # Use a trending hashtag or topic
        trending_queries = ['#technology', '#AI', '#data', '#python', '#machinelearning']
        
        all_tweets = []
        for query in trending_queries[:3]:  # Limit to 3 queries to avoid rate limits
            try:
                tweets = await self._search_tweets(query, limit // 3)
                all_tweets.extend(tweets)
            except Exception as e:
                self.logger.warning(f"Failed to get trending tweets for {query}: {e}")
                continue
        
        return all_tweets[:limit]
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Twitter data structure."""
        if not data:
            return False
            
        # Check if it's a tweet with user data
        if 'tweet' in data and 'user' in data:
            tweet = data['tweet']
            user = data['user']
            
            required_tweet_fields = ['id', 'text', 'created_at']
            required_user_fields = ['id', 'username']
            
            return all(field in tweet for field in required_tweet_fields) and \
                   all(field in user for field in required_user_fields)
        
        # Check if it's a standalone tweet
        elif 'id' in data and 'text' in data:
            return True
            
        return False
    
    def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Twitter data to standard format."""
        if 'tweet' in data and 'user' in data:
            # Data with user information
            tweet = data['tweet']
            user = data['user']
            
            return {
                'id': tweet['id'],
                'text': tweet['text'],
                'created_at': tweet['created_at'],
                'author_id': tweet.get('author_id'),
                'author_username': user.get('username'),
                'author_name': user.get('name'),
                'author_verified': user.get('verified', False),
                'retweet_count': tweet.get('public_metrics', {}).get('retweet_count', 0),
                'like_count': tweet.get('public_metrics', {}).get('like_count', 0),
                'reply_count': tweet.get('public_metrics', {}).get('reply_count', 0),
                'quote_count': tweet.get('public_metrics', {}).get('quote_count', 0),
                'source': 'twitter',
                'collected_at': data.get('collected_at'),
                'raw_data': data
            }
        else:
            # Standalone tweet data
            return {
                'id': data['id'],
                'text': data['text'],
                'created_at': data.get('created_at'),
                'author_id': data.get('author_id'),
                'source': 'twitter',
                'collected_at': data.get('collected_at'),
                'raw_data': data
            }
    
    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific user."""
        try:
            loop = asyncio.get_event_loop()
            user = await loop.run_in_executor(
                None,
                lambda: self.client.get_user(username=username)
            )
            
            if user.data:
                user_data = user.data._json
                user_data['source'] = 'twitter'
                user_data['collected_at'] = datetime.utcnow().isoformat()
                return user_data
                
        except Exception as e:
            self.logger.error(f"Error getting user info for {username}: {e}")
            
        return None
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information."""
        return {
            'remaining': self.rate_limit_remaining,
            'reset_time': self.rate_limit_reset,
            'source': 'twitter'
        }


# Factory function for creating Twitter collector from environment variables
def create_twitter_collector() -> TwitterCollector:
    """Create a Twitter collector using environment variables."""
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
    
    if not all([bearer_token, api_key, api_secret, access_token, access_token_secret]):
        raise ValueError("Missing Twitter API credentials in environment variables")
    
    return TwitterCollector(
        bearer_token=bearer_token,
        api_key=api_key,
        api_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )


if __name__ == "__main__":
    # Example usage
    async def main():
        try:
            collector = create_twitter_collector()
            
            # Test collection
            tweets = await collector.collect_with_retry(query="#python", limit=10)
            print(f"Collected {len(tweets)} tweets")
            
            # Print stats
            stats = collector.get_collection_stats()
            print(f"Collection stats: {stats}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(main())
