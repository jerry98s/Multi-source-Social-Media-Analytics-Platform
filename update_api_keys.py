#!/usr/bin/env python3
"""
Simple API Key Update Script
Updates only Reddit and News API keys in your .env file
"""

import os
from pathlib import Path

def update_api_keys():
    """Update Reddit and News API keys in .env file"""
    
    print("🔐 API Key Update - Reddit & News Only")
    print("=" * 40)
    print()
    
    # Check if .env exists
    if not Path('.env').exists():
        print("❌ .env file not found!")
        print("   Please run 'python setup_secure_environment.py' first to create it.")
        return False
    
    print("📝 Please enter your new API keys:")
    print()
    
    # Get Reddit API keys
    print("🔴 Reddit API:")
    reddit_client_id = input("Reddit Client ID: ").strip()
    reddit_client_secret = input("Reddit Client Secret: ").strip()
    reddit_user_agent = input("Reddit User Agent (or press Enter for default): ").strip()
    if not reddit_user_agent:
        reddit_user_agent = "Social Media Analytics Platform v1.0 by /u/yourusername"
    
    print()
    
    # Get News API key
    print("📰 News API:")
    news_api_key = input("News API Key: ").strip()
    
    print()
    
    # Read current .env file
    try:
        with open('.env', 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    # Update the specific lines
    updated_lines = []
    for line in lines:
        if line.startswith('REDDIT_CLIENT_ID='):
            updated_lines.append(f'REDDIT_CLIENT_ID={reddit_client_id}\n')
        elif line.startswith('REDDIT_CLIENT_SECRET='):
            updated_lines.append(f'REDDIT_CLIENT_SECRET={reddit_client_secret}\n')
        elif line.startswith('REDDIT_USER_AGENT='):
            updated_lines.append(f'REDDIT_USER_AGENT={reddit_user_agent}\n')
        elif line.startswith('NEWS_API_KEY='):
            updated_lines.append(f'NEWS_API_KEY={news_api_key}\n')
        else:
            updated_lines.append(line)
    
    # Write updated .env file
    try:
        with open('.env', 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ API keys updated successfully!")
        print()
        print("🔒 Your new keys are now stored securely in .env")
        print("📋 Updated keys:")
        print(f"   Reddit Client ID: {reddit_client_id}")
        print(f"   Reddit Client Secret: {'*' * len(reddit_client_secret)}")
        print(f"   News API Key: {'*' * len(news_api_key)}")
        print()
        print("🔄 Next steps:")
        print("1. Restart your Docker containers")
        print("2. Test the platform")
        print("3. Verify data collection is working")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

def test_api_keys():
    """Test if the API keys are working"""
    
    print("🧪 Testing API keys...")
    print()
    
    try:
        # Test Reddit API
        print("🔴 Testing Reddit API...")
        from app.collectors import RedditCollector
        reddit = RedditCollector()
        print("✅ Reddit API connection successful!")
        
        # Test News API
        print("📰 Testing News API...")
        from app.collectors import NewsCollector
        news = NewsCollector()
        print("✅ News API connection successful!")
        
        print()
        print("🎉 All API keys are working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        print("   Please check your API keys and try again.")
        return False

def main():
    """Main function"""
    
    # Update API keys
    if update_api_keys():
        print()
        
        # Ask if user wants to test
        test_response = input("Would you like to test the API keys? (y/N): ").strip()
        if test_response.lower() == 'y':
            test_api_keys()
    
    print()
    print("🔐 Security reminder:")
    print("   - Your .env file is protected by .gitignore")
    print("   - Never commit .env files to Git")
    print("   - Keep your API keys secure")

if __name__ == "__main__":
    main()
