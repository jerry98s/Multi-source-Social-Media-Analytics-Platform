-- Social Media Analytics Database Schema
-- Simple and clean design

-- Create database (run manually)
-- CREATE DATABASE social_analytics;

-- Connect to database
\c social_analytics;

-- Create enum types
CREATE TYPE source_type AS ENUM ('reddit', 'news', 'twitter');
CREATE TYPE sentiment_type AS ENUM ('positive', 'negative', 'neutral');

-- Raw Posts Table (Bronze Layer)
CREATE TABLE IF NOT EXISTS raw_posts (
    id SERIAL PRIMARY KEY,
    source source_type NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    
    UNIQUE(source, external_id)
);

CREATE INDEX idx_raw_posts_source ON raw_posts(source);
CREATE INDEX idx_raw_posts_collected_at ON raw_posts(collected_at);
CREATE INDEX idx_raw_posts_processed ON raw_posts(processed);

-- Clean Posts Table (Silver Layer)  
CREATE TABLE IF NOT EXISTS clean_posts (
    id SERIAL PRIMARY KEY,
    raw_id INTEGER REFERENCES raw_posts(id) ON DELETE CASCADE,
    source source_type NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    
    -- Content fields
    title TEXT,
    content TEXT,
    author VARCHAR(255),
    url TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Engagement metrics
    likes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    
    -- Processing metadata
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    
    UNIQUE(source, external_id)
);

CREATE INDEX idx_clean_posts_source ON clean_posts(source);
CREATE INDEX idx_clean_posts_published_at ON clean_posts(published_at);
CREATE INDEX idx_clean_posts_author ON clean_posts(author);
CREATE INDEX idx_clean_posts_processed ON clean_posts(processed);

-- Post Features Table (Gold Layer)
CREATE TABLE IF NOT EXISTS post_features (
    id SERIAL PRIMARY KEY,
    clean_id INTEGER REFERENCES clean_posts(id) ON DELETE CASCADE,
    source source_type NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    
    -- ML Features
    sentiment_label sentiment_type,
    sentiment_score DECIMAL(3, 2),
    engagement_score DECIMAL(10, 4),
    
    -- Text features
    word_count INTEGER,
    char_count INTEGER,
    hashtag_count INTEGER,
    mention_count INTEGER,
    
    -- Temporal features
    hour_of_day INTEGER,
    day_of_week INTEGER,
    is_weekend BOOLEAN,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source, external_id)
);

CREATE INDEX idx_features_source ON post_features(source);
CREATE INDEX idx_features_sentiment ON post_features(sentiment_label, sentiment_score);
CREATE INDEX idx_features_engagement ON post_features(engagement_score);

-- ML Models Table
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    accuracy DECIMAL(5, 4),
    training_data_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT FALSE,
    
    UNIQUE(name, version)
);

-- Views for analysis
CREATE OR REPLACE VIEW sentiment_summary AS
SELECT 
    source,
    sentiment_label,
    COUNT(*) as post_count,
    AVG(sentiment_score) as avg_sentiment_score,
    AVG(engagement_score) as avg_engagement_score
FROM post_features 
WHERE sentiment_label IS NOT NULL
GROUP BY source, sentiment_label
ORDER BY source, sentiment_label;

CREATE OR REPLACE VIEW top_engaging_posts AS
SELECT 
    cp.source,
    cp.title,
    cp.author,
    cp.published_at,
    pf.engagement_score,
    pf.sentiment_label,
    cp.url
FROM clean_posts cp
JOIN post_features pf ON cp.id = pf.clean_id
ORDER BY pf.engagement_score DESC
LIMIT 100;

-- Sample data (uncomment to test)
/*
INSERT INTO raw_posts (source, external_id, data) VALUES 
('reddit', 'test123', '{"title": "Test Post", "content": "This is a test", "score": 100}'),
('news', 'news456', '{"title": "News Article", "description": "Breaking news", "url": "https://example.com"}');
*/