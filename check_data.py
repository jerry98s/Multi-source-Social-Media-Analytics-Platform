#!/usr/bin/env python3
"""
Check Social Media Analytics Data
"""

import sys
import os
sys.path.append('app')
from database import Database

def main():
    print('📊 SOCIAL MEDIA ANALYTICS DATA SUMMARY')
    print('=' * 50)
    
    db = Database()
    
    # Raw posts summary
    result = db.execute_query('SELECT COUNT(*) FROM raw_posts')
    print(f'📝 Total Raw Posts: {result[0][0]}')
    
    # Clean posts summary  
    result = db.execute_query('SELECT COUNT(*) FROM clean_posts')
    print(f'🧹 Clean Posts: {result[0][0]}')
    
    # Features summary
    result = db.execute_query('SELECT COUNT(*) FROM post_features')
    print(f'🔍 Features Extracted: {result[0][0]}')
    
    # Source breakdown
    result = db.execute_query('SELECT source, COUNT(*) FROM raw_posts GROUP BY source')
    print(f'\n📈 Data Sources:')
    for row in result:
        print(f'  {row[0]}: {row[1]} posts')
    
    # Sample data from each source
    print(f'\n📋 Sample Data:')
    result = db.execute_query("SELECT source, data->'title' as title, collected_at FROM raw_posts WHERE data->'title' IS NOT NULL LIMIT 3")
    for row in result:
        title = row[1][:50] + '...' if row[1] and len(row[1]) > 50 else row[1]
        print(f'  [{row[0]}] {title} ({row[2]})')
    
    # Check sentiment analysis
    print(f'\n😊 Sentiment Analysis:')
    try:
        result = db.execute_query('SELECT sentiment_score, COUNT(*) FROM post_features GROUP BY sentiment_score')
        for row in result:
            print(f'  Score {row[0]}: {row[1]} posts')
    except Exception as e:
        print(f'  Sentiment data: Available in features table')
    
    # Recent activity
    print(f'\n🕒 Recent Activity:')
    result = db.execute_query('SELECT source, collected_at FROM raw_posts ORDER BY collected_at DESC LIMIT 5')
    for row in result:
        print(f'  [{row[0]}] {row[1]}')

if __name__ == "__main__":
    main()
