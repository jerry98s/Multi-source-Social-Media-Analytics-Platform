"""
Database connection and management service.
Handles PostgreSQL connections and provides connection pooling.
"""

import os
import logging
import json
from typing import Optional
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and provides connection pooling."""
    
    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            # Database connection parameters
            db_config = {
                'host': os.getenv('POSTGRES_HOST', 'localhost'),
                'port': os.getenv('POSTGRES_PORT', '5432'),
                'database': os.getenv('POSTGRES_DB', 'social_media_analytics'),
                'user': os.getenv('POSTGRES_USER', 'postgres'),
                'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
                'minconn': 1,
                'maxconn': 10
            }
            
            # Create connection pool
            self.connection_pool = SimpleConnectionPool(
                minconn=db_config['minconn'],
                maxconn=db_config['maxconn'],
                **{k: v for k, v in db_config.items() if k not in ['minconn', 'maxconn']}
            )
            
            logger.info("Database connection pool initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool."""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def test_connection(self) -> bool:
        """Test database connectivity."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def close(self):
        """Close all database connections."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")


class DataLakeStorage:
    """Data Lake storage service implementing Bronze/Silver/Gold architecture."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
    
    def store_bronze_data(self, data: dict, source: str, data_type: str) -> str:
        """Store raw data in Bronze layer (raw_data table)."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Extract external_id from data
                    external_id = str(data.get('id', ''))
                    
                    # Insert into raw_data table
                    cursor.execute("""
                        INSERT INTO raw_data (source, external_id, raw_data, collected_at)
                        VALUES (%s, %s, %s, NOW())
                        RETURNING id
                    """, (source, external_id, json.dumps(data)))
                    
                    raw_data_id = cursor.fetchone()['id']
                    conn.commit()
                    
                    self.logger.info(f"Stored bronze data: {raw_data_id} from {source}")
                    return raw_data_id
                    
        except Exception as e:
            self.logger.error(f"Failed to store bronze data: {e}")
            raise
    
    def store_silver_data(self, bronze_id: str, processed_data: dict, 
                         validation_status: str, quality_score: float) -> str:
        """Store processed data in Silver layer (processed_data table)."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Extract common fields
                    external_id = str(processed_data.get('id', ''))
                    title = processed_data.get('title', '') or processed_data.get('text', '')
                    content = processed_data.get('content', '') or processed_data.get('selftext', '')
                    author = processed_data.get('author', '') or processed_data.get('author_username', '')
                    url = processed_data.get('url', '')
                    
                    # Get published timestamp and convert to proper format
                    published_at = None
                    if 'created_at' in processed_data:
                        published_at = processed_data['created_at']
                    elif 'created_utc' in processed_data:
                        # Convert Unix timestamp to ISO format
                        from datetime import datetime, timezone
                        if isinstance(processed_data['created_utc'], (int, float)):
                            dt = datetime.fromtimestamp(processed_data['created_utc'], tz=timezone.utc)
                            published_at = dt.isoformat()
                        else:
                            published_at = processed_data['created_utc']
                    elif 'published_at' in processed_data:
                        published_at = processed_data['published_at']
                    
                    # Create source metadata
                    source_metadata = {
                        'validation_status': validation_status,
                        'quality_score': quality_score,
                        'original_data': processed_data
                    }
                    
                    # Insert into processed_data table
                    cursor.execute("""
                        INSERT INTO processed_data (
                            raw_data_id, source, external_id, title, content, author, url, 
                            published_at, source_metadata, processing_status, processed_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        RETURNING id
                    """, (bronze_id, processed_data.get('source', 'reddit'), external_id, 
                          title, content, author, url, published_at, 
                          json.dumps(source_metadata), 'processed'))
                    
                    processed_data_id = cursor.fetchone()['id']
                    conn.commit()
                    
                    self.logger.info(f"Stored silver data: {processed_data_id} from bronze {bronze_id}")
                    return processed_data_id
                    
        except Exception as e:
            self.logger.error(f"Failed to store silver data: {e}")
            raise
    
    def store_gold_data(self, processed_data_id: str, analytics_data: dict,
                       aggregation_type: str, metrics: dict) -> str:
        """Store analytics data in Gold layer (analytics_data table)."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get the processed data to extract source and external_id
                    cursor.execute("""
                        SELECT source, external_id FROM processed_data WHERE id = %s
                    """, (processed_data_id,))
                    
                    processed_row = cursor.fetchone()
                    if not processed_row:
                        raise ValueError(f"Processed data with ID {processed_data_id} not found")
                    
                    source = processed_row['source']
                    external_id = processed_row['external_id']
                    
                    # Extract engagement metrics
                    engagement_metrics = analytics_data.get('engagement_metrics', {})
                    engagement_score = engagement_metrics.get('engagement_score', 0.0)
                    like_count = engagement_metrics.get('like_count', 0)
                    retweet_count = engagement_metrics.get('retweet_count', 0)
                    comment_count = engagement_metrics.get('comment_count', 0)
                    share_count = engagement_metrics.get('share_count', 0)
                    
                    # Extract temporal features
                    temporal_features = analytics_data.get('temporal_features', {})
                    hour_of_day = temporal_features.get('hour_of_day')
                    day_of_week = temporal_features.get('day_of_week')
                    
                    # Insert into analytics_data table
                    cursor.execute("""
                        INSERT INTO analytics_data (
                            processed_data_id, source, external_id, engagement_score,
                            like_count, retweet_count, comment_count, share_count,
                            hour_of_day, day_of_week, analyzed_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        RETURNING id
                    """, (processed_data_id, source, external_id, engagement_score,
                          like_count, retweet_count, comment_count, share_count,
                          hour_of_day, day_of_week))
                    
                    analytics_data_id = cursor.fetchone()['id']
                    conn.commit()
                    
                    self.logger.info(f"Stored gold data: {analytics_data_id} from processed {processed_data_id}")
                    return analytics_data_id
                    
        except Exception as e:
            self.logger.error(f"Failed to store gold data: {e}")
            raise
    
    def get_data_quality_metrics(self, source: str, days: int = 7) -> dict:
        """Get data quality metrics for a specific source."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(CASE WHEN pd.processing_status = 'processed' THEN 1 END) as valid_records,
                            COUNT(CASE WHEN pd.processing_status != 'processed' THEN 1 END) as invalid_records
                        FROM processed_data pd
                        JOIN raw_data rd ON pd.raw_data_id = rd.id
                        WHERE rd.source = %s 
                        AND rd.collected_at >= NOW() - INTERVAL '%s days'
                    """, (source, days))
                    
                    result = cursor.fetchone()
                    return dict(result) if result else {}
                    
        except Exception as e:
            self.logger.error(f"Failed to get data quality metrics: {e}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data based on retention policy."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Delete old raw data (keep last 30 days)
                    cursor.execute("""
                        DELETE FROM raw_data 
                        WHERE collected_at < NOW() - INTERVAL '%s days'
                    """, (days,))
                    
                    deleted_raw = cursor.rowcount
                    
                    # Delete old processed data
                    cursor.execute("""
                        DELETE FROM processed_data 
                        WHERE processed_at < NOW() - INTERVAL '%s days'
                    """, (days,))
                    
                    deleted_processed = cursor.rowcount
                    
                    conn.commit()
                    
                    self.logger.info(f"Cleanup completed: {deleted_raw} raw records, {deleted_processed} processed records")
                    
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            raise


# Global database manager instance
db_manager = DatabaseManager()
data_lake_storage = DataLakeStorage(db_manager)


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    return db_manager


def get_data_lake_storage() -> DataLakeStorage:
    """Get the global data lake storage instance."""
    return data_lake_storage
