"""
Reddit data collector using PRAW (Python Reddit API Wrapper).
Collects posts, comments, and user data from specified subreddits.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import praw

from .base_collector import BaseCollector


class RedditCollector(BaseCollector):
    """Collector for Reddit data using PRAW."""
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str,
                 username: str = None, password: str = None):
        super().__init__(name="reddit", rate_limit_delay=1.0, max_retries=3)
        
        # Reddit API credentials
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self.username = username
        self.password = password
        
        # Initialize Reddit client
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=username,
            password=password
        )
        
        # Rate limiting settings
        self.rate_limit_remaining = 60  # Reddit's rate limit
        self.rate_limit_reset = None
        
    async def collect_data(self, subreddit: str = None, query: str = None,
                          limit: int = 100, post_type: str = 'hot', **kwargs) -> List[Dict[str, Any]]:
        """Collect Reddit data from subreddit or search query."""
        try:
            if subreddit:
                return await self._get_subreddit_posts(subreddit, limit, post_type)
            elif query:
                return await self._search_reddit(query, limit)
            else:
                # Default to popular posts from technology subreddits
                return await self._get_popular_posts(limit)
                
        except Exception as e:
            self.logger.error(f"Error collecting Reddit data: {e}")
            raise
    
    async def _get_subreddit_posts(self, subreddit: str, limit: int, post_type: str = 'hot') -> List[Dict[str, Any]]:
        """Get posts from a specific subreddit."""
        posts = []
        
        try:
            subreddit_obj = self.reddit.subreddit(subreddit)
            
            # Get posts based on type
            if post_type == 'hot':
                submission_list = subreddit_obj.hot(limit=limit)
            elif post_type == 'new':
                submission_list = subreddit_obj.new(limit=limit)
            elif post_type == 'top':
                submission_list = subreddit_obj.top(limit=limit)
            elif post_type == 'rising':
                submission_list = subreddit_obj.rising(limit=limit)
            else:
                submission_list = subreddit_obj.hot(limit=limit)
            
            # Convert to list to avoid generator issues
            submissions = list(submission_list)
            
            for submission in submissions:
                try:
                    post_data = {
                        'id': submission.id,
                        'title': submission.title,
                        'text': submission.selftext,
                        'url': submission.url,
                        'author': submission.author.name if submission.author else '[deleted]',
                        'subreddit': submission.subreddit.display_name,
                        'score': submission.score,
                        'upvote_ratio': submission.upvote_ratio,
                        'num_comments': submission.num_comments,
                        'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                        'is_self': submission.is_self,
                        'is_video': submission.is_video,
                        'over_18': submission.over_18,
                        'spoiler': submission.spoiler,
                        'stickied': submission.stickied,
                        'locked': submission.locked,
                        'source': 'reddit',
                        'collected_at': datetime.utcnow().isoformat()
                    }
                    
                    posts.append(post_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing submission {submission.id}: {e}")
                    continue
            
            self.logger.info(f"Collected {len(posts)} posts from r/{subreddit}")
            
        except Exception as e:
            self.logger.error(f"Error getting subreddit posts: {e}")
            raise
            
        return posts
    
    async def _search_reddit(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Reddit for posts matching a query."""
        posts = []
        
        try:
            # Search across all subreddits
            search_results = self.reddit.subreddit('all').search(query, limit=limit)
            
            for submission in search_results:
                try:
                    post_data = {
                        'id': submission.id,
                        'title': submission.title,
                        'text': submission.selftext,
                        'url': submission.url,
                        'author': submission.author.name if submission.author else '[deleted]',
                        'subreddit': submission.subreddit.display_name,
                        'score': submission.score,
                        'upvote_ratio': submission.upvote_ratio,
                        'num_comments': submission.num_comments,
                        'created_utc': datetime.fromtimestamp(submission.created_utc).isoformat(),
                        'is_self': submission.is_self,
                        'is_video': submission.is_video,
                        'over_18': submission.over_18,
                        'spoiler': submission.spoiler,
                        'stickied': submission.stickied,
                        'locked': submission.locked,
                        'source': 'reddit',
                        'collected_at': datetime.utcnow().isoformat()
                    }
                    
                    posts.append(post_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing search result {submission.id}: {e}")
                    continue
            
            self.logger.info(f"Collected {len(posts)} posts for search query: {query}")
            
        except Exception as e:
            self.logger.error(f"Error searching Reddit: {e}")
            raise
            
        return posts
    
    async def _get_popular_posts(self, limit: int) -> List[Dict[str, Any]]:
        """Get popular posts from technology-related subreddits."""
        tech_subreddits = ['technology', 'programming', 'datascience', 'MachineLearning', 'Python']
        
        all_posts = []
        posts_per_subreddit = limit // len(tech_subreddits)
        
        for subreddit in tech_subreddits:
            try:
                posts = await self._get_subreddit_posts(subreddit, posts_per_subreddit, 'hot')
                all_posts.extend(posts)
            except Exception as e:
                self.logger.warning(f"Failed to get posts from r/{subreddit}: {e}")
                continue
        
        return all_posts[:limit]
    
    async def get_comments(self, post_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get comments for a specific post."""
        comments = []
        
        try:
            submission = self.reddit.submission(id=post_id)
            submission.comment_sort = 'top'  # Sort by top comments
            submission.comments.replace_more(limit=0)  # Remove "load more comments" links
            
            for comment in submission.comments.list()[:limit]:
                try:
                    comment_data = {
                        'id': comment.id,
                        'post_id': post_id,
                        'text': comment.body,
                        'author': comment.author.name if comment.author else '[deleted]',
                        'score': comment.score,
                        'created_utc': datetime.fromtimestamp(comment.created_utc).isoformat(),
                        'parent_id': comment.parent_id,
                        'is_submitter': comment.is_submitter,
                        'distinguished': comment.distinguished,
                        'edited': comment.edited,
                        'source': 'reddit',
                        'collected_at': datetime.utcnow().isoformat()
                    }
                    
                    comments.append(comment_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing comment {comment.id}: {e}")
                    continue
            
            self.logger.info(f"Collected {len(comments)} comments for post {post_id}")
            
        except Exception as e:
            self.logger.error(f"Error getting comments for post {post_id}: {e}")
            raise
            
        return comments
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate Reddit data structure."""
        if not data:
            return False
            
        required_fields = ['id', 'title', 'author', 'subreddit', 'score']
        return all(field in data for field in required_fields)
    
    def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Reddit data to standard format."""
        return {
            'id': data['id'],
            'title': data['title'],
            'text': data.get('text', ''),
            'url': data.get('url', ''),
            'author': data['author'],
            'subreddit': data['subreddit'],
            'score': data['score'],
            'upvote_ratio': data.get('upvote_ratio', 0.0),
            'num_comments': data.get('num_comments', 0),
            'created_at': data.get('created_utc'),
            'engagement_score': self._calculate_engagement_score(data),
            'source': 'reddit',
            'collected_at': data.get('collected_at'),
            'raw_data': data
        }
    
    def _calculate_engagement_score(self, data: Dict[str, Any]) -> float:
        """Calculate engagement score based on upvotes and comments."""
        score = data.get('score', 0)
        comments = data.get('num_comments', 0)
        upvote_ratio = data.get('upvote_ratio', 0.5)
        
        # Weighted engagement score
        engagement_score = (score * upvote_ratio) + (comments * 2)
        return round(engagement_score, 2)
    
    async def get_subreddit_info(self, subreddit: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific subreddit."""
        try:
            subreddit_obj = self.reddit.subreddit(subreddit)
            
            subreddit_data = {
                'name': subreddit_obj.display_name,
                'title': subreddit_obj.title,
                'description': subreddit_obj.description,
                'public_description': subreddit_obj.public_description,
                'subscribers': subreddit_obj.subscribers,
                'active_user_count': subreddit_obj.active_user_count,
                'created_utc': datetime.fromtimestamp(subreddit_obj.created_utc).isoformat(),
                'over18': subreddit_obj.over18,
                'subreddit_type': subreddit_obj.subreddit_type,
                'source': 'reddit',
                'collected_at': datetime.utcnow().isoformat()
            }
            
            return subreddit_data
            
        except Exception as e:
            self.logger.error(f"Error getting subreddit info for r/{subreddit}: {e}")
            return None
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information."""
        return {
            'remaining': self.rate_limit_remaining,
            'reset_time': self.rate_limit_reset,
            'source': 'reddit'
        }


# Factory function for creating Reddit collector from environment variables
def create_reddit_collector() -> RedditCollector:
    """Create a Reddit collector using environment variables."""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'SocialMediaAnalytics/1.0')
    username = os.getenv('REDDIT_USERNAME')
    password = os.getenv('REDDIT_PASSWORD')
    
    if not all([client_id, client_secret]):
        raise ValueError("Missing Reddit API credentials in environment variables")
    
    return RedditCollector(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password
    )


if __name__ == "__main__":
    # Example usage
    async def main():
        try:
            collector = create_reddit_collector()
            
            # Test collection
            posts = await collector.collect_with_retry(subreddit="technology", limit=10)
            print(f"Collected {len(posts)} posts")
            
            # Print stats
            stats = collector.get_collection_stats()
            print(f"Collection stats: {stats}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(main())
