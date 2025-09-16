"""
Data collectors for social media platforms
Simple and focused data collection
"""

import os
import praw
import requests
import logging
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv
try:
    from .database import Database
except ImportError:
    from database import Database

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RedditCollector:
    """Reddit data collector"""
    
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'social_analytics/1.0')
        )
    
    def collect(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Collect Reddit posts"""
        posts = []
        
        try:
            for submission in self.reddit.subreddit('all').search(query, limit=limit):
                post_data = {
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
                    'permalink': f"https://reddit.com{submission.permalink}"
                }
                posts.append(post_data)
            
            logger.info(f"Collected {len(posts)} Reddit posts for '{query}'")
            return posts
            
        except Exception as e:
            logger.error(f"Reddit collection failed: {e}")
            return []


class NewsCollector:
    """News API collector"""
    
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2/everything"
    
    def collect(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Collect news articles"""
        if not self.api_key:
            logger.warning("NEWS_API_KEY not configured")
            return []
        
        articles = []
        
        try:
            params = {
                'q': query,
                'apiKey': self.api_key,
                'pageSize': min(limit, 100),
                'sortBy': 'publishedAt',
                'language': 'en'
            }
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            for article in data.get('articles', []):
                article_data = {
                    'id': f"news_{hash(article.get('url', ''))}",
                    'title': article.get('title', ''),
                    'content': article.get('description', '') + ' ' + article.get('content', ''),
                    'author': article.get('author', 'Unknown'),
                    'url': article.get('url', ''),
                    'published_at': article.get('publishedAt', ''),
                    'source_name': article.get('source', {}).get('name', 'Unknown'),
                    'url_to_image': article.get('urlToImage', '')
                }
                articles.append(article_data)
            
            logger.info(f"Collected {len(articles)} news articles for '{query}'")
            return articles
            
        except Exception as e:
            logger.error(f"News collection failed: {e}")
            return []


class DataCollector:
    """Main data collector that orchestrates all sources"""
    
    def __init__(self):
        self.db = Database()
        self.reddit = RedditCollector()
        self.news = NewsCollector()
    
    def collect_all(self, queries: List[str], limit_per_source: int = 50) -> Dict[str, Any]:
        """Collect data from all sources for given queries"""
        results = {
            'total_collected': 0,
            'by_source': {},
            'errors': []
        }
        
        for query in queries:
            logger.info(f"Collecting data for query: '{query}'")
            
            # Collect Reddit data
            try:
                reddit_posts = self.reddit.collect(query, limit_per_source)
                stored_reddit = 0
                
                for post in reddit_posts:
                    if self.db.insert_raw_data('reddit', post['id'], post):
                        stored_reddit += 1
                
                results['by_source'].setdefault('reddit', 0)
                results['by_source']['reddit'] += stored_reddit
                results['total_collected'] += stored_reddit
                
            except Exception as e:
                error_msg = f"Reddit collection failed for '{query}': {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
            
            # Collect News data
            try:
                news_articles = self.news.collect(query, limit_per_source)
                stored_news = 0
                
                for article in news_articles:
                    if self.db.insert_raw_data('news', str(article['id']), article):
                        stored_news += 1
                
                results['by_source'].setdefault('news', 0)
                results['by_source']['news'] += stored_news
                results['total_collected'] += stored_news
                
            except Exception as e:
                error_msg = f"News collection failed for '{query}': {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.info(f"Collection complete. Total: {results['total_collected']} items")
        return results
    
    def close(self):
        """Close database connection"""
        self.db.close()


# Utility function for Airflow
def collect_social_media_data(queries: List[str] = None, limit_per_source: int = 50) -> Dict[str, Any]:
    """Function to be called by Airflow DAG"""
    if queries is None:
        queries = ['artificial intelligence', 'machine learning', 'data science', 'technology']
    
    collector = DataCollector()
    try:
        results = collector.collect_all(queries, limit_per_source)
        return results
    finally:
        collector.close()