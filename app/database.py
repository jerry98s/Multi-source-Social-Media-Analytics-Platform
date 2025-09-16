"""
Database module for social media analytics
Simple PostgreSQL connection and operations
"""

import os
import psycopg2
import psycopg2.extras
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class Database:
    """Simple database manager"""
    
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', 'social_media_analytics'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'postgres')
            )
            logger.info("Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute query and return results"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.conn.commit()
                return []
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Query failed: {e}")
            raise
        finally:
            cursor.close()
    
    # Raw Data Operations
    def insert_raw_data(self, source: str, external_id: str, data: Dict[str, Any]) -> bool:
        """Insert raw data"""
        try:
            query = """
                INSERT INTO raw_posts (source, external_id, data, collected_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (source, external_id) DO NOTHING
            """
            self.execute_query(query, (source, external_id, json.dumps(data), datetime.now()))
            return True
        except Exception as e:
            logger.error(f"Failed to insert raw data: {e}")
            return False
    
    def get_unprocessed_raw_data(self, limit: int = 1000) -> List[tuple]:
        """Get raw data that hasn't been processed"""
        query = """
            SELECT id, source, external_id, data
            FROM raw_posts 
            WHERE processed = FALSE
            ORDER BY collected_at DESC
            LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    # Clean Data Operations
    def insert_clean_data(self, raw_id: int, source: str, external_id: str, 
                         title: str, content: str, author: str, url: str,
                         published_at: datetime, engagement: Dict[str, int]) -> bool:
        """Insert cleaned data"""
        try:
            query = """
                INSERT INTO clean_posts (raw_id, source, external_id, title, content, 
                                       author, url, published_at, likes, shares, comments, processed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, external_id) DO NOTHING
            """
            self.execute_query(query, (
                raw_id, source, external_id, title, content, author, url, published_at,
                engagement.get('likes', 0), engagement.get('shares', 0), 
                engagement.get('comments', 0), datetime.now()
            ))
            
            # Mark raw data as processed
            self.execute_query("UPDATE raw_posts SET processed = TRUE WHERE id = %s", (raw_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to insert clean data: {e}")
            return False
    
    def get_unprocessed_clean_data(self, limit: int = 1000) -> List[tuple]:
        """Get clean data that hasn't been processed for features"""
        query = """
            SELECT id, source, external_id, title, content, author, 
                   published_at, likes, shares, comments
            FROM clean_posts 
            WHERE processed = FALSE
            ORDER BY processed_at DESC
            LIMIT %s
        """
        return self.execute_query(query, (limit,))
    
    # Feature Data Operations
    def insert_features(self, clean_id: int, source: str, external_id: str, features: Dict[str, Any]) -> bool:
        """Insert feature data"""
        try:
            query = """
                INSERT INTO post_features (clean_id, source, external_id, sentiment_label, 
                                         sentiment_score, engagement_score, word_count, 
                                         char_count, hashtag_count, mention_count, 
                                         hour_of_day, day_of_week, is_weekend, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source, external_id) DO NOTHING
            """
            self.execute_query(query, (
                clean_id, source, external_id,
                features.get('sentiment_label'),
                features.get('sentiment_score'),
                features.get('engagement_score'),
                features.get('word_count'),
                features.get('char_count'),
                features.get('hashtag_count'),
                features.get('mention_count'),
                features.get('hour_of_day'),
                features.get('day_of_week'),
                features.get('is_weekend'),
                datetime.now()
            ))
            
            # Mark clean data as processed
            self.execute_query("UPDATE clean_posts SET processed = TRUE WHERE id = %s", (clean_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to insert features: {e}")
            return False
    
    # Statistics
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}
        tables = ['raw_posts', 'clean_posts', 'post_features']
        
        for table in tables:
            result = self.execute_query(f"SELECT COUNT(*) FROM {table}")
            stats[table] = result[0][0] if result else 0
        
        return stats