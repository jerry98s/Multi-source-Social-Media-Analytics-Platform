"""
Social Media Analytics DAG
Simple Airflow pipeline for social media data processing
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app'))

from collectors import collect_social_media_data
from processors import clean_raw_data, extract_features

# Default arguments
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'social_media_analytics',
    default_args=default_args,
    description='Social media analytics pipeline',
    schedule_interval=timedelta(hours=2),
    catchup=False,
    tags=['social-media', 'analytics'],
)

# Task 1: Collect data from social media sources
collect_data_task = PythonOperator(
    task_id='collect_social_media_data',
    python_callable=collect_social_media_data,
    op_kwargs={
        'queries': ['artificial intelligence', 'machine learning', 'technology', 'data science'],
        'limit_per_source': 30
    },
    dag=dag,
)

# Task 2: Clean raw data
clean_data_task = PythonOperator(
    task_id='clean_raw_data',
    python_callable=clean_raw_data,
    op_kwargs={'limit': 1000},
    dag=dag,
)

# Task 3: Extract features
extract_features_task = PythonOperator(
    task_id='extract_features',
    python_callable=extract_features,
    op_kwargs={'limit': 1000},
    dag=dag,
)

# Task 4: Data quality check
data_quality_check = PostgresOperator(
    task_id='data_quality_check',
    postgres_conn_id='postgres_default',
    sql="""
    SELECT 
        'raw_posts' as table_name,
        COUNT(*) as total_records,
        COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed_records
    FROM raw_posts
    
    UNION ALL
    
    SELECT 
        'clean_posts' as table_name,
        COUNT(*) as total_records,
        COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed_records
    FROM clean_posts
    
    UNION ALL
    
    SELECT 
        'post_features' as table_name,
        COUNT(*) as total_records,
        NULL as processed_records
    FROM post_features;
    """,
    dag=dag,
)

# Task dependencies
collect_data_task >> clean_data_task >> extract_features_task >> data_quality_check