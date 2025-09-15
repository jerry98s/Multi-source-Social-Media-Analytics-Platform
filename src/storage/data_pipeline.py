"""
Data pipeline service that integrates collection, validation, and storage.
Implements the complete Bronze/Silver/Gold data lake architecture.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .database import get_data_lake_storage
from .data_quality import get_data_quality_validator, DataQualityResult
from ..collectors.orchestrator import create_orchestrator

logger = logging.getLogger(__name__)


class DataPipeline:
    """Main data pipeline orchestrating the complete data flow."""
    
    def __init__(self):
        self.storage = get_data_lake_storage()
        self.validator = get_data_quality_validator()
        self.orchestrator = create_orchestrator()
        self.logger = logging.getLogger(__name__)
        
        # Pipeline metrics
        self.total_processed = 0
        self.successful_stores = 0
        self.failed_stores = 0
        self.avg_quality_score = 0.0
    
    async def run_collection_pipeline(self, collection_type: str = 'technology', 
                                    limit: int = 100) -> Dict[str, Any]:
        """Run the complete data collection and storage pipeline."""
        start_time = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting data collection pipeline for {collection_type}")
            
            # Step 1: Collect data from all sources
            collected_data = await self._collect_data(collection_type, limit)
            
            # Step 2: Process and store data through Bronze/Silver/Gold layers
            pipeline_results = await self._process_and_store_data(collected_data)
            
            # Step 3: Generate pipeline summary
            duration = (datetime.utcnow() - start_time).total_seconds()
            summary = self._generate_pipeline_summary(pipeline_results, duration)
            
            self.logger.info(f"Pipeline completed successfully in {duration:.2f} seconds")
            return summary
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            raise
    
    async def _collect_data(self, collection_type: str, limit: int) -> Dict[str, List[Dict[str, Any]]]:
        """Collect data from all available sources."""
        try:
            if collection_type == 'technology':
                return await self.orchestrator.collect_technology_data(limit)
            elif collection_type == 'trending':
                return await self.orchestrator.collect_trending_data(limit)
            else:
                # Default collection
                return await self.orchestrator.collect_all_data()
                
        except Exception as e:
            self.logger.error(f"Data collection failed: {e}")
            raise
    
    async def _process_and_store_data(self, collected_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Process and store data through Bronze/Silver/Gold layers."""
        pipeline_results = {
            'bronze_layer': {},
            'silver_layer': {},
            'gold_layer': {},
            'quality_metrics': {},
            'errors': []
        }
        
        for source, data_items in collected_data.items():
            if not data_items:
                continue
                
            self.logger.info(f"Processing {len(data_items)} items from {source}")
            
            try:
                # Process each data item through the pipeline
                source_results = await self._process_source_data(source, data_items)
                
                # Store results
                pipeline_results['bronze_layer'][source] = source_results['bronze_ids']
                pipeline_results['silver_layer'][source] = source_results['silver_ids']
                pipeline_results['gold_layer'][source] = source_results['gold_ids']
                pipeline_results['quality_metrics'][source] = source_results['quality_summary']
                
            except Exception as e:
                error_msg = f"Failed to process {source} data: {e}"
                self.logger.error(error_msg)
                pipeline_results['errors'].append(error_msg)
        
        return pipeline_results
    
    async def _process_source_data(self, source: str, data_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process data from a specific source through the pipeline."""
        bronze_ids = []
        silver_ids = []
        gold_ids = []
        quality_results = []
        
        for item in data_items:
            try:
                # Bronze Layer: Store raw data
                bronze_id = self.storage.store_bronze_data(
                    data=item,
                    source=source,
                    data_type=self._get_data_type(source)
                )
                bronze_ids.append(bronze_id)
                
                # Silver Layer: Validate and store processed data
                quality_result = self._validate_data(source, item)
                quality_results.append(quality_result)
                
                silver_id = self.storage.store_silver_data(
                    bronze_id=bronze_id,
                    processed_data=item,
                    validation_status='valid' if quality_result.is_valid else 'invalid',
                    quality_score=quality_result.quality_score
                )
                silver_ids.append(silver_id)
                
                # Gold Layer: Store analytics data (if valid)
                if quality_result.is_valid:
                    analytics_data = self._generate_analytics_data(item, source)
                    metrics = self._calculate_metrics(item, source)
                    
                    gold_id = self.storage.store_gold_data(
                        processed_data_id=silver_id,
                        analytics_data=analytics_data,
                        aggregation_type='individual',
                        metrics=metrics
                    )
                    gold_ids.append(gold_id)
                
                self.total_processed += 1
                if quality_result.is_valid:
                    self.successful_stores += 1
                else:
                    self.failed_stores += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process item from {source}: {e}")
                continue
        
        # Calculate quality summary for this source
        quality_summary = self.validator.get_quality_summary(quality_results)
        
        return {
            'bronze_ids': bronze_ids,
            'silver_ids': silver_ids,
            'gold_ids': gold_ids,
            'quality_summary': quality_summary
        }
    
    def _validate_data(self, source: str, data: Dict[str, Any]) -> DataQualityResult:
        """Validate data quality based on source."""
        if source == 'reddit':
            return self.validator.validate_reddit_data(data)
        elif source == 'news':
            return self.validator.validate_news_data(data)
        elif source == 'twitter':
            return self.validator.validate_twitter_data(data)
        else:
            # Generic validation for unknown sources
            return self.validator.validate_reddit_data(data)  # Use Reddit as default
    
    def _get_data_type(self, source: str) -> str:
        """Get data type based on source."""
        data_types = {
            'reddit': 'reddit_post',
            'news': 'news_article',
            'twitter': 'tweet'
        }
        return data_types.get(source, 'unknown')
    
    def _generate_analytics_data(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Generate analytics data for Gold layer."""
        analytics = {
            'source': source,
            'content_type': self._get_data_type(source),
            'engagement_metrics': self._extract_engagement_metrics(item, source),
            'content_analysis': self._analyze_content(item, source),
            'temporal_features': self._extract_temporal_features(item, source)
        }
        
        return analytics
    
    def _extract_engagement_metrics(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Extract engagement metrics from data item."""
        metrics = {}
        
        if source == 'reddit':
            metrics = {
                'score': item.get('score', 0),
                'num_comments': item.get('num_comments', 0),
                'upvote_ratio': item.get('upvote_ratio', 0.0)
            }
        elif source == 'news':
            metrics = {
                'engagement_score': item.get('engagement_score', 0.0),
                'content_length': len(item.get('content', '')),
                'has_image': bool(item.get('image_url'))
            }
        elif source == 'twitter':
            metrics = {
                'retweet_count': item.get('retweet_count', 0),
                'like_count': item.get('like_count', 0),
                'reply_count': item.get('reply_count', 0),
                'quote_count': item.get('quote_count', 0)
            }
        
        return metrics
    
    def _analyze_content(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Analyze content characteristics."""
        content = item.get('text', '') or item.get('title', '') or item.get('content', '')
        
        analysis = {
            'content_length': len(content),
            'word_count': len(content.split()) if content else 0,
            'has_hashtags': '#' in content if content else False,
            'has_mentions': '@' in content if content else False,
            'has_urls': 'http' in content if content else False
        }
        
        return analysis
    
    def _extract_temporal_features(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Extract temporal features from data item."""
        timestamp = item.get('created_at') or item.get('created_utc') or item.get('published_at')
        
        if not timestamp:
            return {}
        
        try:
            # Convert to datetime
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            return {
                'hour_of_day': dt.hour,
                'day_of_week': dt.weekday(),
                'is_weekend': dt.weekday() >= 5,
                'age_hours': (datetime.utcnow() - dt).total_seconds() / 3600
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to extract temporal features: {e}")
            return {}
    
    def _calculate_metrics(self, item: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Calculate business metrics for the data item."""
        metrics = {
            'source': source,
            'processing_timestamp': datetime.utcnow().isoformat(),
            'data_volume_bytes': len(str(item))
        }
        
        # Add source-specific metrics
        if source == 'reddit':
            metrics.update({
                'engagement_score': item.get('score', 0) + (item.get('num_comments', 0) * 2),
                'viral_potential': item.get('score', 0) > 1000
            })
        elif source == 'news':
            metrics.update({
                'readability_score': min(100, len(item.get('content', '')) / 10),
                'source_reputation': self._get_source_reputation(item.get('source_name', ''))
            })
        elif source == 'twitter':
            metrics.update({
                'engagement_score': (item.get('retweet_count', 0) * 2) + 
                                  item.get('like_count', 0) + 
                                  item.get('reply_count', 0),
                'viral_potential': item.get('retweet_count', 0) > 100
            })
        
        return metrics
    
    def _get_source_reputation(self, source_name: str) -> float:
        """Get reputation score for news sources."""
        # This could be enhanced with a real reputation database
        high_reputation = ['BBC', 'Reuters', 'AP', 'CNN', 'NYT', 'WSJ']
        medium_reputation = ['TechCrunch', 'Wired', 'Ars Technica', 'The Verge']
        
        if source_name in high_reputation:
            return 0.9
        elif source_name in medium_reputation:
            return 0.7
        else:
            return 0.5
    
    def _generate_pipeline_summary(self, pipeline_results: Dict[str, Any], 
                                 duration: float) -> Dict[str, Any]:
        """Generate comprehensive pipeline summary."""
        # Calculate overall quality score
        all_quality_scores = []
        for source_metrics in pipeline_results['quality_metrics'].values():
            if 'average_quality_score' in source_metrics:
                all_quality_scores.append(source_metrics['average_quality_score'])
        
        overall_quality = sum(all_quality_scores) / len(all_quality_scores) if all_quality_scores else 0.0
        
        # Update pipeline metrics
        self.avg_quality_score = overall_quality
        
        summary = {
            'pipeline_status': 'completed',
            'execution_time_seconds': duration,
            'total_items_processed': self.total_processed,
            'successful_stores': self.successful_stores,
            'failed_stores': self.failed_stores,
            'overall_quality_score': overall_quality,
            'quality_grade': self._get_quality_grade(overall_quality),
            'bronze_layer_summary': {
                source: len(ids) for source, ids in pipeline_results['bronze_layer'].items()
            },
            'silver_layer_summary': {
                source: len(ids) for source, ids in pipeline_results['silver_layer'].items()
            },
            'gold_layer_summary': {
                source: len(ids) for source, ids in pipeline_results['gold_layer'].items()
            },
            'quality_metrics_by_source': pipeline_results['quality_metrics'],
            'errors': pipeline_results['errors'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return summary
    
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
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get current pipeline statistics."""
        return {
            'total_processed': self.total_processed,
            'successful_stores': self.successful_stores,
            'failed_stores': self.failed_stores,
            'success_rate': self.successful_stores / max(self.total_processed, 1),
            'average_quality_score': self.avg_quality_score,
            'quality_grade': self._get_quality_grade(self.avg_quality_score)
        }


# Global pipeline instance
data_pipeline = DataPipeline()


def get_data_pipeline() -> DataPipeline:
    """Get the global data pipeline instance."""
    return data_pipeline


async def run_pipeline(collection_type: str = 'technology', limit: int = 100) -> Dict[str, Any]:
    """Convenience function to run the data pipeline."""
    pipeline = get_data_pipeline()
    return await pipeline.run_collection_pipeline(collection_type, limit)
