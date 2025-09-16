#!/usr/bin/env python3
"""
Unit tests for collectors module
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.collectors import RedditCollector, NewsCollector, DataCollector


class TestRedditCollector(unittest.TestCase):
    """Test RedditCollector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.reddit_collector = RedditCollector()
    
    def test_initialization(self):
        """Test RedditCollector initialization"""
        self.assertIsNotNone(self.reddit_collector.reddit)
    
    @patch('app.collectors.praw.Reddit')
    def test_reddit_initialization_with_env(self, mock_reddit):
        """Test Reddit initialization with environment variables"""
        with patch.dict(os.environ, {
            'REDDIT_CLIENT_ID': 'test_client_id',
            'REDDIT_CLIENT_SECRET': 'test_client_secret',
            'REDDIT_USER_AGENT': 'test_user_agent'
        }):
            collector = RedditCollector()
            mock_reddit.assert_called_once()
    
    @patch('app.collectors.praw.Reddit')
    def test_collect_method(self, mock_reddit):
        """Test collect method"""
        # Mock Reddit submission
        mock_submission = Mock()
        mock_submission.id = 'test_id'
        mock_submission.title = 'Test Title'
        mock_submission.selftext = 'Test content'
        mock_submission.author = 'test_author'
        mock_submission.url = 'https://example.com'
        mock_submission.created_utc = 1234567890
        mock_submission.score = 100
        mock_submission.upvote_ratio = 0.95
        mock_submission.num_comments = 50
        mock_submission.subreddit = 'test_subreddit'
        mock_submission.permalink = '/r/test/comments/test_id/test_title/'
        
        # Mock subreddit search
        mock_subreddit = Mock()
        mock_subreddit.search.return_value = [mock_submission]
        mock_reddit_instance = Mock()
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        collector = RedditCollector()
        collector.reddit = mock_reddit_instance
        
        # Test collection
        posts = collector.collect('test query', limit=1)
        
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]['id'], 'test_id')
        self.assertEqual(posts[0]['title'], 'Test Title')
        self.assertEqual(posts[0]['content'], 'Test content')
        self.assertEqual(posts[0]['author'], 'test_author')
        self.assertEqual(posts[0]['score'], 100)
    
    @patch('app.collectors.praw.Reddit')
    def test_collect_method_exception(self, mock_reddit):
        """Test collect method with exception"""
        mock_reddit_instance = Mock()
        mock_subreddit = Mock()
        mock_subreddit.search.side_effect = Exception("API Error")
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        mock_reddit.return_value = mock_reddit_instance
        
        collector = RedditCollector()
        collector.reddit = mock_reddit_instance
        
        posts = collector.collect('test query', limit=1)
        self.assertEqual(len(posts), 0)


class TestNewsCollector(unittest.TestCase):
    """Test NewsCollector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.news_collector = NewsCollector()
    
    def test_initialization(self):
        """Test NewsCollector initialization"""
        self.assertEqual(self.news_collector.base_url, "https://newsapi.org/v2/everything")
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key"""
        with patch.dict(os.environ, {}, clear=True):
            collector = NewsCollector()
            self.assertIsNone(collector.api_key)
    
    @patch('app.collectors.requests.get')
    def test_collect_method_success(self, mock_get):
        """Test successful collection"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'articles': [
                {
                    'title': 'Test Article',
                    'description': 'Test description',
                    'content': 'Test content',
                    'author': 'Test Author',
                    'url': 'https://example.com/article',
                    'publishedAt': '2024-01-01T00:00:00Z',
                    'source': {'name': 'Test Source'},
                    'urlToImage': 'https://example.com/image.jpg'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'NEWS_API_KEY': 'test_api_key'}):
            collector = NewsCollector()
            articles = collector.collect('test query', limit=1)
            
            self.assertEqual(len(articles), 1)
            self.assertEqual(articles[0]['title'], 'Test Article')
            self.assertEqual(articles[0]['author'], 'Test Author')
            self.assertIn('Test description', articles[0]['content'])
    
    @patch('app.collectors.requests.get')
    def test_collect_method_api_error(self, mock_get):
        """Test collection with API error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {'NEWS_API_KEY': 'test_api_key'}):
            collector = NewsCollector()
            articles = collector.collect('test query', limit=1)
            
            self.assertEqual(len(articles), 0)
    
    def test_collect_method_no_api_key(self):
        """Test collection without API key"""
        with patch.dict(os.environ, {}, clear=True):
            collector = NewsCollector()
            articles = collector.collect('test query', limit=1)
            
            self.assertEqual(len(articles), 0)


class TestDataCollector(unittest.TestCase):
    """Test DataCollector class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_collector = DataCollector()
    
    @patch('app.collectors.Database')
    def test_initialization(self, mock_database):
        """Test DataCollector initialization"""
        collector = DataCollector()
        self.assertIsNotNone(collector.reddit)
        self.assertIsNotNone(collector.news)
        mock_database.assert_called_once()
    
    @patch('app.collectors.RedditCollector')
    @patch('app.collectors.NewsCollector')
    @patch('app.collectors.Database')
    def test_collect_all_success(self, mock_db, mock_news, mock_reddit):
        """Test successful collection from all sources"""
        # Mock collectors
        mock_reddit_instance = Mock()
        mock_reddit_instance.collect.return_value = [
            {'id': 'reddit_1', 'title': 'Reddit Post 1'},
            {'id': 'reddit_2', 'title': 'Reddit Post 2'}
        ]
        mock_reddit.return_value = mock_reddit_instance
        
        mock_news_instance = Mock()
        mock_news_instance.collect.return_value = [
            {'id': 'news_1', 'title': 'News Article 1'},
            {'id': 'news_2', 'title': 'News Article 2'}
        ]
        mock_news.return_value = mock_news_instance
        
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.insert_raw_data.return_value = True
        mock_db.return_value = mock_db_instance
        
        collector = DataCollector()
        collector.reddit = mock_reddit_instance
        collector.news = mock_news_instance
        collector.db = mock_db_instance
        
        # Test collection
        results = collector.collect_all(['test query'], limit_per_source=2)
        
        self.assertEqual(results['total_collected'], 4)
        self.assertEqual(results['by_source']['reddit'], 2)
        self.assertEqual(results['by_source']['news'], 2)
        self.assertEqual(len(results['errors']), 0)
    
    @patch('app.collectors.RedditCollector')
    @patch('app.collectors.NewsCollector')
    @patch('app.collectors.Database')
    def test_collect_all_with_errors(self, mock_db, mock_news, mock_reddit):
        """Test collection with errors"""
        # Mock Reddit collector with error
        mock_reddit_instance = Mock()
        mock_reddit_instance.collect.side_effect = Exception("Reddit API Error")
        mock_reddit.return_value = mock_reddit_instance
        
        # Mock News collector success
        mock_news_instance = Mock()
        mock_news_instance.collect.return_value = [
            {'id': 'news_1', 'title': 'News Article 1'}
        ]
        mock_news.return_value = mock_news_instance
        
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.insert_raw_data.return_value = True
        mock_db.return_value = mock_db_instance
        
        collector = DataCollector()
        collector.reddit = mock_reddit_instance
        collector.news = mock_news_instance
        collector.db = mock_db_instance
        
        # Test collection
        results = collector.collect_all(['test query'], limit_per_source=1)
        
        self.assertEqual(results['total_collected'], 1)
        self.assertEqual(results['by_source']['news'], 1)
        self.assertEqual(len(results['errors']), 1)
        self.assertIn('Reddit collection failed', results['errors'][0])
    
    def test_close_method(self):
        """Test close method"""
        mock_db = Mock()
        collector = DataCollector()
        collector.db = mock_db
        
        collector.close()
        mock_db.close.assert_called_once()


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    @patch('app.collectors.DataCollector')
    def test_collect_social_media_data_function(self, mock_data_collector):
        """Test collect_social_media_data utility function"""
        from app.collectors import collect_social_media_data
        
        # Mock DataCollector
        mock_collector_instance = Mock()
        mock_collector_instance.collect_all.return_value = {
            'total_collected': 10,
            'by_source': {'reddit': 5, 'news': 5},
            'errors': []
        }
        mock_data_collector.return_value = mock_collector_instance
        
        # Test with default queries
        results = collect_social_media_data()
        
        self.assertEqual(results['total_collected'], 10)
        mock_collector_instance.collect_all.assert_called_once()
        mock_collector_instance.close.assert_called_once()
    
    @patch('app.collectors.DataCollector')
    def test_collect_social_media_data_with_custom_queries(self, mock_data_collector):
        """Test collect_social_media_data with custom queries"""
        from app.collectors import collect_social_media_data
        
        # Mock DataCollector
        mock_collector_instance = Mock()
        mock_collector_instance.collect_all.return_value = {
            'total_collected': 5,
            'by_source': {'reddit': 3, 'news': 2},
            'errors': []
        }
        mock_data_collector.return_value = mock_collector_instance
        
        # Test with custom queries
        custom_queries = ['python', 'machine learning']
        results = collect_social_media_data(queries=custom_queries, limit_per_source=10)
        
        self.assertEqual(results['total_collected'], 5)
        mock_collector_instance.collect_all.assert_called_once_with(custom_queries, 10)


if __name__ == '__main__':
    unittest.main()
