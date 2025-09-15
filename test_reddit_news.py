#!/usr/bin/env python3
"""
Test script for Reddit and News collectors only.
Bypasses Twitter to avoid rate limit issues.
"""

import asyncio
import os
from dotenv import load_dotenv
from src.collectors.reddit_collector import create_reddit_collector
from src.collectors.news_collector import create_news_collector

# Load environment variables
load_dotenv()

async def test_reddit_news():
    """Test only Reddit and News collectors."""
    print("🧪 Testing Reddit and News Collectors Only")
    print("=" * 50)
    
    results = {}
    
    # Test Reddit Collector
    try:
        print("\n📱 Testing Reddit Collector...")
        reddit_collector = create_reddit_collector()
        
        # Test collecting from r/technology
        reddit_data = await reddit_collector.collect_with_retry(
            subreddit='technology', 
            limit=10
        )
        
        print(f"✅ Reddit: Collected {len(reddit_data)} posts from r/technology")
        results['reddit'] = reddit_data
        
        # Show sample data
        if reddit_data:
            sample = reddit_data[0]
            print(f"   Sample post: {sample.get('title', 'No title')[:50]}...")
            print(f"   Author: {sample.get('author', 'Unknown')}")
            print(f"   Score: {sample.get('score', 0)}")
            
    except Exception as e:
        print(f"❌ Reddit Collector Error: {e}")
        results['reddit'] = []
    
    # Test News Collector
    try:
        print("\n📰 Testing News Collector...")
        news_collector = create_news_collector()
        
        # Test collecting technology news
        news_data = await news_collector.collect_with_retry(
            query='artificial intelligence', 
            limit=10
        )
        
        print(f"✅ News: Collected {len(news_data)} articles")
        results['news'] = news_data
        
        # Show sample data
        if news_data:
            sample = news_data[0]
            print(f"   Sample article: {sample.get('title', 'No title')[:50]}...")
            print(f"   Source: {sample.get('source_name', 'Unknown')}")
            print(f"   Published: {sample.get('published_at', 'Unknown')}")
            
    except Exception as e:
        print(f"❌ News Collector Error: {e}")
        results['news'] = []
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Reddit: {len(results.get('reddit', []))} posts collected")
    print(f"   News: {len(results.get('news', []))} articles collected")
    
    total_items = len(results.get('reddit', [])) + len(results.get('news', []))
    print(f"\n🎉 Total items collected: {total_items}")
    
    if total_items > 0:
        print("✅ Platform is working! Ready to move to Phase 2 (Data Lake)")
    else:
        print("⚠️  Some issues detected. Check API credentials and network.")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_reddit_news())
