-- PostgreSQL database initialization script for Social Media Analytics Platform
-- This script creates the necessary tables and indexes for storing collected data

-- Create database if it doesn't exist (run this manually if needed)
-- CREATE DATABASE social_media_analytics;

-- Connect to the database
\c social_media_analytics;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create enum types
CREATE TYPE data_source AS ENUM ('twitter', 'reddit', 'news');
CREATE TYPE content_status AS ENUM ('raw', 'processed', 'analyzed', 'archived');
CREATE TYPE sentiment_label AS ENUM ('positive', 'negative', 'neutral', 'mixed');

-- Raw data storage (Bronze layer)
CREATE TABLE IF NOT EXISTS raw_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source data_source NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    raw_data JSONB NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    UNIQUE(source, external_id)
);

CREATE INDEX idx_raw_data_source ON raw_data(source);
CREATE INDEX idx_raw_data_collected_at ON raw_data(collected_at);
CREATE INDEX idx_raw_data_external_id ON raw_data(external_id);
CREATE INDEX idx_raw_data_jsonb ON raw_data USING GIN(raw_data);

-- Processed data storage (Silver layer)
CREATE TABLE IF NOT EXISTS processed_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    raw_data_id UUID REFERENCES raw_data(id) ON DELETE CASCADE,
    source data_source NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    
    -- Common fields across all sources
    title TEXT,
    content TEXT,
    author VARCHAR(255),
    url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Source-specific fields
    source_metadata JSONB,
    
    -- Processing metadata
    processing_status content_status DEFAULT 'processed',
    processing_errors TEXT[],
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source, external_id)
);

CREATE INDEX idx_processed_data_source ON processed_data(source);
CREATE INDEX idx_processed_data_published_at ON processed_data(published_at);
CREATE INDEX idx_processed_data_author ON processed_data(author);
CREATE INDEX idx_processed_data_status ON processed_data(processing_status);
CREATE INDEX idx_processed_data_content_gin ON processed_data USING GIN(to_tsvector('english', content));

-- Analytics data storage (Gold layer)
CREATE TABLE IF NOT EXISTS analytics_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    processed_data_id UUID REFERENCES processed_data(id) ON DELETE CASCADE,
    source data_source NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    
    -- Engagement metrics
    engagement_score DECIMAL(10, 4),
    like_count INTEGER DEFAULT 0,
    retweet_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    
    -- Sentiment analysis
    sentiment_label sentiment_label,
    sentiment_score DECIMAL(3, 2),
    confidence_score DECIMAL(3, 2),
    
    -- Topic classification
    topics TEXT[],
    topic_confidence DECIMAL(3, 2)[],
    
    -- User influence metrics
    author_followers_count INTEGER DEFAULT 0,
    author_verified BOOLEAN DEFAULT FALSE,
    author_influence_score DECIMAL(10, 4),
    
    -- Temporal features
    hour_of_day INTEGER,
    day_of_week INTEGER,
    is_weekend BOOLEAN,
    
    -- Analysis metadata
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(50),
    
    UNIQUE(source, external_id)
);

CREATE INDEX idx_analytics_data_source ON analytics_data(source);
CREATE INDEX idx_analytics_data_engagement ON analytics_data(engagement_score);
CREATE INDEX idx_analytics_data_sentiment ON analytics_data(sentiment_label, sentiment_score);
CREATE INDEX idx_analytics_data_topics ON analytics_data USING GIN(topics);
CREATE INDEX idx_analytics_data_temporal ON analytics_data(hour_of_day, day_of_week);

-- Aggregated metrics (for dashboard and reporting)
CREATE TABLE IF NOT EXISTS aggregated_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source data_source NOT NULL,
    aggregation_period VARCHAR(20) NOT NULL, -- 'hourly', 'daily', 'weekly'
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Counts
    total_posts INTEGER DEFAULT 0,
    total_engagement INTEGER DEFAULT 0,
    total_authors INTEGER DEFAULT 0,
    
    -- Averages
    avg_engagement_score DECIMAL(10, 4),
    avg_sentiment_score DECIMAL(3, 2),
    
    -- Sentiment distribution
    positive_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    mixed_count INTEGER DEFAULT 0,
    
    -- Top topics
    top_topics JSONB,
    
    -- Top authors
    top_authors JSONB,
    
    -- Calculated at
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source, aggregation_period, period_start)
);

CREATE INDEX idx_aggregated_metrics_period ON aggregated_metrics(aggregation_period, period_start);
CREATE INDEX idx_aggregated_metrics_source ON aggregated_metrics(source);

-- Data quality metrics
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source data_source NOT NULL,
    collection_date DATE NOT NULL,
    
    -- Collection metrics
    total_collected INTEGER DEFAULT 0,
    successful_collections INTEGER DEFAULT 0,
    failed_collections INTEGER DEFAULT 0,
    
    -- Data quality metrics
    missing_title_count INTEGER DEFAULT 0,
    missing_content_count INTEGER DEFAULT 0,
    missing_author_count INTEGER DEFAULT 0,
    duplicate_count INTEGER DEFAULT 0,
    
    -- Processing metrics
    processing_success_rate DECIMAL(5, 2),
    avg_processing_time_ms INTEGER,
    
    -- Calculated at
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source, collection_date)
);

CREATE INDEX idx_data_quality_date ON data_quality_metrics(collection_date);
CREATE INDEX idx_data_quality_source ON data_quality_metrics(source);

-- API rate limit tracking
CREATE TABLE IF NOT EXISTS api_rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source data_source NOT NULL,
    endpoint VARCHAR(255),
    current_usage INTEGER DEFAULT 0,
    rate_limit INTEGER,
    reset_time TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source, endpoint)
);

CREATE INDEX idx_api_rate_limits_source ON api_rate_limits(source);
CREATE INDEX idx_api_rate_limits_reset ON api_rate_limits(reset_time);

-- Collection logs
CREATE TABLE IF NOT EXISTS collection_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source data_source NOT NULL,
    collection_type VARCHAR(50) NOT NULL, -- 'scheduled', 'manual', 'api_triggered'
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'partial'
    
    -- Collection details
    items_collected INTEGER DEFAULT 0,
    items_processed INTEGER DEFAULT 0,
    errors TEXT[],
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Metadata
    configuration JSONB,
    user_agent TEXT,
    ip_address INET
);

CREATE INDEX idx_collection_logs_source ON collection_logs(source);
CREATE INDEX idx_collection_logs_status ON collection_logs(status);
CREATE INDEX idx_collection_logs_started ON collection_logs(started_at);

-- Create views for common queries
CREATE OR REPLACE VIEW recent_posts AS
SELECT 
    pd.id,
    pd.source,
    pd.title,
    pd.author,
    pd.published_at,
    pd.collected_at,
    ad.engagement_score,
    ad.sentiment_label,
    ad.sentiment_score,
    ad.topics
FROM processed_data pd
LEFT JOIN analytics_data ad ON pd.id = ad.processed_data_id
WHERE pd.processing_status = 'processed'
ORDER BY pd.published_at DESC;

CREATE OR REPLACE VIEW sentiment_summary AS
SELECT 
    source,
    sentiment_label,
    COUNT(*) as count,
    AVG(sentiment_score) as avg_score,
    AVG(engagement_score) as avg_engagement
FROM analytics_data
WHERE sentiment_label IS NOT NULL
GROUP BY source, sentiment_label
ORDER BY source, sentiment_label;

CREATE OR REPLACE VIEW trending_topics AS
SELECT 
    unnest(topics) as topic,
    source,
    COUNT(*) as mention_count,
    AVG(engagement_score) as avg_engagement
FROM analytics_data
WHERE topics IS NOT NULL
GROUP BY unnest(topics), source
ORDER BY mention_count DESC, avg_engagement DESC;

-- Insert sample data for testing (optional)
-- INSERT INTO raw_data (source, external_id, raw_data) VALUES 
-- ('twitter', 'test_1', '{"text": "Test tweet", "user": "testuser"}'),
-- ('reddit', 'test_2', '{"title": "Test post", "author": "testuser"}');

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_processed_data_title_gin ON processed_data USING GIN(to_tsvector('english', title));
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_data_author_influence ON analytics_data(author_influence_score);

-- Add comments for documentation
COMMENT ON TABLE raw_data IS 'Bronze layer: Raw data from social media APIs';
COMMENT ON TABLE processed_data IS 'Silver layer: Cleaned and standardized data';
COMMENT ON TABLE analytics_data IS 'Gold layer: Enriched data with ML insights';
COMMENT ON TABLE aggregated_metrics IS 'Pre-calculated metrics for dashboard performance';
COMMENT ON TABLE data_quality_metrics IS 'Data quality tracking and monitoring';
COMMENT ON TABLE api_rate_limits IS 'API rate limit tracking and management';
COMMENT ON TABLE collection_logs IS 'Audit trail for data collection activities';
