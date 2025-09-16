#!/usr/bin/env python3
"""
Database setup script for Social Media Analytics Platform
Creates the database schema using the SQL file
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def setup_database():
    """Setup the database schema"""
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    database = os.getenv('POSTGRES_DB', 'social_media_analytics')
    
    try:
        logger.info(f"Connecting to PostgreSQL at {host}:{port}")
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        logger.info("Connected to PostgreSQL successfully!")
        
        # Read and execute schema file
        schema_file = 'sql/schema.sql'
        if os.path.exists(schema_file):
            logger.info(f"Reading schema file: {schema_file}")
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Remove the \\c command as we're already connected
            schema_sql = schema_sql.replace('\\c social_analytics;', '')
            
            # Execute the schema
            logger.info("Creating database schema...")
            cursor.execute(schema_sql)
            logger.info("Database schema created successfully!")
            
            # Test the schema by checking if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            logger.info("Created tables:")
            for table in tables:
                logger.info(f"  - {table[0]}")
            
        else:
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        cursor.close()
        conn.close()
        
        logger.info("Database setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    host = os.getenv('POSTGRES_HOST', 'localhost')
    port = os.getenv('POSTGRES_PORT', '5432')
    user = os.getenv('POSTGRES_USER', 'postgres')
    password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    database = os.getenv('POSTGRES_DB', 'social_media_analytics')
    
    try:
        logger.info("Testing database connection...")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        
        logger.info("Database connection test successful!")
        return True
        
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("🗄️ Social Media Analytics Platform - Database Setup")
    print("=" * 60)
    
    # Test connection first
    if not test_database_connection():
        print("❌ Database connection failed. Please check:")
        print("   1. PostgreSQL Docker container is running")
        print("   2. Environment variables are correct")
        print("   3. Port 5432 is accessible")
        return False
    
    # Setup database schema
    if setup_database():
        print("\n✅ Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the test runner: python test_runner.py")
        print("2. Test the collectors: python -c \"from app.collectors import DataCollector; print('Collectors ready!')\"")
        print("3. Start the platform: python test_runner.py")
        return True
    else:
        print("\n❌ Database setup failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
