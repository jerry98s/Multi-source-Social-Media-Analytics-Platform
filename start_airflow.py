#!/usr/bin/env python3
"""
Start Airflow locally for Social Media Analytics Platform
"""

import os
import sys
import subprocess
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_airflow_environment():
    """Setup Airflow environment variables"""
    os.environ['AIRFLOW_HOME'] = os.getcwd()
    os.environ['AIRFLOW__CORE__EXECUTOR'] = 'LocalExecutor'
    os.environ['AIRFLOW__DATABASE__SQL_ALCHEMY_CONN'] = 'postgresql+psycopg2://postgres:postgres@localhost/social_media_analytics'
    os.environ['AIRFLOW__CORE__FERNET_KEY'] = ''
    os.environ['AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION'] = 'true'
    os.environ['AIRFLOW__CORE__LOAD_EXAMPLES'] = 'false'
    os.environ['AIRFLOW__API__AUTH_BACKENDS'] = 'airflow.api.auth.backend.basic_auth'
    os.environ['AIRFLOW__WEBSERVER__EXPOSE_CONFIG'] = 'true'
    os.environ['AIRFLOW__WEBSERVER__SECRET_KEY'] = 'your-secret-key'
    
    print("✅ Airflow environment configured")

def initialize_airflow_db():
    """Initialize Airflow database"""
    print("🗄️ Initializing Airflow database...")
    try:
        result = subprocess.run(['airflow', 'db', 'init'], 
                              capture_output=True, text=True, check=True)
        print("✅ Airflow database initialized successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Airflow DB init failed: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Airflow not found. Please install: pip install apache-airflow")
        return False

def create_airflow_user():
    """Create Airflow admin user"""
    print("👤 Creating Airflow admin user...")
    try:
        cmd = [
            'airflow', 'users', 'create',
            '--username', 'admin',
            '--firstname', 'Admin',
            '--lastname', 'User',
            '--role', 'Admin',
            '--email', 'admin@example.com',
            '--password', 'admin'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 or "already exists" in result.stderr:
            print("✅ Airflow admin user created")
            return True
        else:
            print(f"⚠️ User creation: {result.stderr}")
            return True  # Continue anyway
    except Exception as e:
        print(f"⚠️ User creation error: {e}")
        return True  # Continue anyway

def start_airflow_webserver():
    """Start Airflow webserver"""
    print("🌐 Starting Airflow webserver on http://localhost:8080")
    print("   Username: admin")
    print("   Password: admin")
    print("   Press Ctrl+C to stop")
    
    try:
        subprocess.run(['airflow', 'webserver', '--port', '8080'], check=True)
    except KeyboardInterrupt:
        print("\n⏹️ Airflow webserver stopped")
    except Exception as e:
        print(f"❌ Webserver error: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 Social Media Analytics Platform - Airflow Setup")
    print("=" * 60)
    
    # Setup environment
    setup_airflow_environment()
    
    # Initialize database
    if not initialize_airflow_db():
        return False
    
    # Create user
    create_airflow_user()
    
    # Start webserver
    start_airflow_webserver()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
