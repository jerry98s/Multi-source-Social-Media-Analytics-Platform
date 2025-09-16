"""
Rate limiting utilities for API calls
Handles rate limiting across different APIs with proper backoff strategies
"""

import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10  # Allow burst of requests
    backoff_multiplier: float = 2.0  # Exponential backoff


class RateLimiter:
    """Thread-safe rate limiter with multiple time windows"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.lock = Lock()
        self.request_times = {
            'minute': [],
            'hour': [],
            'day': []
        }
        self.last_request_time = 0
        self.consecutive_failures = 0
        
    def _clean_old_requests(self, window: str, max_age: int):
        """Remove requests older than max_age seconds"""
        current_time = time.time()
        cutoff_time = current_time - max_age
        self.request_times[window] = [
            req_time for req_time in self.request_times[window]
            if req_time > cutoff_time
        ]
    
    def _can_make_request(self) -> bool:
        """Check if we can make a request without exceeding limits"""
        current_time = time.time()
        
        # Clean old requests
        self._clean_old_requests('minute', 60)
        self._clean_old_requests('hour', 3600)
        self._clean_old_requests('day', 86400)
        
        # Check limits
        if len(self.request_times['minute']) >= self.config.requests_per_minute:
            return False
        if len(self.request_times['hour']) >= self.config.requests_per_hour:
            return False
        if len(self.request_times['day']) >= self.config.requests_per_day:
            return False
            
        return True
    
    def _calculate_delay(self) -> float:
        """Calculate delay needed before next request"""
        if self.consecutive_failures == 0:
            return 0
        
        # Exponential backoff with jitter
        base_delay = min(60, self.config.backoff_multiplier ** self.consecutive_failures)
        jitter = base_delay * 0.1 * (0.5 - time.time() % 1)  # ±10% jitter
        return max(1, base_delay + jitter)
    
    def wait_if_needed(self) -> float:
        """Wait if necessary to respect rate limits. Returns actual delay."""
        with self.lock:
            current_time = time.time()
            delay = 0
            
            # Check if we need to wait
            if not self._can_make_request():
                # Calculate minimum delay needed
                if self.request_times['minute']:
                    oldest_minute_request = min(self.request_times['minute'])
                    delay = max(delay, 60 - (current_time - oldest_minute_request))
                
                if self.request_times['hour']:
                    oldest_hour_request = min(self.request_times['hour'])
                    delay = max(delay, 3600 - (current_time - oldest_hour_request))
                
                if self.request_times['day']:
                    oldest_day_request = min(self.request_times['day'])
                    delay = max(delay, 86400 - (current_time - oldest_day_request))
            
            # Add exponential backoff if we've had failures
            backoff_delay = self._calculate_delay()
            delay = max(delay, backoff_delay)
            
            if delay > 0:
                logger.info(f"Rate limiting: waiting {delay:.2f} seconds")
                time.sleep(delay)
            
            # Record this request
            self.request_times['minute'].append(current_time)
            self.request_times['hour'].append(current_time)
            self.request_times['day'].append(current_time)
            
            return delay
    
    def record_success(self):
        """Record a successful request"""
        with self.lock:
            self.consecutive_failures = 0
    
    def record_failure(self):
        """Record a failed request (rate limited)"""
        with self.lock:
            self.consecutive_failures += 1


class APIRateLimiter:
    """Centralized rate limiter for all APIs"""
    
    def __init__(self):
        self.limiters = {
            'reddit': RateLimiter(RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=3600,
                requests_per_day=86400
            )),
            'news': RateLimiter(RateLimitConfig(
                requests_per_minute=1,  # Conservative for daily limits
                requests_per_hour=4,
                requests_per_day=100  # Free tier limit
            )),
            'twitter': RateLimiter(RateLimitConfig(
                requests_per_minute=1,  # Conservative for monthly limits
                requests_per_hour=2,
                requests_per_day=50  # Conservative for 1500/month
            ))
        }
    
    def wait_for_api(self, api_name: str) -> float:
        """Wait for the specified API if needed"""
        if api_name not in self.limiters:
            logger.warning(f"Unknown API: {api_name}")
            return 0
        
        return self.limiters[api_name].wait_if_needed()
    
    def record_success(self, api_name: str):
        """Record successful request for API"""
        if api_name in self.limiters:
            self.limiters[api_name].record_success()
    
    def record_failure(self, api_name: str):
        """Record failed request for API"""
        if api_name in self.limiters:
            self.limiters[api_name].record_failure()


# Global rate limiter instance
rate_limiter = APIRateLimiter()


def with_rate_limit(api_name: str):
    """Decorator to add rate limiting to API calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = rate_limiter.wait_for_api(api_name)
            try:
                result = func(*args, **kwargs)
                rate_limiter.record_success(api_name)
                return result
            except Exception as e:
                if "rate limit" in str(e).lower() or "429" in str(e):
                    rate_limiter.record_failure(api_name)
                raise
        return wrapper
    return decorator
