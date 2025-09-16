#!/usr/bin/env python3
"""
Comprehensive test suite for Social Media Analytics Platform
"""

import unittest
import sys
import os
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all test modules
from test_collectors import TestRedditCollector, TestNewsCollector, TestDataCollector, TestUtilityFunctions as TestCollectorUtils
from test_database import TestDatabase, TestDatabaseIntegration
from test_processors import TestDataCleaner, TestFeatureExtractor, TestUtilityFunctions as TestProcessorUtils
from test_ml_pipeline import TestSentimentModel, TestMLPipeline, TestUtilityFunctions as TestMLUtils


def create_test_suite():
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Collectors tests
    suite.addTest(unittest.makeSuite(TestRedditCollector))
    suite.addTest(unittest.makeSuite(TestNewsCollector))
    suite.addTest(unittest.makeSuite(TestDataCollector))
    suite.addTest(unittest.makeSuite(TestCollectorUtils))
    
    # Database tests
    suite.addTest(unittest.makeSuite(TestDatabase))
    suite.addTest(unittest.makeSuite(TestDatabaseIntegration))
    
    # Processors tests
    suite.addTest(unittest.makeSuite(TestDataCleaner))
    suite.addTest(unittest.makeSuite(TestFeatureExtractor))
    suite.addTest(unittest.makeSuite(TestProcessorUtils))
    
    # ML Pipeline tests
    suite.addTest(unittest.makeSuite(TestSentimentModel))
    suite.addTest(unittest.makeSuite(TestMLPipeline))
    suite.addTest(unittest.makeSuite(TestMLUtils))
    
    return suite


def run_tests(verbose=False):
    """Run all tests with detailed output"""
    print("=" * 80)
    print("🧪 SOCIAL MEDIA ANALYTICS PLATFORM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Create test suite
    suite = create_test_suite()
    
    # Run tests
    runner = unittest.TextTestRunner(
        verbosity=2 if verbose else 1,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    passed = total_tests - failures - errors - skipped
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    if skipped > 0:
        print(f"⏭️ Skipped: {skipped}")
    
    success_rate = (passed / total_tests) * 100 if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failures > 0:
        print(f"\n❌ FAILURES ({failures}):")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print(f"\n💥 ERRORS ({errors}):")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print("\n" + "=" * 80)
    if failures == 0 and errors == 0:
        print("🎉 ALL TESTS PASSED! Platform is fully tested and ready.")
    else:
        print("⚠️ Some tests failed. Review the output above for details.")
    print("=" * 80)
    
    return result.wasSuccessful()


def run_module_tests(module_name, verbose=False):
    """Run tests for a specific module"""
    print(f"🧪 Running tests for {module_name} module...")
    print("=" * 60)
    
    suite = unittest.TestSuite()
    
    if module_name.lower() == 'collectors':
        suite.addTest(unittest.makeSuite(TestRedditCollector))
        suite.addTest(unittest.makeSuite(TestNewsCollector))
        suite.addTest(unittest.makeSuite(TestDataCollector))
        suite.addTest(unittest.makeSuite(TestCollectorUtils))
    elif module_name.lower() == 'database':
        suite.addTest(unittest.makeSuite(TestDatabase))
        suite.addTest(unittest.makeSuite(TestDatabaseIntegration))
    elif module_name.lower() == 'processors':
        suite.addTest(unittest.makeSuite(TestDataCleaner))
        suite.addTest(unittest.makeSuite(TestFeatureExtractor))
        suite.addTest(unittest.makeSuite(TestProcessorUtils))
    elif module_name.lower() == 'ml_pipeline':
        suite.addTest(unittest.makeSuite(TestSentimentModel))
        suite.addTest(unittest.makeSuite(TestMLPipeline))
        suite.addTest(unittest.makeSuite(TestMLUtils))
    else:
        print(f"❌ Unknown module: {module_name}")
        print("Available modules: collectors, database, processors, ml_pipeline")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Social Media Analytics Platform tests')
    parser.add_argument('--module', '-m', help='Run tests for specific module')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.module:
        success = run_module_tests(args.module, args.verbose)
    else:
        success = run_tests(args.verbose)
    
    sys.exit(0 if success else 1)
