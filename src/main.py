#!/usr/bin/env python3
"""
Main CLI script for the Multi-source Social Media Analytics Platform.
Provides commands to test collectors, run data collection, and manage the platform.
"""

import asyncio
import os
import sys
import click
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.orchestrator import create_orchestrator
from collectors.twitter_collector import create_twitter_collector
from collectors.reddit_collector import create_reddit_collector
from collectors.news_collector import create_news_collector


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Multi-source Social Media Analytics Platform CLI."""
    pass


@cli.command()
@click.option('--source', '-s', type=click.Choice(['twitter', 'reddit', 'news', 'all']), 
              default='all', help='Data source to test')
@click.option('--limit', '-l', type=int, default=10, help='Number of items to collect')
@click.option('--query', '-q', type=str, help='Search query for Twitter and News')
@click.option('--subreddit', type=str, default='technology', help='Subreddit for Reddit collection')
def test_collector(source: str, limit: int, query: Optional[str], subreddit: str):
    """Test individual data collectors."""
    asyncio.run(_test_collector(source, limit, query, subreddit))


async def _test_collector(source: str, limit: int, query: Optional[str], subreddit: str):
    """Test collector functionality."""
    click.echo(f"Testing {source} collector...")
    
    try:
        if source == 'twitter' or source == 'all':
            await _test_twitter_collector(limit, query)
            
        if source == 'reddit' or source == 'all':
            await _test_reddit_collector(limit, subreddit)
            
        if source == 'news' or source == 'all':
            await _test_news_collector(limit, query)
            
    except Exception as e:
        click.echo(f"Error testing collector: {e}", err=True)
        sys.exit(1)


async def _test_twitter_collector(limit: int, query: Optional[str]):
    """Test Twitter collector."""
    try:
        collector = create_twitter_collector()
        click.echo("✓ Twitter collector created successfully")
        
        # Test collection
        if query:
            data = await collector.collect_with_retry(query=query, limit=limit)
        else:
            data = await collector.collect_with_retry(limit=limit)
            
        click.echo(f"✓ Collected {len(data)} tweets from Twitter")
        
        # Show sample data
        if data:
            sample = data[0]
            click.echo(f"Sample tweet: {sample.get('text', 'N/A')[:100]}...")
            
    except Exception as e:
        click.echo(f"✗ Twitter collector test failed: {e}", err=True)


async def _test_reddit_collector(limit: int, subreddit: str):
    """Test Reddit collector."""
    try:
        collector = create_reddit_collector()
        click.echo("✓ Reddit collector created successfully")
        
        # Test collection
        data = await collector.collect_with_retry(subreddit=subreddit, limit=limit)
        click.echo(f"✓ Collected {len(data)} posts from r/{subreddit}")
        
        # Show sample data
        if data:
            sample = data[0]
            click.echo(f"Sample post: {sample.get('title', 'N/A')[:100]}...")
            
    except Exception as e:
        click.echo(f"✗ Reddit collector test failed: {e}", err=True)


async def _test_news_collector(limit: int, query: Optional[str]):
    """Test News collector."""
    try:
        collector = create_news_collector()
        click.echo("✓ News collector created successfully")
        
        # Test collection
        if query:
            data = await collector.collect_with_retry(query=query, limit=limit)
        else:
            data = await collector.collect_with_retry(limit=limit)
            
        click.echo(f"✓ Collected {len(data)} articles from News API")
        
        # Show sample data
        if data:
            sample = data[0]
            click.echo(f"Sample article: {sample.get('title', 'N/A')[:100]}...")
            
    except Exception as e:
        click.echo(f"✗ News collector test failed: {e}", err=True)


@cli.command()
@click.option('--limit', '-l', type=int, default=30, help='Number of items to collect per source')
@click.option('--type', '-t', type=click.Choice(['technology', 'trending']), 
              default='technology', help='Type of data to collect')
def collect_data(limit: int, type: str):
    """Collect data from all available sources using the orchestrator."""
    asyncio.run(_collect_data(limit, type))


async def _collect_data(limit: int, type: str):
    """Collect data using the orchestrator."""
    click.echo(f"Starting data collection ({type})...")
    
    try:
        orchestrator = create_orchestrator()
        click.echo(f"✓ Orchestrator created with {len(orchestrator.collectors)} collectors")
        
        # Check collector health
        health = await orchestrator.health_check_all()
        healthy_collectors = [name for name, status in health.items() if status]
        click.echo(f"✓ {len(healthy_collectors)} healthy collectors: {healthy_collectors}")
        
        if not healthy_collectors:
            click.echo("No healthy collectors available", err=True)
            return
        
        # Collect data
        if type == 'technology':
            data = await orchestrator.collect_technology_data(limit)
        else:
            data = await orchestrator.collect_trending_data(limit)
        
        # Show results
        total_items = 0
        for source, items in data.items():
            click.echo(f"✓ {source}: {len(items)} items collected")
            total_items += len(items)
        
        click.echo(f"✓ Total collection completed: {total_items} items")
        
        # Show stats
        stats = orchestrator.get_collection_stats()
        click.echo(f"Collection stats: {stats}")
        
    except Exception as e:
        click.echo(f"Error during data collection: {e}", err=True)
        sys.exit(1)


@cli.command()
def health_check():
    """Check the health of all collectors."""
    asyncio.run(_health_check())


async def _health_check():
    """Perform health checks on all collectors."""
    click.echo("Performing health checks...")
    
    try:
        orchestrator = create_orchestrator()
        
        # Check individual collector health
        health = await orchestrator.health_check_all()
        
        for collector_name, status in health.items():
            if status:
                click.echo(f"✓ {collector_name}: Healthy")
            else:
                click.echo(f"✗ {collector_name}: Unhealthy")
        
        # Show overall status
        healthy_count = sum(health.values())
        total_count = len(health)
        
        if healthy_count == total_count:
            click.echo(f"✓ All {total_count} collectors are healthy")
        else:
            click.echo(f"⚠ {healthy_count}/{total_count} collectors are healthy")
            
    except Exception as e:
        click.echo(f"Error during health check: {e}", err=True)
        sys.exit(1)


@cli.command()
def status():
    """Show the status of all collectors."""
    asyncio.run(_status())


async def _status():
    """Show detailed collector status."""
    click.echo("Collector Status:")
    click.echo("=" * 50)
    
    try:
        orchestrator = create_orchestrator()
        status_info = orchestrator.get_collector_status()
        
        click.echo(f"Total Collectors: {status_info['total_collectors']}")
        click.echo(f"Collector Names: {', '.join(status_info['collector_names'])}")
        click.echo()
        
        for collector_name, info in status_info['collectors'].items():
            click.echo(f"📊 {collector_name.upper()}")
            click.echo(f"   Class: {info['class']}")
            click.echo(f"   Collection Count: {info['stats']['collection_count']}")
            click.echo(f"   Error Count: {info['stats']['error_count']}")
            click.echo(f"   Success Rate: {info['stats']['success_rate']:.2%}")
            
            if info['rate_limit_info']:
                click.echo(f"   Rate Limit: {info['rate_limit_info']}")
            click.echo()
            
    except Exception as e:
        click.echo(f"Error getting status: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--interval', '-i', type=int, default=15, help='Collection interval in minutes')
def schedule(interval: int):
    """Start scheduled data collection."""
    click.echo(f"Starting scheduled collection every {interval} minutes...")
    click.echo("Press Ctrl+C to stop")
    
    try:
        asyncio.run(_schedule_collection(interval))
    except KeyboardInterrupt:
        click.echo("\nScheduled collection stopped")
    except Exception as e:
        click.echo(f"Error in scheduled collection: {e}", err=True)
        sys.exit(1)


async def _schedule_collection(interval: int):
    """Run scheduled data collection."""
    orchestrator = create_orchestrator()
    await orchestrator.schedule_collection(interval)


@cli.command()
def setup():
    """Setup the platform and check configuration."""
    click.echo("Setting up Multi-source Social Media Analytics Platform...")
    
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
        click.echo("⚠ Missing environment variables:")
        for missing in missing_vars:
            click.echo(f"   {missing}")
        click.echo("\nPlease check your .env file")
    else:
        click.echo("✓ All required environment variables are set")
    
    # Check if we can create collectors
    try:
        orchestrator = create_orchestrator()
        click.echo(f"✓ Successfully initialized {len(orchestrator.collectors)} collectors")
        
        if orchestrator.collectors:
            click.echo("Available collectors:")
            for name in orchestrator.collectors.keys():
                click.echo(f"   - {name}")
        else:
            click.echo("⚠ No collectors available - check your API credentials")
            
    except Exception as e:
        click.echo(f"✗ Error during setup: {e}", err=True)
        sys.exit(1)
    
    click.echo("\nSetup complete! Use 'test-collector' to verify functionality.")


if __name__ == '__main__':
    cli()
