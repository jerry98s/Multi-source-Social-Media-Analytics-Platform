"""
Base collector class for social media data collection.
Provides common functionality for all collectors.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import structlog
from prometheus_client import Counter, Histogram, Gauge


class BaseCollector(ABC):
    """Base class for all data collectors."""
    
    def __init__(self, name: str, rate_limit_delay: float = 1.0, max_retries: int = 3):
        self.name = name
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        
        # Setup logging
        self.logger = structlog.get_logger(__name__)
        
        # Setup metrics with unique names
        self.collection_counter = Counter(
            f'{name}_data_collections_total',
            'Total number of data collections',
            ['source', 'status']
        )
        self.collection_duration = Histogram(
            f'{name}_data_collection_duration_seconds',
            'Time spent collecting data',
            ['source']
        )
        self.data_volume_gauge = Gauge(
            f'{name}_data_volume_bytes',
            'Volume of data collected',
            ['source']
        )
        self.error_counter = Counter(
            f'{name}_data_errors_total',
            'Total number of errors',
            ['source', 'error_type']
        )
        
        # Collection state
        self.last_collection = None
        self.collection_count = 0
        self.error_count = 0
        
    @abstractmethod
    async def collect_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect data from the source. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate collected data. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw data to standard format. Must be implemented by subclasses."""
        pass
    
    async def collect_with_retry(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect data with retry logic and rate limiting."""
        start_time = time.time()
        
        try:
            # Rate limiting
            if self.last_collection:
                time_since_last = time.time() - self.last_collection
                if time_since_last < self.rate_limit_delay:
                    await asyncio.sleep(self.rate_limit_delay - time_since_last)
            
            # Collect data with retries
            for attempt in range(self.max_retries):
                try:
                    raw_data = await self.collect_data(**kwargs)
                    
                    # Validate and transform data
                    processed_data = []
                    for item in raw_data:
                        if self.validate_data(item):
                            transformed_item = self.transform_data(item)
                            processed_data.append(transformed_item)
                    
                    # Update metrics
                    duration = time.time() - start_time
                    self.collection_duration.labels(source=self.name).observe(duration)
                    self.collection_counter.labels(source=self.name, status='success').inc()
                    self.data_volume_gauge.labels(source=self.name).set(len(str(processed_data)))
                    
                    # Update state
                    self.last_collection = time.time()
                    self.collection_count += 1
                    
                    self.logger.info(
                        f"Successfully collected {len(processed_data)} items from {self.name}",
                        source=self.name,
                        items_collected=len(processed_data),
                        duration=duration,
                        attempt=attempt + 1
                    )
                    
                    return processed_data
                    
                except Exception as e:
                    self.logger.warning(
                        f"Collection attempt {attempt + 1} failed for {self.name}",
                        source=self.name,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    
                    if attempt == self.max_retries - 1:
                        raise
                    
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
            
        except Exception as e:
            # Update error metrics
            self.error_counter.labels(source=self.name, error_type=type(e).__name__).inc()
            self.error_count += 1
            
            self.logger.error(
                f"Failed to collect data from {self.name} after {self.max_retries} attempts",
                source=self.name,
                error=str(e),
                error_type=type(e).__name__
            )
            
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            'name': self.name,
            'collection_count': self.collection_count,
            'error_count': self.error_count,
            'last_collection': self.last_collection,
            'success_rate': (self.collection_count - self.error_count) / max(self.collection_count, 1)
        }
    
    async def health_check(self) -> bool:
        """Perform a health check on the collector."""
        try:
            # Try to collect a small amount of data
            test_data = await self.collect_data(limit=1)
            return len(test_data) >= 0  # Just check if it doesn't raise an exception
        except Exception as e:
            self.logger.error(f"Health check failed for {self.name}: {e}")
            return False
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()
