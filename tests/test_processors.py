#!/usr/bin/env python3
"""
Unit tests for processors module
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.processors import DataCleaner, FeatureExtractor


class TestDataCleaner(unittest.TestCase):
    """Test DataCleaner class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cleaner = DataCleaner()
    
    @patch('app.processors.Database')
    def test_initialization(self, mock_database):
        """Test DataCleaner initialization"""
        cleaner = DataCleaner()
        mock_database.assert_called_once()
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        # Test cases
        test_cases = [
            ("  Hello   World  ", "Hello World"),
            ("Test!!!", "Test!!!"),
            ("Special@#$%chars", "Special@#$%chars"),
            ("", ""),
            (None, ""),
            ("Normal text", "Normal text"),
            ("Multiple   spaces", "Multiple spaces"),
            ("\n\nNewlines\n\n", "Newlines"),
            ("\t\tTabs\t\t", "Tabs")
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.cleaner.clean_text(input_text)
                self.assertEqual(result, expected)
    
    def test_parse_timestamp(self):
        """Test timestamp parsing"""
        # Test Unix timestamp
        unix_timestamp = 1234567890
        result = self.cleaner.parse_timestamp(unix_timestamp)
        self.assertIsInstance(result, datetime)
        
        # Test ISO string
        iso_string = "2024-01-01T12:00:00Z"
        result = self.cleaner.parse_timestamp(iso_string)
        self.assertIsInstance(result, datetime)
        
        # Test datetime object
        dt = datetime.now()
        result = self.cleaner.parse_timestamp(dt)
        self.assertEqual(result, dt)
        
        # Test invalid input
        result = self.cleaner.parse_timestamp("invalid")
        self.assertIsInstance(result, datetime)  # Should return current time
    
    def test_clean_reddit_data(self):
        """Test Reddit data cleaning"""
        reddit_data = {
            'title': '  Test Title  ',
            'content': 'Test content with special chars!@#',
            'author': 'test_author',
            'url': 'https://reddit.com/test',
            'created_utc': 1234567890,
            'score': 100,
            'num_comments': 50
        }
        
        result = self.cleaner.clean_reddit_data(reddit_data)
        
        self.assertEqual(result['title'], 'Test Title')
        self.assertEqual(result['content'], 'Test content with special chars!@#')
        self.assertEqual(result['author'], 'test_author')
        self.assertEqual(result['url'], 'https://reddit.com/test')
        self.assertIsInstance(result['published_at'], datetime)
        self.assertEqual(result['engagement']['likes'], 100)
        self.assertEqual(result['engagement']['shares'], 0)  # Reddit doesn't have shares
        self.assertEqual(result['engagement']['comments'], 50)
    
    def test_clean_news_data(self):
        """Test News data cleaning"""
        news_data = {
            'title': '  News Title  ',
            'content': 'News content with description',
            'author': 'News Author',
            'url': 'https://news.com/article',
            'published_at': '2024-01-01T12:00:00Z'
        }
        
        result = self.cleaner.clean_news_data(news_data)
        
        self.assertEqual(result['title'], 'News Title')
        self.assertEqual(result['content'], 'News content with description')
        self.assertEqual(result['author'], 'News Author')
        self.assertEqual(result['url'], 'https://news.com/article')
        self.assertIsInstance(result['published_at'], datetime)
        self.assertEqual(result['engagement']['likes'], 0)  # News doesn't have engagement
        self.assertEqual(result['engagement']['shares'], 0)
        self.assertEqual(result['engagement']['comments'], 0)
    
    @patch('app.processors.Database')
    def test_process_raw_data(self, mock_database):
        """Test raw data processing"""
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.get_unprocessed_raw_data.return_value = [
            (1, 'reddit', 'test_id', {'title': 'Test', 'content': 'Test content', 'score': 10, 'num_comments': 5, 'created_utc': 1234567890}),
            (2, 'news', 'news_id', {'title': 'News', 'content': 'News content', 'published_at': '2024-01-01T12:00:00Z'})
        ]
        mock_db_instance.insert_clean_data.return_value = True
        mock_database.return_value = mock_db_instance
        
        cleaner = DataCleaner()
        cleaner.db = mock_db_instance
        
        result = cleaner.process_raw_data(limit=10)
        
        self.assertEqual(result['processed_count'], 2)
        self.assertEqual(mock_db_instance.insert_clean_data.call_count, 2)
    
    @patch('app.processors.Database')
    def test_process_raw_data_with_errors(self, mock_database):
        """Test raw data processing with errors"""
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.get_unprocessed_raw_data.return_value = [
            (1, 'unknown_source', 'test_id', {'title': 'Test'})
        ]
        mock_database.return_value = mock_db_instance
        
        cleaner = DataCleaner()
        cleaner.db = mock_db_instance
        
        result = cleaner.process_raw_data(limit=10)
        
        self.assertEqual(result['processed_count'], 0)


class TestFeatureExtractor(unittest.TestCase):
    """Test FeatureExtractor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = FeatureExtractor()
    
    @patch('app.processors.Database')
    def test_initialization(self, mock_database):
        """Test FeatureExtractor initialization"""
        extractor = FeatureExtractor()
        mock_database.assert_called_once()
    
    def test_analyze_sentiment(self):
        """Test sentiment analysis"""
        # Test positive sentiment
        positive_text = "This is great and amazing!"
        label, score = self.extractor.analyze_sentiment(positive_text)
        self.assertEqual(label, 'positive')
        self.assertEqual(score, 0.7)
        
        # Test negative sentiment
        negative_text = "This is terrible and awful!"
        label, score = self.extractor.analyze_sentiment(negative_text)
        self.assertEqual(label, 'negative')
        self.assertEqual(score, -0.7)
        
        # Test neutral sentiment
        neutral_text = "This is just a normal text."
        label, score = self.extractor.analyze_sentiment(neutral_text)
        self.assertEqual(label, 'neutral')
        self.assertEqual(score, 0.0)
        
        # Test empty text
        label, score = self.extractor.analyze_sentiment("")
        self.assertEqual(label, 'neutral')
        self.assertEqual(score, 0.0)
    
    def test_calculate_engagement_score(self):
        """Test engagement score calculation"""
        # Test normal engagement
        score = self.extractor.calculate_engagement_score(100, 50, 25)
        expected = (100 * 1.0 + 50 * 2.0 + 25 * 1.5) / 100.0
        self.assertEqual(score, expected)
        
        # Test high engagement (should be capped at 10)
        score = self.extractor.calculate_engagement_score(1000, 500, 250)
        self.assertEqual(score, 10.0)
        
        # Test zero engagement
        score = self.extractor.calculate_engagement_score(0, 0, 0)
        self.assertEqual(score, 0.0)
    
    def test_extract_text_features(self):
        """Test text feature extraction"""
        # Test normal text
        text = "Hello #world @user! This is a test."
        features = self.extractor.extract_text_features(text)
        
        self.assertEqual(features['word_count'], 7)
        self.assertEqual(features['char_count'], len(text))
        self.assertEqual(features['hashtag_count'], 1)
        self.assertEqual(features['mention_count'], 1)
        
        # Test empty text
        features = self.extractor.extract_text_features("")
        self.assertEqual(features['word_count'], 0)
        self.assertEqual(features['char_count'], 0)
        self.assertEqual(features['hashtag_count'], 0)
        self.assertEqual(features['mention_count'], 0)
        
        # Test None text
        features = self.extractor.extract_text_features(None)
        self.assertEqual(features['word_count'], 0)
        self.assertEqual(features['char_count'], 0)
        self.assertEqual(features['hashtag_count'], 0)
        self.assertEqual(features['mention_count'], 0)
    
    def test_extract_temporal_features(self):
        """Test temporal feature extraction"""
        # Test weekday
        weekday_time = datetime(2024, 1, 1, 14, 30)  # Monday, 2:30 PM
        features = self.extractor.extract_temporal_features(weekday_time)
        
        self.assertEqual(features['hour_of_day'], 14)
        self.assertEqual(features['day_of_week'], 0)  # Monday
        self.assertFalse(features['is_weekend'])
        
        # Test weekend
        weekend_time = datetime(2024, 1, 6, 9, 0)  # Saturday, 9:00 AM
        features = self.extractor.extract_temporal_features(weekend_time)
        
        self.assertEqual(features['hour_of_day'], 9)
        self.assertEqual(features['day_of_week'], 5)  # Saturday
        self.assertTrue(features['is_weekend'])
    
    @patch('app.processors.Database')
    def test_process_clean_data(self, mock_database):
        """Test clean data processing"""
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.get_unprocessed_clean_data.return_value = [
            (1, 'reddit', 'test_id', 'Test Title', 'This is great content!', 'author', 
             datetime.now(), 10, 5, 3)
        ]
        mock_db_instance.insert_features.return_value = True
        mock_database.return_value = mock_db_instance
        
        extractor = FeatureExtractor()
        extractor.db = mock_db_instance
        
        result = extractor.process_clean_data(limit=10)
        
        self.assertEqual(result['processed_count'], 1)
        mock_db_instance.insert_features.assert_called_once()
        
        # Check that features were extracted correctly
        call_args = mock_db_instance.insert_features.call_args
        features = call_args[0][3]  # Fourth argument is features dict
        
        self.assertEqual(features['sentiment_label'], 'positive')
        self.assertEqual(features['sentiment_score'], 0.7)
        self.assertIn('word_count', features)
        self.assertIn('char_count', features)
        self.assertIn('hashtag_count', features)
        self.assertIn('mention_count', features)
        self.assertIn('hour_of_day', features)
        self.assertIn('day_of_week', features)
        self.assertIn('is_weekend', features)
    
    @patch('app.processors.Database')
    def test_process_clean_data_with_errors(self, mock_database):
        """Test clean data processing with errors"""
        # Mock database
        mock_db_instance = Mock()
        mock_db_instance.get_unprocessed_clean_data.return_value = [
            (1, 'reddit', 'test_id', None, None, 'author', 
             datetime.now(), 10, 5, 3)  # None title and content
        ]
        mock_database.return_value = mock_db_instance
        
        extractor = FeatureExtractor()
        extractor.db = mock_db_instance
        
        result = extractor.process_clean_data(limit=10)
        
        self.assertEqual(result['processed_count'], 0)


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    @patch('app.processors.DataCleaner')
    def test_clean_raw_data_function(self, mock_cleaner):
        """Test clean_raw_data utility function"""
        from app.processors import clean_raw_data
        
        mock_cleaner_instance = Mock()
        mock_cleaner_instance.process_raw_data.return_value = {'processed_count': 5}
        mock_cleaner.return_value = mock_cleaner_instance
        
        result = clean_raw_data(limit=100)
        
        self.assertEqual(result['processed_count'], 5)
        mock_cleaner_instance.process_raw_data.assert_called_once_with(100)
        mock_cleaner_instance.close.assert_called_once()
    
    @patch('app.processors.FeatureExtractor')
    def test_extract_features_function(self, mock_extractor):
        """Test extract_features utility function"""
        from app.processors import extract_features
        
        mock_extractor_instance = Mock()
        mock_extractor_instance.process_clean_data.return_value = {'processed_count': 3}
        mock_extractor.return_value = mock_extractor_instance
        
        result = extract_features(limit=50)
        
        self.assertEqual(result['processed_count'], 3)
        mock_extractor_instance.process_clean_data.assert_called_once_with(50)
        mock_extractor_instance.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
