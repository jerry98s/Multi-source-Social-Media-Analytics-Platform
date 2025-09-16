"""
Data processing modules
Clean raw data and extract features
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
try:
    from .database import Database
except ImportError:
    from database import Database

logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean raw data and transform to structured format"""
    
    def __init__(self):
        self.db = Database()
    
    def clean_text(self, text: str) -> str:
        """Clean text content"""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation and symbols
        text = re.sub(r'[^\w\s.,!?@#$%-]', '', text)
        
        return text
    
    def parse_timestamp(self, timestamp) -> datetime:
        """Parse various timestamp formats"""
        try:
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # Try different formats
                try:
                    return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except:
                    return datetime.fromisoformat(timestamp.replace('T', ' ').replace('Z', ''))
            elif isinstance(timestamp, datetime):
                return timestamp
            return datetime.now()
        except:
            return datetime.now()
    
    def clean_reddit_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean Reddit post data"""
        return {
            'title': self.clean_text(data.get('title', '')),
            'content': self.clean_text(data.get('content', '')),
            'author': data.get('author', '[deleted]'),
            'url': data.get('url', ''),
            'published_at': self.parse_timestamp(data.get('created_utc')),
            'engagement': {
                'likes': data.get('score', 0),
                'shares': 0,  # Reddit doesn't have shares
                'comments': data.get('num_comments', 0)
            }
        }
    
    def clean_news_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean news article data"""
        return {
            'title': self.clean_text(data.get('title', '')),
            'content': self.clean_text(data.get('content', '')),
            'author': data.get('author', 'Unknown'),
            'url': data.get('url', ''),
            'published_at': self.parse_timestamp(data.get('published_at')),
            'engagement': {
                'likes': 0,  # News doesn't have likes
                'shares': 0,
                'comments': 0
            }
        }
    
    def process_raw_data(self, limit: int = 1000) -> Dict[str, Any]:
        """Process raw data to clean format"""
        raw_data = self.db.get_unprocessed_raw_data(limit)
        processed_count = 0
        
        for row in raw_data:
            raw_id, source, external_id, data = row
            
            try:
                if source == 'reddit':
                    clean_data = self.clean_reddit_data(data)
                elif source == 'news':
                    clean_data = self.clean_news_data(data)
                else:
                    logger.warning(f"Unknown source: {source}")
                    continue
                
                # Insert clean data
                success = self.db.insert_clean_data(
                    raw_id=raw_id,
                    source=source,
                    external_id=external_id,
                    title=clean_data['title'],
                    content=clean_data['content'],
                    author=clean_data['author'],
                    url=clean_data['url'],
                    published_at=clean_data['published_at'],
                    engagement=clean_data['engagement']
                )
                
                if success:
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to clean data for {source}:{external_id}: {e}")
        
        logger.info(f"Cleaned {processed_count} records")
        return {'processed_count': processed_count}
    
    def close(self):
        """Close database connection"""
        self.db.close()


class FeatureExtractor:
    """Extract ML features from clean data"""
    
    def __init__(self):
        self.db = Database()
    
    def analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """Simple keyword-based sentiment analysis"""
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'awesome', 'love', 'best', 
            'fantastic', 'wonderful', 'perfect', 'brilliant', 'outstanding'
        ]
        negative_words = [
            'bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 
            'disappointing', 'poor', 'pathetic', 'disgusting'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            return 'positive', 0.7
        elif negative_count > positive_count:
            return 'negative', -0.7
        else:
            return 'neutral', 0.0
    
    def calculate_engagement_score(self, likes: int, shares: int, comments: int) -> float:
        """Calculate engagement score"""
        # Weighted score
        score = (likes * 1.0 + shares * 2.0 + comments * 1.5) / 100.0
        return min(score, 10.0)  # Cap at 10
    
    def extract_text_features(self, text: str) -> Dict[str, int]:
        """Extract text features"""
        if not text:
            return {
                'word_count': 0,
                'char_count': 0,
                'hashtag_count': 0,
                'mention_count': 0
            }
        
        return {
            'word_count': len(text.split()),
            'char_count': len(text),
            'hashtag_count': len(re.findall(r'#\w+', text)),
            'mention_count': len(re.findall(r'@\w+', text))
        }
    
    def extract_temporal_features(self, timestamp: datetime) -> Dict[str, Any]:
        """Extract temporal features"""
        return {
            'hour_of_day': timestamp.hour,
            'day_of_week': timestamp.weekday(),  # 0 = Monday
            'is_weekend': timestamp.weekday() >= 5
        }
    
    def process_clean_data(self, limit: int = 1000) -> Dict[str, Any]:
        """Extract features from clean data"""
        clean_data = self.db.get_unprocessed_clean_data(limit)
        processed_count = 0
        
        for row in clean_data:
            (clean_id, source, external_id, title, content, author, 
             published_at, likes, shares, comments) = row
            
            try:
                # Skip if no content
                if not title and not content:
                    continue
                    
                # Combine title and content
                full_text = f"{title or ''} {content or ''}".strip()
                
                # Extract features
                sentiment_label, sentiment_score = self.analyze_sentiment(full_text)
                engagement_score = self.calculate_engagement_score(likes or 0, shares or 0, comments or 0)
                text_features = self.extract_text_features(full_text)
                temporal_features = self.extract_temporal_features(published_at or datetime.now())
                
                # Combine all features
                features = {
                    'sentiment_label': sentiment_label,
                    'sentiment_score': sentiment_score,
                    'engagement_score': engagement_score,
                    **text_features,
                    **temporal_features
                }
                
                # Insert features
                success = self.db.insert_features(clean_id, source, external_id, features)
                
                if success:
                    processed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to extract features for {source}:{external_id}: {e}")
        
        logger.info(f"Extracted features for {processed_count} records")
        return {'processed_count': processed_count}
    
    def close(self):
        """Close database connection"""
        self.db.close()


# Utility functions for Airflow
def clean_raw_data(limit: int = 1000) -> Dict[str, Any]:
    """Function to be called by Airflow DAG"""
    cleaner = DataCleaner()
    try:
        return cleaner.process_raw_data(limit)
    finally:
        cleaner.close()


def extract_features(limit: int = 1000) -> Dict[str, Any]:
    """Function to be called by Airflow DAG"""
    extractor = FeatureExtractor()
    try:
        return extractor.process_clean_data(limit)
    finally:
        extractor.close()