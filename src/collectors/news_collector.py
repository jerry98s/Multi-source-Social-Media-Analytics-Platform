"""
News data collector using News API.
Collects articles from major news outlets and publications.
"""

import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import requests
from newsapi import NewsApiClient

from .base_collector import BaseCollector


class NewsCollector(BaseCollector):
    """Collector for news data using News API."""
    
    def __init__(self, api_key: str):
        super().__init__(name="news", rate_limit_delay=1.0, max_retries=3)
        
        # News API credentials
        self.api_key = api_key
        
        # Initialize News API client
        self.newsapi = NewsApiClient(api_key=api_key)
        
        # Rate limiting settings
        self.rate_limit_remaining = 100  # News API rate limit
        self.rate_limit_reset = None
        
        # Default sources for technology news
        self.default_sources = [
            'techcrunch', 'wired', 'ars-technica', 'the-verge', 'engadget',
            'reuters', 'bloomberg', 'cnn', 'bbc-news', 'the-guardian-uk'
        ]
        
    async def collect_data(self, query: str = None, sources: List[str] = None,
                          category: str = None, country: str = 'us', 
                          language: str = 'en', limit: int = 100, **kwargs) -> List[Dict[str, Any]]:
        """Collect news data based on query, sources, or category."""
        try:
            if query:
                return await self._search_news(query, language, limit)
            elif sources:
                return await self._get_news_from_sources(sources, limit)
            elif category:
                return await self._get_news_by_category(category, country, limit)
            else:
                # Default to top headlines
                return await self._get_top_headlines(country, limit)
                
        except Exception as e:
            self.logger.error(f"Error collecting news data: {e}")
            raise
    
    async def _search_news(self, query: str, language: str = 'en', limit: int = 100) -> List[Dict[str, Any]]:
        """Search for news articles using a query string."""
        articles = []
        
        try:
            # Use asyncio to run the synchronous News API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.newsapi.get_everything(
                    q=query,
                    language=language,
                    sort_by='relevancy',
                    page_size=min(limit, 100)  # News API max is 100 per request
                )
            )
            
            if response['status'] == 'ok' and response['articles']:
                for article in response['articles']:
                    try:
                        article_data = {
                            'id': self._generate_article_id(article),
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'content': article.get('content', ''),
                            'url': article.get('url', ''),
                            'url_to_image': article.get('urlToImage', ''),
                            'source_name': article.get('source', {}).get('name', ''),
                            'source_id': article.get('source', {}).get('id', ''),
                            'author': article.get('author', ''),
                            'published_at': article.get('publishedAt', ''),
                            'language': language,
                            'query': query,
                            'source': 'news',
                            'collected_at': datetime.utcnow().isoformat()
                        }
                        
                        articles.append(article_data)
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing article: {e}")
                        continue
            
            self.logger.info(f"Collected {len(articles)} articles for query: {query}")
            
        except Exception as e:
            self.logger.error(f"Error searching news: {e}")
            raise
            
        return articles
    
    async def _get_news_from_sources(self, sources: List[str], limit: int = 100) -> List[Dict[str, Any]]:
        """Get news articles from specific sources."""
        all_articles = []
        articles_per_source = limit // len(sources)
        
        for source in sources:
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.newsapi.get_top_headlines(
                        sources=source,
                        page_size=min(articles_per_source, 100)
                    )
                )
                
                if response['status'] == 'ok' and response['articles']:
                    for article in response['articles']:
                        try:
                            article_data = {
                                'id': self._generate_article_id(article),
                                'title': article.get('title', ''),
                                'description': article.get('description', ''),
                                'content': article.get('content', ''),
                                'url': article.get('url', ''),
                                'url_to_image': article.get('urlToImage', ''),
                                'source_name': article.get('source', {}).get('name', ''),
                                'source_id': article.get('source', {}).get('id', ''),
                                'author': article.get('author', ''),
                                'published_at': article.get('publishedAt', ''),
                                'source': 'news',
                                'collected_at': datetime.utcnow().isoformat()
                            }
                            
                            all_articles.append(article_data)
                            
                        except Exception as e:
                            self.logger.warning(f"Error processing article from {source}: {e}")
                            continue
                            
            except Exception as e:
                self.logger.warning(f"Failed to get articles from {source}: {e}")
                continue
        
        return all_articles[:limit]
    
    async def _get_news_by_category(self, category: str, country: str = 'us', limit: int = 100) -> List[Dict[str, Any]]:
        """Get news articles by category."""
        articles = []
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.newsapi.get_top_headlines(
                    category=category,
                    country=country,
                    page_size=min(limit, 100)
                )
            )
            
            if response['status'] == 'ok' and response['articles']:
                for article in response['articles']:
                    try:
                        article_data = {
                            'id': self._generate_article_id(article),
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'content': article.get('content', ''),
                            'url': article.get('url', ''),
                            'url_to_image': article.get('urlToImage', ''),
                            'source_name': article.get('source', {}).get('name', ''),
                            'source_id': article.get('source', {}).get('id', ''),
                            'author': article.get('author', ''),
                            'published_at': article.get('publishedAt', ''),
                            'category': category,
                            'country': country,
                            'source': 'news',
                            'collected_at': datetime.utcnow().isoformat()
                        }
                        
                        articles.append(article_data)
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing article: {e}")
                        continue
            
            self.logger.info(f"Collected {len(articles)} articles for category: {category}")
            
        except Exception as e:
            self.logger.error(f"Error getting news by category: {e}")
            raise
            
        return articles
    
    async def _get_top_headlines(self, country: str = 'us', limit: int = 100) -> List[Dict[str, Any]]:
        """Get top headlines for a country."""
        articles = []
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.newsapi.get_top_headlines(
                    country=country,
                    page_size=min(limit, 100)
                )
            )
            
            if response['status'] == 'ok' and response['articles']:
                for article in response['articles']:
                    try:
                        article_data = {
                            'id': self._generate_article_id(article),
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'content': article.get('content', ''),
                            'url': article.get('url', ''),
                            'url_to_image': article.get('urlToImage', ''),
                            'source_name': article.get('source', {}).get('name', ''),
                            'source_id': article.get('source', {}).get('id', ''),
                            'author': article.get('author', ''),
                            'published_at': article.get('publishedAt', ''),
                            'country': country,
                            'source': 'news',
                            'collected_at': datetime.utcnow().isoformat()
                        }
                        
                        articles.append(article_data)
                        
                    except Exception as e:
                        self.logger.warning(f"Error processing article: {e}")
                        continue
            
            self.logger.info(f"Collected {len(articles)} top headlines for {country}")
            
        except Exception as e:
            self.logger.error(f"Error getting top headlines: {e}")
            raise
            
        return articles
    
    async def get_technology_news(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get technology-related news articles."""
        tech_queries = ['artificial intelligence', 'machine learning', 'data science', 
                       'python programming', 'technology trends', 'startup news']
        
        all_articles = []
        articles_per_query = limit // len(tech_queries)
        
        for query in tech_queries:
            try:
                articles = await self._search_news(query, limit=articles_per_query)
                all_articles.extend(articles)
            except Exception as e:
                self.logger.warning(f"Failed to get articles for query '{query}': {e}")
                continue
        
        return all_articles[:limit]
    
    def _generate_article_id(self, article: Dict[str, Any]) -> str:
        """Generate a unique ID for an article."""
        # Use URL hash or title hash as ID
        url = article.get('url', '')
        title = article.get('title', '')
        
        if url:
            return str(hash(url))
        elif title:
            return str(hash(title))
        else:
            return str(hash(str(article)))
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate news data structure."""
        if not data:
            return False
            
        required_fields = ['id', 'title', 'source_name', 'url']
        return all(field in data for field in required_fields)
    
    def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform news data to standard format."""
        return {
            'id': data['id'],
            'title': data['title'],
            'description': data.get('description', ''),
            'content': data.get('content', ''),
            'url': data['url'],
            'image_url': data.get('url_to_image', ''),
            'source_name': data['source_name'],
            'source_id': data.get('source_id', ''),
            'author': data.get('author', ''),
            'published_at': data.get('published_at'),
            'category': data.get('category', ''),
            'country': data.get('country', ''),
            'language': data.get('language', 'en'),
            'query': data.get('query', ''),
            'engagement_score': self._calculate_engagement_score(data),
            'source': 'news',
            'collected_at': data.get('collected_at'),
            'raw_data': data
        }
    
    def _calculate_engagement_score(self, data: Dict[str, Any]) -> float:
        """Calculate engagement score based on content quality and source reputation."""
        score = 0.0
        
        # Content length score
        title_length = len(data.get('title', ''))
        description_length = len(data.get('description', ''))
        content_length = len(data.get('content', ''))
        
        score += min(title_length / 100, 1.0) * 10
        score += min(description_length / 200, 1.0) * 15
        score += min(content_length / 1000, 1.0) * 25
        
        # Source reputation score (simplified)
        reputable_sources = ['reuters', 'bloomberg', 'bbc-news', 'the-guardian-uk', 'cnn']
        if data.get('source_name', '').lower() in reputable_sources:
            score += 20
        
        # Image presence bonus
        if data.get('url_to_image'):
            score += 10
        
        return round(score, 2)
    
    async def get_sources(self, category: str = None, language: str = 'en', country: str = 'us') -> List[Dict[str, Any]]:
        """Get available news sources."""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.newsapi.get_sources(
                    category=category,
                    language=language,
                    country=country
                )
            )
            
            if response['status'] == 'ok':
                sources = []
                for source in response['sources']:
                    source_data = {
                        'id': source.get('id', ''),
                        'name': source.get('name', ''),
                        'description': source.get('description', ''),
                        'url': source.get('url', ''),
                        'category': source.get('category', ''),
                        'language': source.get('language', ''),
                        'country': source.get('country', ''),
                        'source': 'news',
                        'collected_at': datetime.utcnow().isoformat()
                    }
                    sources.append(source_data)
                
                return sources
                
        except Exception as e:
            self.logger.error(f"Error getting sources: {e}")
            return []
    
    def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get current rate limit information."""
        return {
            'remaining': self.rate_limit_remaining,
            'reset_time': self.rate_limit_reset,
            'source': 'news'
        }


# Factory function for creating News collector from environment variables
def create_news_collector() -> NewsCollector:
    """Create a News collector using environment variables."""
    api_key = os.getenv('NEWS_API_KEY')
    
    if not api_key:
        raise ValueError("Missing News API key in environment variables")
    
    return NewsCollector(api_key=api_key)


if __name__ == "__main__":
    # Example usage
    async def main():
        try:
            collector = create_news_collector()
            
            # Test collection
            articles = await collector.collect_with_retry(query="artificial intelligence", limit=10)
            print(f"Collected {len(articles)} articles")
            
            # Print stats
            stats = collector.get_collection_stats()
            print(f"Collection stats: {stats}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    asyncio.run(main())
