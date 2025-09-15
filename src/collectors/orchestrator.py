"""
Data collection orchestrator.
Manages multiple collectors and coordinates data collection from all sources.
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import structlog
from prometheus_client import Counter, Histogram, Gauge

from .twitter_collector import create_twitter_collector
from .reddit_collector import create_reddit_collector
from .news_collector import create_news_collector
from .base_collector import BaseCollector


class DataCollectionOrchestrator:
    """Orchestrates data collection from multiple sources."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        
        # Initialize collectors
        self.collectors: Dict[str, BaseCollector] = {}
        self._initialize_collectors()
        
        # Setup metrics with unique names
        self.orchestration_counter = Counter(
            'orchestrator_collections_total',
            'Total number of orchestrated collections',
            ['status']
        )
        self.orchestration_duration = Histogram(
            'orchestrator_duration_seconds',
            'Time spent orchestrating data collection'
        )
        self.collector_health_gauge = Gauge(
            'orchestrator_collector_health_status',
            'Health status of each collector',
            ['collector_name']
        )
        
        # Collection state
        self.last_orchestration = None
        self.collection_schedule = {}
        
    def _initialize_collectors(self):
        """Initialize available collectors based on environment variables."""
        try:
            # Twitter collector
            if all(os.getenv(var) for var in ['TWITTER_BEARER_TOKEN', 'TWITTER_API_KEY']):
                self.collectors['twitter'] = create_twitter_collector()
                self.logger.info("Twitter collector initialized successfully")
            else:
                self.logger.warning("Twitter collector not initialized - missing credentials")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter collector: {e}")
        
        try:
            # Reddit collector
            if all(os.getenv(var) for var in ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET']):
                self.collectors['reddit'] = create_reddit_collector()
                self.logger.info("Reddit collector initialized successfully")
            else:
                self.logger.warning("Reddit collector not initialized - missing credentials")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Reddit collector: {e}")
        
        try:
            # News collector
            if os.getenv('NEWS_API_KEY'):
                self.collectors['news'] = create_news_collector()
                self.logger.info("News collector initialized successfully")
            else:
                self.logger.warning("News collector not initialized - missing credentials")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize News collector: {e}")
        
        self.logger.info(f"Initialized {len(self.collectors)} collectors: {list(self.collectors.keys())}")
    
    async def collect_all_data(self, collection_config: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Collect data from all available sources."""
        start_time = datetime.utcnow()
        
        if not self.collectors:
            self.logger.error("No collectors available")
            return {}
        
        # Default collection configuration
        if collection_config is None:
            collection_config = {
                'twitter': {'query': '#technology', 'limit': 50},
                'reddit': {'subreddit': 'technology', 'limit': 50},
                'news': {'query': 'artificial intelligence', 'limit': 50}
            }
        
        results = {}
        failed_collectors = []
        
        # Collect data from each source concurrently
        collection_tasks = []
        for collector_name, collector in self.collectors.items():
            if collector_name in collection_config:
                config = collection_config[collector_name]
                task = self._collect_from_source(collector_name, collector, config)
                collection_tasks.append(task)
        
        # Execute all collection tasks concurrently
        if collection_tasks:
            collection_results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            for i, (collector_name, collector) in enumerate(self.collectors.items()):
                if collector_name in collection_config:
                    result = collection_results[i]
                    
                    if isinstance(result, Exception):
                        self.logger.error(f"Collection failed for {collector_name}: {result}")
                        failed_collectors.append(collector_name)
                        results[collector_name] = []
                    else:
                        results[collector_name] = result
                        self.logger.info(f"Successfully collected {len(result)} items from {collector_name}")
        
        # Update metrics
        duration = (datetime.utcnow() - start_time).total_seconds()
        self.orchestration_duration.observe(duration)
        
        if failed_collectors:
            self.orchestration_counter.labels(status='failed').inc()
            self.logger.error(f"Collection failed for collectors: {failed_collectors}")
        else:
            self.orchestration_counter.labels(status='success').inc()
            self.logger.info("All collections completed successfully")
        
        self.last_orchestration = datetime.utcnow()
        
        return results
    
    async def _collect_from_source(self, collector_name: str, collector: BaseCollector, 
                                 config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect data from a specific source."""
        try:
            # Use the collector's retry mechanism
            data = await collector.collect_with_retry(**config)
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting from {collector_name}: {e}")
            raise
    
    async def collect_technology_data(self, limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Collect technology-related data from all sources."""
        # Ensure minimum limits for each collector
        twitter_limit = max(limit // 3, 10)
        reddit_limit = max(limit // 3, 10)
        news_limit = max(limit // 3, 10)
        
        collection_config = {
            'twitter': {'query': '#technology OR #AI OR #machinelearning', 'limit': twitter_limit},
            'reddit': {'subreddit': 'technology', 'limit': reddit_limit},
            'news': {'query': 'artificial intelligence technology', 'limit': news_limit}
        }
        
        return await self.collect_all_data(collection_config)
    
    async def collect_trending_data(self, limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Collect trending data from all sources."""
        # Ensure minimum limits for each collector
        twitter_limit = max(limit // 3, 10)
        reddit_limit = max(limit // 3, 10)
        news_limit = max(limit // 3, 10)
        
        collection_config = {
            'twitter': {'limit': twitter_limit},  # Will use trending tweets
            'reddit': {'subreddit': 'technology', 'limit': reddit_limit},   # Will use popular posts
            'news': {'limit': news_limit}      # Will use top headlines
        }
        
        return await self.collect_all_data(collection_config)
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health checks on all collectors."""
        health_results = {}
        
        for collector_name, collector in self.collectors.items():
            try:
                health_status = await collector.health_check()
                health_results[collector_name] = health_status
                
                # Update metrics
                self.collector_health_gauge.labels(collector_name=collector_name).set(
                    1 if health_status else 0
                )
                
            except Exception as e:
                self.logger.error(f"Health check failed for {collector_name}: {e}")
                health_results[collector_name] = False
                self.collector_health_gauge.labels(collector_name=collector_name).set(0)
        
        return health_results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics for all collectors."""
        stats = {
            'total_collectors': len(self.collectors),
            'collector_names': list(self.collectors.keys()),
            'last_orchestration': self.last_orchestration,
            'collector_stats': {}
        }
        
        for collector_name, collector in self.collectors.items():
            stats['collector_stats'][collector_name] = collector.get_collection_stats()
        
        return stats
    
    async def schedule_collection(self, interval_minutes: int = 15):
        """Schedule periodic data collection."""
        self.logger.info(f"Scheduling data collection every {interval_minutes} minutes")
        
        while True:
            try:
                # Perform health check
                health_status = await self.health_check_all()
                healthy_collectors = [name for name, status in health_status.items() if status]
                
                if healthy_collectors:
                    # Collect trending data
                    await self.collect_trending_data(limit=50)
                    self.logger.info(f"Scheduled collection completed for {len(healthy_collectors)} collectors")
                else:
                    self.logger.warning("No healthy collectors available for scheduled collection")
                
                # Wait for next collection cycle
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in scheduled collection: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_collector_status(self) -> Dict[str, Any]:
        """Get detailed status of all collectors."""
        status = {
            'total_collectors': len(self.collectors),
            'collectors': {}
        }
        
        for collector_name, collector in self.collectors.items():
            status['collectors'][collector_name] = {
                'name': collector.name,
                'class': collector.__class__.__name__,
                'stats': collector.get_collection_stats(),
                'rate_limit_info': collector.get_rate_limit_info() if hasattr(collector, 'get_rate_limit_info') else {}
            }
        
        return status
    
    async def stop_all_collectors(self):
        """Stop all collectors gracefully."""
        self.logger.info("Stopping all collectors...")
        
        for collector_name, collector in self.collectors.items():
            try:
                if hasattr(collector, 'close'):
                    await collector.close()
                self.logger.info(f"Stopped collector: {collector_name}")
            except Exception as e:
                self.logger.error(f"Error stopping collector {collector_name}: {e}")
        
        self.logger.info("All collectors stopped")


# Factory function for creating the orchestrator
def create_orchestrator() -> DataCollectionOrchestrator:
    """Create a data collection orchestrator."""
    return DataCollectionOrchestrator()


if __name__ == "__main__":
    # Example usage
    async def main():
        try:
            orchestrator = create_orchestrator()
            
            # Check collector health
            health = await orchestrator.health_check_all()
            print(f"Collector health: {health}")
            
            # Collect technology data
            data = await orchestrator.collect_technology_data(limit=30)
            
            # Print results
            for source, items in data.items():
                print(f"{source}: {len(items)} items collected")
            
            # Print stats
            stats = orchestrator.get_collection_stats()
            print(f"Orchestrator stats: {stats}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(main())
