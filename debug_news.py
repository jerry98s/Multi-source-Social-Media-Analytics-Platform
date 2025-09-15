#!/usr/bin/env python3
"""
Debug script to see the actual structure of news data.
"""

import asyncio
from dotenv import load_dotenv
from src.collectors.news_collector import create_news_collector

# Load environment variables
load_dotenv()

async def debug_news():
    """Debug the news collector data structure."""
    print("🔍 Debugging News Collector Data Structure")
    print("=" * 50)
    
    try:
        news_collector = create_news_collector()
        
        # Collect just 1 article to see the structure
        news_data = await news_collector.collect_with_retry(
            query='artificial intelligence', 
            limit=1
        )
        
        print(f"✅ Collected {len(news_data)} articles")
        
        if news_data:
            article = news_data[0]
            print("\n📰 Article Data Structure:")
            print(f"   Type: {type(article)}")
            print(f"   Keys: {list(article.keys())}")
            
            print("\n📋 Sample Article Content:")
            for key, value in article.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}...")
                else:
                    print(f"   {key}: {value}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_news())
