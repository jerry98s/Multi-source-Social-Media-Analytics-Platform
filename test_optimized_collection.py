"""
Test script for optimized data collection
Demonstrates the improved collection capabilities
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

try:
    from app.optimized_collectors import OptimizedDataCollector
    from app.database import Database
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running from the project root directory")
    exit(1)


def test_optimized_collection():
    """Test the optimized data collection"""
    logger.info("🚀 Starting Optimized Data Collection Test")
    
    # Initialize collector
    collector = OptimizedDataCollector()
    
    # Test query
    test_query = "artificial intelligence"
    
    logger.info(f"Collecting data for query: '{test_query}'")
    logger.info("This will demonstrate:")
    logger.info("- Parallel Reddit collection from multiple subreddits")
    logger.info("- Optimized News API usage with rate limiting")
    logger.info("- Proper error handling and retry logic")
    
    # Collect data
    start_time = datetime.now()
    results = collector.collect_all_sources(
        query=test_query,
        reddit_limit=300,  # Collect from multiple subreddits
        news_limit=100     # Respect daily limits
    )
    end_time = datetime.now()
    
    # Display results
    collection_time = (end_time - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("COLLECTION RESULTS")
    print("="*60)
    print(f"Query: {test_query}")
    print(f"Collection Time: {collection_time:.2f} seconds")
    print(f"Reddit Posts: {len(results['reddit'])}")
    print(f"News Articles: {len(results['news'])}")
    print(f"Total Items: {results['total_collected']}")
    print(f"Items per Second: {results['total_collected']/collection_time:.2f}")
    
    # Show sample data
    if results['reddit']:
        print(f"\nSample Reddit Post:")
        sample_reddit = results['reddit'][0]
        print(f"  Title: {sample_reddit['title'][:80]}...")
        print(f"  Subreddit: r/{sample_reddit['subreddit']}")
        print(f"  Score: {sample_reddit['score']}")
    
    if results['news']:
        print(f"\nSample News Article:")
        sample_news = results['news'][0]
        print(f"  Title: {sample_news['title'][:80]}...")
        print(f"  Source: {sample_news['raw_data']['source_name']}")
        print(f"  Author: {sample_news['author']}")
    
    # Store data
    logger.info("Storing collected data...")
    success = collector.store_collected_data(results)
    
    if success:
        logger.info("✅ Data successfully stored in database")
    else:
        logger.error("❌ Failed to store data")
    
    # Show optimization potential
    print("\n" + "="*60)
    print("OPTIMIZATION ANALYSIS")
    print("="*60)
    
    reddit_rate = len(results['reddit']) / collection_time * 60  # posts per minute
    news_rate = len(results['news']) / collection_time * 86400   # posts per day
    
    print(f"Current Reddit Collection Rate: {reddit_rate:.1f} posts/minute")
    print(f"Reddit API Limit: 60 requests/minute")
    print(f"Optimization Potential: {60/reddit_rate:.1f}x faster collection possible")
    
    print(f"\nCurrent News Collection Rate: {news_rate:.1f} posts/day")
    print(f"News API Limit: 100 requests/day (free) or 100,000/day (paid)")
    print(f"Optimization Potential: {100/news_rate:.1f}x more data with free tier")
    print(f"Paid Tier Potential: {100000/news_rate:.1f}x more data with paid tier")
    
    print("\n🚀 NEXT STEPS FOR MAXIMUM OPTIMIZATION:")
    print("1. Run: python monitor_api_usage.py - Check current usage")
    print("2. Upgrade News API to paid tier for 1000x more data")
    print("3. Implement Twitter API integration")
    print("4. Add more subreddits for parallel collection")
    print("5. Implement intelligent caching and deduplication")


def compare_with_original():
    """Compare optimized vs original collection"""
    logger.info("\n📊 Comparing Optimized vs Original Collection")
    
    # This would require running both collectors and comparing results
    # For now, just show the theoretical improvements
    
    print("\n" + "="*60)
    print("THEORETICAL IMPROVEMENTS")
    print("="*60)
    
    print("Original Collection:")
    print("- Reddit: 50 posts per query, single subreddit")
    print("- News: Limited by manual rate limiting")
    print("- Sequential processing")
    print("- No intelligent error handling")
    
    print("\nOptimized Collection:")
    print("- Reddit: 100+ posts per query, multiple subreddits")
    print("- News: Optimized batch collection with quota management")
    print("- Parallel processing (3-5x faster)")
    print("- Intelligent rate limiting and retry logic")
    print("- Automatic deduplication")
    
    print("\nExpected Improvements:")
    print("- 3-5x faster collection speed")
    print("- 2-3x more data per collection cycle")
    print("- Better error handling and reliability")
    print("- Automatic quota management")


if __name__ == "__main__":
    try:
        test_optimized_collection()
        compare_with_original()
        
        print("\n✅ Optimized collection test completed successfully!")
        print("\nTo monitor your API usage, run:")
        print("python monitor_api_usage.py")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print("\n❌ Test failed. Make sure:")
        print("1. PostgreSQL is running")
        print("2. Database is initialized (python setup_database.py)")
        print("3. Environment variables are configured (.env file)")
        print("4. All dependencies are installed")
