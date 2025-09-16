#!/usr/bin/env python3
"""
Test runner for Social Media Analytics Platform
Tests all components and provides a simple interface
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test all module imports"""
    print("🔍 Testing module imports...")
    
    try:
        from app.collectors import RedditCollector, NewsCollector, DataCollector
        print("✅ Collectors module - OK")
    except Exception as e:
        print(f"❌ Collectors module - FAILED: {e}")
        return False
    
    try:
        from app.database import Database
        print("✅ Database module - OK")
    except Exception as e:
        print(f"❌ Database module - FAILED: {e}")
        return False
    
    try:
        from app.processors import DataCleaner, FeatureExtractor
        print("✅ Processors module - OK")
    except Exception as e:
        print(f"❌ Processors module - FAILED: {e}")
        return False
    
    try:
        from app.ml_pipeline import SentimentModel, MLPipeline
        print("✅ ML Pipeline module - OK")
    except Exception as e:
        print(f"❌ ML Pipeline module - FAILED: {e}")
        return False
    
    return True


def test_collectors():
    """Test collectors functionality"""
    print("\n🔍 Testing collectors...")
    
    try:
        from app.collectors import RedditCollector, NewsCollector
        
        # Test Reddit collector initialization
        reddit = RedditCollector()
        print("✅ RedditCollector initialization - OK")
        
        # Test News collector initialization
        news = NewsCollector()
        print("✅ NewsCollector initialization - OK")
        
        # Test collection (will fail with placeholder API keys, but that's expected)
        print("Testing collection (expecting API auth failures with placeholder keys)...")
        
        reddit_posts = reddit.collect("test", limit=1)
        print(f"✅ Reddit collection test - Collected {len(reddit_posts)} posts")
        
        news_articles = news.collect("test", limit=1)
        print(f"✅ News collection test - Collected {len(news_articles)} articles")
        
        return True
        
    except Exception as e:
        print(f"❌ Collectors test - FAILED: {e}")
        return False


def test_database():
    """Test database functionality"""
    print("\n🔍 Testing database...")
    
    try:
        from app.database import Database
        
        # Test database initialization (will fail if PostgreSQL not running)
        try:
            db = Database()
            print("✅ Database connection - OK")
            
            # Test basic operations
            stats = db.get_stats()
            print(f"✅ Database stats - {stats}")
            
            db.close()
            return True
            
        except Exception as e:
            print(f"⚠️ Database connection - FAILED (expected if PostgreSQL not running): {e}")
            return False
            
    except Exception as e:
        print(f"❌ Database test - FAILED: {e}")
        return False


def test_processors():
    """Test data processors"""
    print("\n🔍 Testing processors...")
    
    try:
        from app.processors import DataCleaner, FeatureExtractor
        
        # Test DataCleaner
        cleaner = DataCleaner()
        print("✅ DataCleaner initialization - OK")
        
        # Test text cleaning
        test_text = "  This is a test!!!  "
        cleaned = cleaner.clean_text(test_text)
        print(f"✅ Text cleaning - '{test_text}' -> '{cleaned}'")
        
        # Test FeatureExtractor
        extractor = FeatureExtractor()
        print("✅ FeatureExtractor initialization - OK")
        
        # Test sentiment analysis
        sentiment_label, sentiment_score = extractor.analyze_sentiment("This is great!")
        print(f"✅ Sentiment analysis - 'This is great!' -> {sentiment_label} ({sentiment_score})")
        
        # Test feature extraction
        features = extractor.extract_text_features("Hello #world @user!")
        print(f"✅ Feature extraction - {features}")
        
        cleaner.close()
        extractor.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Processors test - FAILED: {e}")
        return False


def test_ml_pipeline():
    """Test ML pipeline"""
    print("\n🔍 Testing ML pipeline...")
    
    try:
        from app.ml_pipeline import SentimentModel, MLPipeline
        
        # Test SentimentModel
        model = SentimentModel()
        print("✅ SentimentModel initialization - OK")
        
        # Test prediction (without training)
        prediction, confidence = model.predict("This is a test")
        print(f"✅ Sentiment prediction - 'This is a test' -> {prediction} ({confidence})")
        
        # Test MLPipeline
        pipeline = MLPipeline()
        print("✅ MLPipeline initialization - OK")
        
        pipeline.close()
        
        return True
        
    except Exception as e:
        print(f"❌ ML Pipeline test - FAILED: {e}")
        return False


def test_environment():
    """Test environment configuration"""
    print("\n🔍 Testing environment...")
    
    required_vars = [
        'REDDIT_CLIENT_ID',
        'REDDIT_CLIENT_SECRET',
        'REDDIT_USER_AGENT',
        'NEWS_API_KEY'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var} - Set (length: {len(value)})")
        else:
            print(f"❌ {var} - Not set")
            all_set = False
    
    return all_set


def main():
    """Main test function"""
    print("=" * 60)
    print("🚀 Social Media Analytics Platform - Test Runner")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Environment Config", test_environment),
        ("Collectors", test_collectors),
        ("Database", test_database),
        ("Processors", test_processors),
        ("ML Pipeline", test_ml_pipeline),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} - CRASHED: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} - {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Platform is ready to use.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
