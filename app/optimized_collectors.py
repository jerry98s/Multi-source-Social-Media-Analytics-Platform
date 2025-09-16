"""
Optimized data collectors with proper rate limiting and parallel processing
Maximizes data collection while respecting API limits
"""

import os
import praw
import requests
import logging
import asyncio
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from .rate_limiter import with_rate_limit, rate_limiter

try:
    from .database import Database
except ImportError:
    from database import Database

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class OptimizedRedditCollector:
    """Optimized Reddit collector with rate limiting and parallel processing"""
    
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'social_analytics/1.0')
        )
        
        # Configuration from environment
        self.max_posts_per_request = int(os.getenv('REDDIT_MAX_POSTS_PER_REQUEST', 100))
        self.parallel_requests = int(os.getenv('REDDIT_PARALLEL_REQUESTS', 3))
        self.popular_subreddits = [
            'all', 'popular', 'worldnews', 'technology', 'science', 
            'politics', 'business', 'sports', 'entertainment', 'gaming'
        ]
    
    @with_rate_limit('reddit')
    def _collect_from_subreddit(self, subreddit_name: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Collect posts from a specific subreddit"""
        posts = []
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Use different methods to get diverse data
            methods = [
                ('search', lambda: subreddit.search(query, limit=limit//3)),
                ('hot', lambda: subreddit.hot(limit=limit//3)),
                ('new', lambda: subreddit.new(limit=limit//3))
            ]
            
            for method_name, method_func in methods:
                try:
                    for submission in method_func():
                        post_data = self._extract_post_data(submission)
                        posts.append(post_data)
                except Exception as e:
                    logger.warning(f"Failed to collect from {subreddit_name} using {method_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to collect from subreddit {subreddit_name}: {e}")
            
        return posts
    
    def _extract_post_data(self, submission) -> Dict[str, Any]:
        """Extract structured data from Reddit submission"""
        return {
            'id': submission.id,
            'title': submission.title,
            'content': submission.selftext,
            'author': str(submission.author) if submission.author else '[deleted]',
            'url': submission.url,
            'created_utc': submission.created_utc,
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,
            'subreddit': str(submission.subreddit),
            'source': 'reddit',
            'collected_at': datetime.utcnow().isoformat(),
            'external_id': f"reddit_{submission.id}",
            'raw_data': {
                'permalink': submission.permalink,
                'is_self': submission.is_self,
                'over_18': submission.over_18,
                'spoiler': submission.spoiler,
                'locked': submission.locked,
                'stickied': submission.stickied
            }
        }
    
    def collect_parallel(self, query: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Collect data from multiple subreddits in parallel"""
        posts = []
        subreddits_to_search = self.popular_subreddits[:self.parallel_requests]
        
        logger.info(f"Starting parallel collection from {len(subreddits_to_search)} subreddits")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.parallel_requests) as executor:
            # Submit tasks for each subreddit
            future_to_subreddit = {
                executor.submit(
                    self._collect_from_subreddit, 
                    subreddit, 
                    query, 
                    self.max_posts_per_request
                ): subreddit 
                for subreddit in subreddits_to_search
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_subreddit):
                subreddit = future_to_subreddit[future]
                try:
                    subreddit_posts = future.result()
                    posts.extend(subreddit_posts)
                    logger.info(f"Collected {len(subreddit_posts)} posts from r/{subreddit}")
                except Exception as e:
                    logger.error(f"Error collecting from r/{subreddit}: {e}")
        
        # Remove duplicates based on external_id
        unique_posts = {}
        for post in posts:
            unique_posts[post['external_id']] = post
        
        final_posts = list(unique_posts.values())
        logger.info(f"Total unique posts collected: {len(final_posts)}")
        
        return final_posts


class OptimizedNewsCollector:
    """Optimized News API collector with rate limiting"""
    
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.base_url = 'https://newsapi.org/v2/everything'
        self.max_articles_per_request = int(os.getenv('NEWS_MAX_ARTICLES_PER_REQUEST', 100))
        self.daily_quota = int(os.getenv('NEWS_DAILY_QUOTA', 100))
        
        # Track daily usage
        self.daily_requests = 0
        self.last_reset_date = datetime.now().date()
    
    def _check_daily_quota(self) -> bool:
        """Check if we've exceeded daily quota"""
        current_date = datetime.now().date()
        
        # Reset counter if it's a new day
        if current_date != self.last_reset_date:
            self.daily_requests = 0
            self.last_reset_date = current_date
        
        return self.daily_requests < self.daily_quota
    
    @with_rate_limit('news')
    def _make_api_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make a single API request with rate limiting"""
        if not self._check_daily_quota():
            raise Exception(f"Daily quota exceeded ({self.daily_quota} requests)")
        
        params['apiKey'] = self.api_key
        params['pageSize'] = min(params.get('pageSize', 100), self.max_articles_per_request)
        
        response = requests.get(self.base_url, params=params, timeout=30)
        
        if response.status_code == 429:
            raise Exception("Rate limit exceeded")
        elif response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code}")
        
        self.daily_requests += 1
        return response.json()
    
    def collect(self, query: str, days_back: int = 7, max_articles: int = 500) -> List[Dict[str, Any]]:
        """Collect news articles with optimized parameters"""
        articles = []
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Collect in batches to maximize data while respecting limits
        batch_size = min(self.max_articles_per_request, max_articles)
        total_batches = (max_articles + batch_size - 1) // batch_size
        
        logger.info(f"Collecting news articles in {total_batches} batches")
        
        for page in range(1, total_batches + 1):
            try:
                params = {
                    'q': query,
                    'from': start_date.strftime('%Y-%m-%d'),
                    'to': end_date.strftime('%Y-%m-%d'),
                    'page': page,
                    'pageSize': batch_size,
                    'sortBy': 'publishedAt',
                    'language': 'en'
                }
                
                response_data = self._make_api_request(params)
                
                if 'articles' in response_data:
                    batch_articles = self._extract_article_data(response_data['articles'])
                    articles.extend(batch_articles)
                    logger.info(f"Collected {len(batch_articles)} articles from page {page}")
                
                # Check if we've reached the total available
                if response_data.get('totalResults', 0) <= len(articles):
                    break
                    
            except Exception as e:
                logger.error(f"Failed to collect news batch {page}: {e}")
                break
        
        logger.info(f"Total news articles collected: {len(articles)}")
        return articles
    
    def _extract_article_data(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """Extract structured data from news articles"""
        processed_articles = []
        
        for article in articles:
            if not article.get('title'):
                continue
                
            article_data = {
                'id': article.get('url', '').split('/')[-1][:50],  # Use URL slug as ID
                'title': article.get('title', ''),
                'content': article.get('description', ''),
                'author': article.get('author', 'Unknown'),
                'url': article.get('url', ''),
                'created_utc': self._parse_date(article.get('publishedAt')),
                'score': 0,  # News API doesn't provide engagement metrics
                'upvote_ratio': 0,
                'num_comments': 0,
                'subreddit': article.get('source', {}).get('name', 'news'),
                'source': 'news',
                'collected_at': datetime.utcnow().isoformat(),
                'external_id': f"news_{article.get('url', '').split('/')[-1][:50]}",
                'raw_data': {
                    'source_id': article.get('source', {}).get('id'),
                    'source_name': article.get('source', {}).get('name'),
                    'url_to_image': article.get('urlToImage'),
                    'content': article.get('content')
                }
            }
            processed_articles.append(article_data)
        
        return processed_articles
    
    def _parse_date(self, date_str: str) -> float:
        """Parse ISO date string to UTC timestamp"""
        try:
            if date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.timestamp()
        except Exception:
            pass
        return datetime.utcnow().timestamp()


class OptimizedDataCollector:
    """Main collector that orchestrates all data sources"""
    
    def __init__(self):
        self.reddit_collector = OptimizedRedditCollector()
        self.news_collector = OptimizedNewsCollector()
        self.database = Database()
    
    def collect_all_sources(self, query: str, reddit_limit: int = 1000, news_limit: int = 500) -> Dict[str, List[Dict[str, Any]]]:
        """Collect data from all sources in parallel"""
        logger.info(f"Starting data collection for query: '{query}'")
        
        results = {
            'reddit': [],
            'news': [],
            'total_collected': 0,
            'collection_time': datetime.utcnow().isoformat()
        }
        
        # Collect from Reddit and News in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit Reddit collection
            reddit_future = executor.submit(
                self.reddit_collector.collect_parallel, 
                query, 
                reddit_limit
            )
            
            # Submit News collection
            news_future = executor.submit(
                self.news_collector.collect, 
                query, 
                max_articles=news_limit
            )
            
            # Collect results
            try:
                results['reddit'] = reddit_future.result(timeout=300)  # 5 minute timeout
                logger.info(f"Reddit collection completed: {len(results['reddit'])} posts")
            except Exception as e:
                logger.error(f"Reddit collection failed: {e}")
            
            try:
                results['news'] = news_future.result(timeout=300)  # 5 minute timeout
                logger.info(f"News collection completed: {len(results['news'])} articles")
            except Exception as e:
                logger.error(f"News collection failed: {e}")
        
        results['total_collected'] = len(results['reddit']) + len(results['news'])
        logger.info(f"Total data collected: {results['total_collected']} items")
        
        return results
    
    def store_collected_data(self, data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Store collected data in database"""
        try:
            all_data = data['reddit'] + data['news']
            
            if not all_data:
                logger.warning("No data to store")
                return False
            
            # Store in bronze layer
            stored_count = 0
            for item in all_data:
                success = self.database.insert_raw_data(
                    source=item['source'],
                    external_id=item['external_id'],
                    data=item
                )
                if success:
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} items in database")
            
            return stored_count > 0
            
        except Exception as e:
            logger.error(f"Failed to store data: {e}")
            return False
