"""
API Usage Monitor
Tracks and reports API usage across all platforms
"""

import os
import logging
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class APIUsageMonitor:
    """Monitor API usage and provide optimization recommendations"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'social_media_analytics'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def get_collection_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get collection statistics for the last N hours"""
        query = """
        SELECT 
            source,
            COUNT(*) as total_items,
            COUNT(DISTINCT DATE(collected_at)) as days_active,
            MIN(collected_at) as first_collection,
            MAX(collected_at) as last_collection,
            AVG(CASE WHEN raw_data->>'score' IS NOT NULL 
                THEN (raw_data->>'score')::int 
                ELSE 0 END) as avg_score
        FROM bronze_layer 
        WHERE collected_at >= NOW() - INTERVAL '%s hours'
        GROUP BY source
        ORDER BY total_items DESC;
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (hours,))
                    results = cur.fetchall()
                    
                    stats = {}
                    for row in results:
                        source = row[0]
                        stats[source] = {
                            'total_items': row[1],
                            'days_active': row[2],
                            'first_collection': row[3],
                            'last_collection': row[4],
                            'avg_score': float(row[5]) if row[5] else 0
                        }
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    def get_api_usage_recommendations(self) -> Dict[str, Any]:
        """Generate API usage recommendations"""
        stats = self.get_collection_stats(24)
        recommendations = {
            'reddit': {
                'current_usage': 'Unknown',
                'optimization_potential': 'HIGH',
                'recommendations': []
            },
            'news': {
                'current_usage': 'Unknown',
                'optimization_potential': 'MEDIUM',
                'recommendations': []
            }
        }
        
        # Analyze Reddit usage
        if 'reddit' in stats:
            reddit_stats = stats['reddit']
            items_per_hour = reddit_stats['total_items'] / 24
            
            if items_per_hour < 50:
                recommendations['reddit']['recommendations'].extend([
                    "Increase collection frequency - you're using less than 10% of Reddit's rate limit",
                    "Consider parallel subreddit collection to maximize data diversity",
                    "Implement trending topics collection for better coverage"
                ])
            elif items_per_hour < 200:
                recommendations['reddit']['recommendations'].extend([
                    "Good usage level - consider adding more subreddits",
                    "Implement comment collection for deeper analysis"
                ])
            else:
                recommendations['reddit']['recommendations'].extend([
                    "High usage - monitor for rate limiting",
                    "Consider implementing intelligent caching"
                ])
        
        # Analyze News usage
        if 'news' in stats:
            news_stats = stats['news']
            items_per_hour = news_stats['total_items'] / 24
            
            if items_per_hour < 5:
                recommendations['news']['recommendations'].extend([
                    "Very low News API usage - consider upgrading to paid tier",
                    "Implement multiple query strategies to maximize daily quota",
                    "Add trending topics and keyword expansion"
                ])
            elif items_per_hour < 20:
                recommendations['news']['recommendations'].extend([
                    "Moderate usage - optimize query strategies",
                    "Consider implementing news source diversification"
                ])
            else:
                recommendations['news']['recommendations'].extend([
                    "High usage - consider upgrading to paid tier for more data",
                    "Implement intelligent caching to reduce API calls"
                ])
        
        return recommendations
    
    def generate_optimization_report(self) -> str:
        """Generate a comprehensive optimization report"""
        stats = self.get_collection_stats(24)
        recommendations = self.get_api_usage_recommendations()
        
        report = f"""
# API Usage Optimization Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Current Collection Statistics (Last 24 Hours)
"""
        
        for source, data in stats.items():
            report += f"""
### {source.upper()}
- Total Items: {data['total_items']:,}
- Days Active: {data['days_active']}
- Average Score: {data['avg_score']:.2f}
- Last Collection: {data['last_collection']}
"""
        
        report += "\n## Optimization Recommendations\n"
        
        for source, recs in recommendations.items():
            report += f"\n### {source.upper()}\n"
            for rec in recs['recommendations']:
                report += f"- {rec}\n"
        
        # Add general recommendations
        report += """
## General Optimization Strategies

### Rate Limiting Optimization
- **Reddit**: 60 requests/minute = 3,600/hour = 86,400/day
- **News API**: 100 requests/day (free) or 100,000/day (paid)
- **Twitter**: 1,500 tweets/month (free) or 10,000/month ($100)

### Parallel Processing
- Use concurrent.futures for parallel subreddit collection
- Implement async/await for I/O-bound operations
- Consider using Redis for distributed rate limiting

### Data Quality Improvements
- Implement deduplication based on content similarity
- Add sentiment analysis during collection
- Store engagement metrics for better ML training

### Cost Optimization
- News API: Consider upgrading to paid tier ($449/month for 100k requests/day)
- Twitter API: Evaluate if Basic tier ($100/month) provides sufficient data
- Implement intelligent caching to reduce redundant API calls

### Monitoring & Alerting
- Set up alerts for rate limit approaching
- Monitor API response times and error rates
- Track data quality metrics (completeness, freshness)
"""
        
        return report
    
    def print_current_status(self):
        """Print current API usage status"""
        stats = self.get_collection_stats(24)
        
        print("\n" + "="*60)
        print("API USAGE STATUS (Last 24 Hours)")
        print("="*60)
        
        if not stats:
            print("No data collected in the last 24 hours")
            return
        
        for source, data in stats.items():
            print(f"\n{source.upper()}:")
            print(f"  Items Collected: {data['total_items']:,}")
            print(f"  Items/Hour: {data['total_items']/24:.1f}")
            print(f"  Last Collection: {data['last_collection']}")
            print(f"  Average Score: {data['avg_score']:.2f}")
        
        print("\n" + "="*60)
        print("OPTIMIZATION RECOMMENDATIONS")
        print("="*60)
        
        recommendations = self.get_api_usage_recommendations()
        for source, recs in recommendations.items():
            if recs['recommendations']:
                print(f"\n{source.upper()}:")
                for rec in recs['recommendations']:
                    print(f"  • {rec}")


def main():
    """Main function to run the API usage monitor"""
    monitor = APIUsageMonitor()
    
    print("🔍 API Usage Monitor")
    print("=" * 50)
    
    # Print current status
    monitor.print_current_status()
    
    # Generate and save report
    report = monitor.generate_optimization_report()
    
    # Save report to file
    report_filename = f"api_usage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"\n📊 Detailed report saved to: {report_filename}")
    
    # Print key recommendations
    print("\n🚀 KEY OPTIMIZATION OPPORTUNITIES:")
    print("1. Reddit: You can collect 60x more data per minute")
    print("2. News API: Consider upgrading to paid tier for 1000x more data")
    print("3. Implement parallel collection for 3-5x faster data gathering")
    print("4. Add intelligent caching to reduce redundant API calls")


if __name__ == "__main__":
    main()
