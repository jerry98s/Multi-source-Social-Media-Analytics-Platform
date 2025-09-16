#!/usr/bin/env python3
"""
Unit tests for database module
"""

import unittest
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Database


class TestDatabase(unittest.TestCase):
    """Test Database class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the database connection to avoid requiring actual PostgreSQL
        self.mock_conn = Mock()
        self.mock_cursor = Mock()
        self.mock_conn.cursor.return_value = self.mock_cursor
    
    @patch('app.database.psycopg2.connect')
    def test_initialization(self, mock_connect):
        """Test Database initialization"""
        mock_connect.return_value = self.mock_conn
        
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PORT': '5432',
            'POSTGRES_DB': 'test_db',
            'POSTGRES_USER': 'test_user',
            'POSTGRES_PASSWORD': 'test_password'
        }):
            db = Database()
            mock_connect.assert_called_once_with(
                host='localhost',
                port='5432',
                database='test_db',
                user='test_user',
                password='test_password'
            )
    
    @patch('app.database.psycopg2.connect')
    def test_initialization_with_defaults(self, mock_connect):
        """Test Database initialization with default values"""
        mock_connect.return_value = self.mock_conn
        
        with patch.dict(os.environ, {}, clear=True):
            db = Database()
            mock_connect.assert_called_once_with(
                host='localhost',
                port='5432',
                database='social_media_analytics',
                user='postgres',
                password='postgres'
            )
    
    @patch('app.database.psycopg2.connect')
    def test_initialization_connection_error(self, mock_connect):
        """Test Database initialization with connection error"""
        mock_connect.side_effect = Exception("Connection failed")
        
        with self.assertRaises(Exception):
            Database()
    
    def test_close(self):
        """Test close method"""
        db = Database()
        db.conn = self.mock_conn
        
        db.close()
        self.mock_conn.close.assert_called_once()
    
    def test_execute_query_select(self):
        """Test execute_query with SELECT statement"""
        db = Database()
        db.conn = self.mock_conn
        self.mock_cursor.fetchall.return_value = [('row1',), ('row2',)]
        
        result = db.execute_query("SELECT * FROM test_table")
        
        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table", None)
        self.mock_cursor.fetchall.assert_called_once()
        self.assertEqual(result, [('row1',), ('row2',)])
    
    def test_execute_query_insert(self):
        """Test execute_query with INSERT statement"""
        db = Database()
        db.conn = self.mock_conn
        
        result = db.execute_query("INSERT INTO test_table VALUES (%s)", ('test_value',))
        
        self.mock_cursor.execute.assert_called_once_with("INSERT INTO test_table VALUES (%s)", ('test_value',))
        self.mock_conn.commit.assert_called_once()
        self.assertEqual(result, [])
    
    def test_execute_query_error(self):
        """Test execute_query with error"""
        db = Database()
        db.conn = self.mock_conn
        self.mock_cursor.execute.side_effect = Exception("Query failed")
        
        with self.assertRaises(Exception):
            db.execute_query("SELECT * FROM test_table")
        
        self.mock_conn.rollback.assert_called_once()
        self.mock_cursor.close.assert_called_once()
    
    def test_insert_raw_data(self):
        """Test insert_raw_data method"""
        db = Database()
        db.conn = self.mock_conn
        
        test_data = {'title': 'Test', 'content': 'Test content'}
        
        result = db.insert_raw_data('reddit', 'test_id', test_data)
        
        self.mock_cursor.execute.assert_called_once()
        args = self.mock_cursor.execute.call_args[0]
        self.assertEqual(args[0], """
                INSERT INTO raw_posts (source, external_id, data, collected_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source, external_id) DO NOTHING
            """)
        self.assertEqual(args[1][0], 'reddit')
        self.assertEqual(args[1][1], 'test_id')
        self.assertEqual(json.loads(args[1][2]), test_data)
        self.assertTrue(result)
    
    def test_insert_raw_data_error(self):
        """Test insert_raw_data with error"""
        db = Database()
        db.conn = self.mock_conn
        self.mock_cursor.execute.side_effect = Exception("Insert failed")
        
        result = db.insert_raw_data('reddit', 'test_id', {})
        
        self.assertFalse(result)
    
    def test_get_unprocessed_raw_data(self):
        """Test get_unprocessed_raw_data method"""
        db = Database()
        db.conn = self.mock_conn
        self.mock_cursor.fetchall.return_value = [
            (1, 'reddit', 'test_id', '{"title": "Test"}'),
            (2, 'news', 'news_id', '{"title": "News"}')
        ]
        
        result = db.get_unprocessed_raw_data(limit=10)
        
        self.mock_cursor.execute.assert_called_once()
        args = self.mock_cursor.execute.call_args[0]
        self.assertIn("SELECT id, source, external_id, data", args[0])
        self.assertIn("WHERE processed = FALSE", args[0])
        self.assertEqual(args[1], (10,))
        self.assertEqual(len(result), 2)
    
    def test_insert_clean_data(self):
        """Test insert_clean_data method"""
        db = Database()
        db.conn = self.mock_conn
        
        engagement = {'likes': 10, 'shares': 5, 'comments': 3}
        test_date = datetime.now()
        
        result = db.insert_clean_data(
            raw_id=1,
            source='reddit',
            external_id='test_id',
            title='Test Title',
            content='Test content',
            author='test_author',
            url='https://example.com',
            published_at=test_date,
            engagement=engagement
        )
        
        self.mock_cursor.execute.assert_called()
        # Check that raw data is marked as processed
        calls = self.mock_cursor.execute.call_args_list
        self.assertTrue(any("UPDATE raw_posts SET processed = TRUE" in call[0][0] for call in calls))
        self.assertTrue(result)
    
    def test_get_unprocessed_clean_data(self):
        """Test get_unprocessed_clean_data method"""
        db = Database()
        db.conn = self.mock_conn
        self.mock_cursor.fetchall.return_value = [
            (1, 'reddit', 'test_id', 'Test Title', 'Test content', 'author', 
             datetime.now(), 10, 5, 3)
        ]
        
        result = db.get_unprocessed_clean_data(limit=10)
        
        self.mock_cursor.execute.assert_called_once()
        args = self.mock_cursor.execute.call_args[0]
        self.assertIn("SELECT id, source, external_id, title, content", args[0])
        self.assertIn("WHERE processed = FALSE", args[0])
        self.assertEqual(len(result), 1)
    
    def test_insert_features(self):
        """Test insert_features method"""
        db = Database()
        db.conn = self.mock_conn
        
        features = {
            'sentiment_label': 'positive',
            'sentiment_score': 0.8,
            'engagement_score': 5.5,
            'word_count': 100,
            'char_count': 500,
            'hashtag_count': 2,
            'mention_count': 1,
            'hour_of_day': 14,
            'day_of_week': 1,
            'is_weekend': False
        }
        
        result = db.insert_features(1, 'reddit', 'test_id', features)
        
        self.mock_cursor.execute.assert_called()
        # Check that clean data is marked as processed
        calls = self.mock_cursor.execute.call_args_list
        self.assertTrue(any("UPDATE clean_posts SET processed = TRUE" in call[0][0] for call in calls))
        self.assertTrue(result)
    
    def test_get_stats(self):
        """Test get_stats method"""
        db = Database()
        db.conn = self.mock_conn
        
        # Mock different return values for each table
        call_count = 0
        def side_effect():
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # raw_posts
                return [(10,)]
            elif call_count == 2:  # clean_posts
                return [(8,)]
            elif call_count == 3:  # post_features
                return [(6,)]
            return []
        
        self.mock_cursor.fetchall.side_effect = side_effect
        
        stats = db.get_stats()
        
        self.assertEqual(stats['raw_posts'], 10)
        self.assertEqual(stats['clean_posts'], 8)
        self.assertEqual(stats['post_features'], 6)
        self.assertEqual(self.mock_cursor.execute.call_count, 3)


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for Database class"""
    
    @patch('app.database.psycopg2.connect')
    def test_full_data_flow(self, mock_connect):
        """Test complete data flow from raw to features"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        db = Database()
        
        # Test data
        raw_data = {'title': 'Test Post', 'content': 'This is a test post'}
        engagement = {'likes': 10, 'shares': 2, 'comments': 5}
        features = {
            'sentiment_label': 'positive',
            'sentiment_score': 0.7,
            'engagement_score': 2.5,
            'word_count': 6,
            'char_count': 25,
            'hashtag_count': 0,
            'mention_count': 0,
            'hour_of_day': 12,
            'day_of_week': 1,
            'is_weekend': False
        }
        
        # Insert raw data
        raw_result = db.insert_raw_data('reddit', 'test_id', raw_data)
        self.assertTrue(raw_result)
        
        # Insert clean data
        clean_result = db.insert_clean_data(
            raw_id=1, source='reddit', external_id='test_id',
            title='Test Post', content='This is a test post',
            author='test_author', url='https://example.com',
            published_at=datetime.now(), engagement=engagement
        )
        self.assertTrue(clean_result)
        
        # Insert features
        features_result = db.insert_features(1, 'reddit', 'test_id', features)
        self.assertTrue(features_result)
        
        # Verify all operations were called
        self.assertGreaterEqual(mock_cursor.execute.call_count, 3)


if __name__ == '__main__':
    unittest.main()
