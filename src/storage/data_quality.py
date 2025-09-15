"""
Data quality monitoring service.
Validates collected data and provides quality scoring.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import json
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DataQualityResult:
    """Result of data quality validation."""
    is_valid: bool
    quality_score: float
    validation_errors: List[str]
    warnings: List[str]
    validation_timestamp: datetime


class DataQualityValidator:
    """Validates data quality and provides scoring."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define quality thresholds
        self.thresholds = {
            'completeness': 0.8,  # 80% of required fields must be present
            'accuracy': 0.7,       # 70% accuracy threshold
            'consistency': 0.9,    # 90% consistency threshold
            'timeliness': 0.95     # 95% timeliness threshold
        }
    
    def validate_reddit_data(self, data: Dict[str, Any]) -> DataQualityResult:
        """Validate Reddit post data quality."""
        errors = []
        warnings = []
        score = 0.0
        
        try:
            # Required fields for Reddit posts
            required_fields = ['id', 'title', 'author', 'score', 'created_utc']
            optional_fields = ['selftext', 'url', 'subreddit', 'num_comments']
            
            # Check completeness
            completeness_score = self._check_completeness(data, required_fields, optional_fields)
            
            # Check data types and formats
            type_score = self._check_reddit_data_types(data)
            
            # Check content quality
            content_score = self._check_reddit_content_quality(data)
            
            # Check timeliness
            timeliness_score = self._check_timeliness(data.get('created_utc'))
            
            # Calculate overall score
            score = (completeness_score + type_score + content_score + timeliness_score) / 4
            
            # Determine if data is valid
            is_valid = score >= self.thresholds['completeness'] and len(errors) == 0
            
            return DataQualityResult(
                is_valid=is_valid,
                quality_score=score,
                validation_errors=errors,
                warnings=warnings,
                validation_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error validating Reddit data: {e}")
            errors.append(f"Validation error: {str(e)}")
            return DataQualityResult(
                is_valid=False,
                quality_score=0.0,
                validation_errors=errors,
                warnings=warnings,
                validation_timestamp=datetime.utcnow()
            )
    
    def validate_news_data(self, data: Dict[str, Any]) -> DataQualityResult:
        """Validate news article data quality."""
        errors = []
        warnings = []
        score = 0.0
        
        try:
            # Required fields for news articles
            required_fields = ['id', 'title', 'url', 'source_name', 'published_at']
            optional_fields = ['description', 'content', 'author', 'image_url']
            
            # Check completeness
            completeness_score = self._check_completeness(data, required_fields, optional_fields)
            
            # Check data types and formats
            type_score = self._check_news_data_types(data)
            
            # Check content quality
            content_score = self._check_news_content_quality(data)
            
            # Check timeliness
            timeliness_score = self._check_timeliness(data.get('published_at'))
            
            # Calculate overall score
            score = (completeness_score + type_score + content_score + timeliness_score) / 4
            
            # Determine if data is valid
            is_valid = score >= self.thresholds['completeness'] and len(errors) == 0
            
            return DataQualityResult(
                is_valid=is_valid,
                quality_score=score,
                validation_errors=errors,
                warnings=warnings,
                validation_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error validating news data: {e}")
            errors.append(f"Validation error: {str(e)}")
            return DataQualityResult(
                is_valid=False,
                quality_score=0.0,
                validation_errors=errors,
                warnings=warnings,
                validation_timestamp=datetime.utcnow()
            )
    
    def validate_twitter_data(self, data: Dict[str, Any]) -> DataQualityResult:
        """Validate Twitter tweet data quality."""
        errors = []
        warnings = []
        score = 0.0
        
        try:
            # Required fields for Twitter tweets
            required_fields = ['id', 'text', 'created_at', 'author_id']
            optional_fields = ['retweet_count', 'like_count', 'reply_count', 'quote_count']
            
            # Check completeness
            completeness_score = self._check_completeness(data, required_fields, optional_fields)
            
            # Check data types and formats
            type_score = self._check_twitter_data_types(data)
            
            # Check content quality
            content_score = self._check_twitter_content_quality(data)
            
            # Check timeliness
            timeliness_score = self._check_timeliness(data.get('created_at'))
            
            # Calculate overall score
            score = (completeness_score + type_score + content_score + timeliness_score) / 4
            
            # Determine if data is valid
            is_valid = score >= self.thresholds['completeness'] and len(errors) == 0
            
            return DataQualityResult(
                is_valid=is_valid,
                quality_score=score,
                validation_errors=errors,
                warnings=warnings,
                validation_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error validating Twitter data: {e}")
            errors.append(f"Validation error: {str(e)}")
            return DataQualityResult(
                is_valid=False,
                quality_score=0.0,
                validation_errors=errors,
                warnings=warnings,
                validation_timestamp=datetime.utcnow()
            )
    
    def _check_completeness(self, data: Dict[str, Any], required_fields: List[str], 
                           optional_fields: List[str]) -> float:
        """Check data completeness score."""
        if not data:
            return 0.0
        
        # Count required fields present
        required_present = sum(1 for field in required_fields if field in data and data[field] is not None)
        required_total = len(required_fields)
        
        # Count optional fields present
        optional_present = sum(1 for field in optional_fields if field in data and data[field] is not None)
        optional_total = len(optional_fields)
        
        # Calculate completeness score (weighted towards required fields)
        required_score = required_present / required_total if required_total > 0 else 0.0
        optional_score = optional_present / optional_total if optional_total > 0 else 0.0
        
        # Weight required fields more heavily (70% required, 30% optional)
        completeness_score = (required_score * 0.7) + (optional_score * 0.3)
        
        return completeness_score
    
    def _check_reddit_data_types(self, data: Dict[str, Any]) -> float:
        """Check Reddit data type consistency."""
        score = 0.0
        checks = 0
        
        # Check ID is string or integer
        if 'id' in data:
            if isinstance(data['id'], (str, int)):
                score += 1.0
            checks += 1
        
        # Check score is numeric
        if 'score' in data:
            if isinstance(data['score'], (int, float)):
                score += 1.0
            checks += 1
        
        # Check created_utc is numeric
        if 'created_utc' in data:
            if isinstance(data['created_utc'], (int, float)):
                score += 1.0
            checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _check_news_data_types(self, data: Dict[str, Any]) -> float:
        """Check news data type consistency."""
        score = 0.0
        checks = 0
        
        # Check ID is string or integer
        if 'id' in data:
            if isinstance(data['id'], (str, int)):
                score += 1.0
            checks += 1
        
        # Check URL is string and valid format
        if 'url' in data:
            if isinstance(data['url'], str) and data['url'].startswith('http'):
                score += 1.0
            checks += 1
        
        # Check published_at is string or datetime
        if 'published_at' in data:
            if isinstance(data['published_at'], str):
                score += 1.0
            checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _check_twitter_data_types(self, data: Dict[str, Any]) -> float:
        """Check Twitter data type consistency."""
        score = 0.0
        checks = 0
        
        # Check ID is string
        if 'id' in data:
            if isinstance(data['id'], str):
                score += 1.0
            checks += 1
        
        # Check text is string
        if 'text' in data:
            if isinstance(data['text'], str):
                score += 1.0
            checks += 1
        
        # Check metrics are numeric
        for metric in ['retweet_count', 'like_count', 'reply_count', 'quote_count']:
            if metric in data:
                if isinstance(data[metric], (int, float)):
                    score += 1.0
                checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _check_reddit_content_quality(self, data: Dict[str, Any]) -> float:
        """Check Reddit content quality."""
        score = 0.0
        checks = 0
        
        # Check title length
        if 'title' in data and data['title']:
            title_length = len(data['title'])
            if 5 <= title_length <= 300:  # Reasonable title length
                score += 1.0
            checks += 1
        
        # Check score is reasonable
        if 'score' in data:
            score_value = data['score']
            if isinstance(score_value, (int, float)) and score_value >= 0:
                score += 1.0
            checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _check_news_content_quality(self, data: Dict[str, Any]) -> float:
        """Check news content quality."""
        score = 0.0
        checks = 0
        
        # Check title length
        if 'title' in data and data['title']:
            title_length = len(data['title'])
            if 10 <= title_length <= 200:  # Reasonable title length
                score += 1.0
            checks += 1
        
        # Check description length
        if 'description' in data and data['description']:
            desc_length = len(data['description'])
            if desc_length >= 20:  # Minimum description length
                score += 1.0
            checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _check_twitter_content_quality(self, data: Dict[str, Any]) -> float:
        """Check Twitter content quality."""
        score = 0.0
        checks = 0
        
        # Check text length
        if 'text' in data and data['text']:
            text_length = len(data['text'])
            if 1 <= text_length <= 280:  # Twitter character limit
                score += 1.0
            checks += 1
        
        # Check metrics are reasonable
        for metric in ['retweet_count', 'like_count', 'reply_count', 'quote_count']:
            if metric in data:
                metric_value = data[metric]
                if isinstance(metric_value, (int, float)) and metric_value >= 0:
                    score += 1.0
                checks += 1
        
        return score / checks if checks > 0 else 0.0
    
    def _check_timeliness(self, timestamp) -> float:
        """Check data timeliness."""
        if not timestamp:
            return 0.0
        
        try:
            # Convert timestamp to datetime if needed
            if isinstance(timestamp, (int, float)):
                # Unix timestamp
                dt = datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                # ISO format string
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            # Calculate age in hours (make both timestamps timezone-aware)
            from datetime import timezone
            utc_now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_hours = (utc_now - dt).total_seconds() / 3600
            
            # Score based on age (newer = higher score)
            if age_hours <= 1:  # Less than 1 hour
                return 1.0
            elif age_hours <= 24:  # Less than 1 day
                return 0.9
            elif age_hours <= 168:  # Less than 1 week
                return 0.7
            else:  # Older than 1 week
                return 0.5
                
        except Exception as e:
            self.logger.warning(f"Error checking timeliness: {e}")
            return 0.5
    
    def get_quality_summary(self, validation_results: List[DataQualityResult]) -> Dict[str, Any]:
        """Get summary of data quality validation results."""
        if not validation_results:
            return {}
        
        total_records = len(validation_results)
        valid_records = sum(1 for result in validation_results if result.is_valid)
        avg_quality_score = sum(result.quality_score for result in validation_results) / total_records
        
        # Count validation errors and warnings
        total_errors = sum(len(result.validation_errors) for result in validation_results)
        total_warnings = sum(len(result.warnings) for result in validation_results)
        
        return {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': total_records - valid_records,
            'validation_rate': valid_records / total_records if total_records > 0 else 0.0,
            'average_quality_score': avg_quality_score,
            'total_validation_errors': total_errors,
            'total_warnings': total_warnings,
            'quality_grade': self._get_quality_grade(avg_quality_score)
        }
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'


# Global validator instance
data_quality_validator = DataQualityValidator()


def get_data_quality_validator() -> DataQualityValidator:
    """Get the global data quality validator instance."""
    return data_quality_validator
