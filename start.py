#!/usr/bin/env python3
"""
Quick startup script for the Multi-source Social Media Analytics Platform.
This script provides a simple way to test the platform without using the CLI.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append('src')

def print_banner():
    """Print the platform banner."""
    print("=" * 60)
    print("🚀 Multi-source Social Media Analytics Platform")
    print("=" * 60)
    print()

def print_menu():
    """Print the main menu."""
    print("Available options:")
    print("1. Setup and check configuration")
    print("2. Test all collectors")
    print("3. Collect technology data")
    print("4. Health check")
    print("5. Exit")
    print()

async def main():
    """Main function."""
    print_banner()
    
    while True:
        print_menu()
        choice = input("Enter your choice (1-5): ").strip()
        
        try:
            if choice == '1':
                await setup_check()
            elif choice == '2':
                await test_collectors()
            elif choice == '3':
                await collect_technology_data()
            elif choice == '4':
                await health_check()
            elif choice == '5':
                print("Goodbye! 👋")
                break
            else:
                print("Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 60 + "\n")

async def setup_check():
    """Check platform setup."""
    print("🔧 Checking platform setup...")
    
    # Check environment variables
    required_vars = {
        'Twitter API': ['TWITTER_BEARER_TOKEN', 'TWITTER_API_KEY'],
        'Reddit API': ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET'],
        'News API': ['NEWS_API_KEY']
    }
    
    missing_vars = []
    
    for api_name, vars in required_vars.items():
        missing = [var for var in vars if not os.getenv(var)]
        if missing:
            missing_vars.append(f"{api_name}: {', '.join(missing)}")
    
    if missing_vars:
        print("⚠ Missing environment variables:")
        for missing in missing_vars:
            print(f"   {missing}")
        print("\nPlease check your .env file")
    else:
        print("✓ All required environment variables are set")
    
    # Try to create orchestrator
    try:
        from collectors.orchestrator import create_orchestrator
        orchestrator = create_orchestrator()
        print(f"✓ Successfully initialized {len(orchestrator.collectors)} collectors")
        
        if orchestrator.collectors:
            print("Available collectors:")
            for name in orchestrator.collectors.keys():
                print(f"   - {name}")
        else:
            print("⚠ No collectors available - check your API credentials")
            
    except Exception as e:
        print(f"✗ Error during setup: {e}")

async def test_collectors():
    """Test all collectors."""
    print("🧪 Testing all collectors...")
    
    try:
        from collectors.orchestrator import create_orchestrator
        orchestrator = create_orchestrator()
        
        # Check health
        health = await orchestrator.health_check_all()
        healthy_collectors = [name for name, status in health.items() if status]
        
        print(f"✓ {len(healthy_collectors)} healthy collectors: {healthy_collectors}")
        
        if not healthy_collectors:
            print("No healthy collectors available")
            return
        
        # Test collection
        data = await orchestrator.collect_trending_data(limit=15)
        
        for source, items in data.items():
            print(f"✓ {source}: {len(items)} items collected")
            
    except Exception as e:
        print(f"✗ Error testing collectors: {e}")

async def collect_technology_data():
    """Collect technology-related data."""
    print("📊 Collecting technology data...")
    
    try:
        from collectors.orchestrator import create_orchestrator
        orchestrator = create_orchestrator()
        
        # Check health first
        health = await orchestrator.health_check_all()
        healthy_collectors = [name for name, status in health.items() if status]
        
        if not healthy_collectors:
            print("No healthy collectors available")
            return
        
        # Collect data
        data = await orchestrator.collect_technology_data(limit=30)
        
        total_items = 0
        for source, items in data.items():
            print(f"✓ {source}: {len(items)} items collected")
            total_items += len(items)
        
        print(f"✓ Total collection completed: {total_items} items")
        
        # Show sample data
        if data:
            print("\nSample data:")
            for source, items in data.items():
                if items:
                    sample = items[0]
                    if 'title' in sample:
                        print(f"  {source}: {sample['title'][:80]}...")
                    elif 'text' in sample:
                        print(f"  {source}: {sample['text'][:80]}...")
                        
    except Exception as e:
        print(f"✗ Error collecting data: {e}")

async def health_check():
    """Perform health check on all collectors."""
    print("🏥 Performing health check...")
    
    try:
        from collectors.orchestrator import create_orchestrator
        orchestrator = create_orchestrator()
        
        health = await orchestrator.health_check_all()
        
        for collector_name, status in health.items():
            if status:
                print(f"✓ {collector_name}: Healthy")
            else:
                print(f"✗ {collector_name}: Unhealthy")
        
        # Show overall status
        healthy_count = sum(health.values())
        total_count = len(health)
        
        if healthy_count == total_count:
            print(f"✓ All {total_count} collectors are healthy")
        else:
            print(f"⚠ {healthy_count}/{total_count} collectors are healthy")
            
    except Exception as e:
        print(f"✗ Error during health check: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nGoodbye! 👋")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

