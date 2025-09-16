# 🐛 Debugging Guide: Multi-source Social Media Analytics Platform

This document chronicles all the mistakes encountered during the setup and debugging process, along with their solutions.

## 📋 Table of Contents
1. [Environment Setup Issues](#environment-setup-issues)
2. [Database Connection Problems](#database-connection-problems)
3. [Docker Configuration Issues](#docker-configuration-issues)
4. [Airflow Integration Problems](#airflow-integration-problems)
5. [DAG Execution Failures](#dag-execution-failures)
6. [Import and Module Issues](#import-and-module-issues)
7. [Configuration Mismatches](#configuration-mismatches)
8. [DAG Import Error Resolution](#dag-import-error-resolution)

---

## 🔧 Environment Setup Issues

### ❌ **Mistake 1: Missing Environment Variables**
**Problem**: Environment variables not loaded in Python modules
```python
# In app/collectors.py - Missing dotenv import
import praw
import requests
# Environment variables not loaded!
```

**Solution**: Added dotenv import and load
```python
from dotenv import load_dotenv
load_dotenv()  # Load environment variables
```

**Files Fixed**: `app/collectors.py`, `app/ml_pipeline.py`, `app/processors.py`

---

### ❌ **Mistake 2: PowerShell Command Syntax**
**Problem**: Using `&&` operator in PowerShell (Windows-specific)
```bash
# This fails in PowerShell
python setup_database.py && python test_runner.py
```

**Solution**: Use PowerShell-compatible syntax
```powershell
# Use semicolon or separate commands
python setup_database.py; python test_runner.py
# OR
python setup_database.py
python test_runner.py
```

---

## 🗄️ Database Connection Problems

### ❌ **Mistake 3: Database Credential Mismatch**
**Problem**: Default database credentials didn't match Docker setup
```python
# In app/database.py - Wrong defaults
database=os.getenv('POSTGRES_DB', 'social_analytics'),  # Wrong!
password=os.getenv('POSTGRES_PASSWORD', 'password')     # Wrong!
```

**Solution**: Updated defaults to match Docker Compose
```python
database=os.getenv('POSTGRES_DB', 'social_media_analytics'),  # Correct!
password=os.getenv('POSTGRES_PASSWORD', 'postgres')          # Correct!
```

**Files Fixed**: `app/database.py`

---

### ❌ **Mistake 4: Database Schema Conflicts**
**Problem**: Trying to recreate views with conflicting data types
```sql
-- Error: cannot change data type of view column "source" from data_source to source_type
CREATE VIEW analytics_summary AS ...
```

**Solution**: Drop existing views before recreation
```python
# In setup_database.py
cursor.execute("DROP VIEW IF EXISTS analytics_summary CASCADE;")
cursor.execute("DROP VIEW IF EXISTS sentiment_summary CASCADE;")
# Then recreate schema
```

**Files Fixed**: `setup_database.py`

---

## 🐳 Docker Configuration Issues

### ❌ **Mistake 5: Missing Docker Compose File**
**Problem**: `docker-compose.yml` file was missing entirely
```bash
# Error when trying to start services
docker-compose up -d airflow-webserver
# Error: no configuration file provided: not found
```

**Solution**: Created comprehensive `docker-compose.yml` with all services
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: social_media_analytics
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    # ... rest of configuration
```

**Files Created**: `docker-compose.yml`

---

### ❌ **Mistake 6: Docker Compose Syntax Error**
**Problem**: Typo in docker-compose.yml
```yaml
# Wrong!
inversion: '3.8'  # Should be "version"
```

**Solution**: Fixed the typo
```yaml
# Correct!
version: '3.8'
```

**Files Fixed**: `docker-compose.yml`

---

### ❌ **Mistake 7: Missing Infrastructure Files**
**Problem**: Docker Compose referenced non-existent files
```yaml
volumes:
  - ./infrastructure/init.sql:/docker-entrypoint-initdb.d/init.sql
  - ./infrastructure/prometheus.yml:/etc/prometheus/prometheus.yml
```

**Solution**: Created empty placeholder files
```bash
mkdir -p infrastructure/grafana/datasources
touch infrastructure/init.sql
touch infrastructure/prometheus.yml
```

**Files Created**: `infrastructure/init.sql`, `infrastructure/prometheus.yml`, `infrastructure/grafana/datasources/prometheus.yml`

---

## 🔄 Airflow Integration Problems

### ❌ **Mistake 8: Missing Airflow Database Initialization**
**Problem**: Airflow containers failing to start because database wasn't initialized
```bash
# Error: container is not running
docker exec airflow-webserver airflow db init
```

**Solution**: Added `airflow-init` service to Docker Compose
```yaml
airflow-init:
  build:
    context: .
    dockerfile: Dockerfile.airflow
  command: >
    bash -c "
      airflow db init &&
      airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin
    "
```

**Files Modified**: `docker-compose.yml`

---

### ❌ **Mistake 9: Missing Python Dependencies in Airflow**
**Problem**: Airflow containers didn't have project dependencies
```python
# Error: ModuleNotFoundError: No module named 'praw'
from praw import Reddit
```

**Solution**: Created custom Dockerfile for Airflow
```dockerfile
FROM apache/airflow:2.7.1
USER root
RUN apt-get update && apt-get install -y gcc g++
USER airflow
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY app/ /opt/airflow/app/
ENV PYTHONPATH="/opt/airflow/app:${PYTHONPATH}"
```

**Files Created**: `Dockerfile.airflow`

---

### ❌ **Mistake 10: Wrong Import Paths in Container**
**Problem**: Import paths didn't work inside Docker container
```python
# This failed inside container
from app.database import Database
```

**Solution**: Updated import paths and PYTHONPATH
```python
# Changed to direct import
from database import Database
```

**Files Fixed**: `app/collectors.py`, `app/ml_pipeline.py`, `app/processors.py`

---

## 🚫 DAG Execution Failures

### ❌ **Mistake 11: Incorrect PostgreSQL Connection**
**Problem**: Airflow connection pointed to wrong database
```bash
# Wrong connection details
postgres_default: postgres://postgres:airflow@postgres/airflow
```

**Solution**: Recreated connection with correct details
```bash
# Correct connection
airflow connections add postgres_default \
  --conn-type postgres \
  --conn-host postgres \
  --conn-schema social_media_analytics \
  --conn-login postgres \
  --conn-password postgres \
  --conn-port 5432
```

**Commands Used**: 
- `docker exec airflow-webserver airflow connections delete postgres_default`
- `docker exec airflow-webserver airflow connections add postgres_default ...`

---

### ❌ **Mistake 12: Missing Environment Variables in Airflow**
**Problem**: Airflow containers couldn't connect to PostgreSQL
```python
# Error: connection to server at "localhost" failed
# Because containers were looking for localhost instead of postgres service
```

**Solution**: Added explicit environment variables to all Airflow services
```yaml
environment:
  POSTGRES_HOST: 'postgres'
  POSTGRES_PORT: '5432'
  POSTGRES_DB: 'social_media_analytics'
  POSTGRES_USER: 'postgres'
  POSTGRES_PASSWORD: 'postgres'
```

**Files Fixed**: `docker-compose.yml`

---

## 📦 Import and Module Issues

### ❌ **Mistake 13: Missing Module Files**
**Problem**: Referenced files didn't exist
```bash
# Error: FileNotFoundError: [Errno 2] No such file or directory: 'simple_main.py'
python simple_main.py
```

**Solution**: Created missing files or used existing alternatives
- Created `test_runner.py` instead of `simple_main.py`
- Created `setup_database.py` for database initialization

**Files Created**: `test_runner.py`, `setup_database.py`

---

### ❌ **Mistake 14: Dependency Version Conflicts**
**Problem**: Flask-Limiter version conflict with Airflow
```bash
# Error: ModuleNotFoundError: No module named 'flask_limiter.wrappers'
```

**Solution**: Attempted to downgrade conflicting packages
```bash
pip install Flask-Limiter==3.5.0
pip install apache-airflow==2.6.3
```

**Note**: This was resolved by using the custom Dockerfile approach instead.

---

## ⚙️ Configuration Mismatches

### ❌ **Mistake 15: Database Name Inconsistency**
**Problem**: Different parts of the system used different database names
- Docker Compose: `social_media_analytics`
- Default in code: `social_analytics`
- Airflow connection: `airflow`

**Solution**: Standardized on `social_media_analytics` everywhere
```python
# Updated all references to use consistent naming
POSTGRES_DB: 'social_media_analytics'
```

**Files Fixed**: `app/database.py`, `docker-compose.yml`, Airflow connections

---

### ❌ **Mistake 16: Password Inconsistency**
**Problem**: Different password expectations across components
- Docker Compose: `postgres`
- Default in code: `password`
- Airflow connection: `airflow`

**Solution**: Standardized on `postgres` everywhere
```python
# Updated all references to use consistent password
POSTGRES_PASSWORD: 'postgres'
```

**Files Fixed**: `app/database.py`, `docker-compose.yml`, Airflow connections

---

## 🎯 Key Lessons Learned

### 1. **Environment Consistency**
- Always ensure environment variables are loaded in Python modules
- Use consistent naming across all configuration files
- Verify credentials match between Docker and application code

### 2. **Docker Best Practices**
- Create comprehensive docker-compose.yml with all dependencies
- Use custom Dockerfiles for specialized requirements (like Airflow)
- Set explicit environment variables for container communication

### 3. **Database Setup**
- Initialize databases before starting dependent services
- Handle schema conflicts by dropping existing objects before recreation
- Use consistent connection parameters across all components

### 4. **Airflow Integration**
- Ensure all Python dependencies are available in Airflow containers
- Configure connections properly with correct database details
- Set PYTHONPATH correctly for module imports

### 5. **Debugging Strategy**
- Check container logs for detailed error messages
- Verify connections and configurations step by step
- Test individual components before integrating them

---

## 🛠️ Debugging Commands Reference

### Container Management
```bash
# Check container status
docker-compose ps

# View container logs
docker logs airflow-scheduler --tail 50
docker logs airflow-webserver --tail 50

# Execute commands in containers
docker exec airflow-webserver airflow connections list
docker exec airflow-webserver airflow dags list
```

### Database Operations
```bash
# Connect to PostgreSQL
docker exec -it social-media-postgres psql -U postgres -d social_media_analytics

# Test database connection
python -c "from app.database import Database; db = Database(); print('Connected!')"
```

### Airflow Operations
```bash
# Trigger DAG
docker exec airflow-webserver airflow dags trigger social_media_analytics

# Check DAG status
docker exec airflow-webserver airflow dags state social_media_analytics <execution_date>

# List connections
docker exec airflow-webserver airflow connections list
```

---

## 🚨 DAG Import Error Resolution

### ❌ **Mistake 17: Relative Import Conflicts in Docker**
**Problem**: DAG failed to load in Airflow with import errors
```python
# Error in Docker container
ImportError: attempted relative import with no known parent package
```

**Root Cause**: 
- Local development used relative imports (`from .database import Database`)
- Docker containers execute modules directly, breaking package context
- Airflow DAGs import modules directly, not as packages

**Solution**: Implemented dual import strategy
```python
# Before (Fragile)
from .database import Database

# After (Robust)
try:
    from .database import Database  # Try relative first (for tests)
except ImportError:
    from database import Database   # Fallback to absolute (for Docker)
```

**Files Fixed**: `app/collectors.py`, `app/processors.py`, `app/ml_pipeline.py`

**Prevention**:
- Always test imports in both local and Docker contexts
- Use dual import pattern for internal modules
- Monitor DAG loading errors regularly

**Impact**: 
- ✅ DAG now loads successfully
- ✅ Data collection resumed (+102 new posts)
- ✅ Full pipeline operational

---

## 📊 Final Status

After fixing all these issues:
- ✅ **536 posts collected** (122 Reddit + 414 News)
- ✅ **All data processed** (cleaned and features extracted)
- ✅ **Sentiment analysis working** (490 neutral, 42 positive, 4 negative)
- ✅ **DAG loads and executes successfully**
- ✅ **Platform fully operational**

The debugging process took us through 17 major issues, but each one taught us valuable lessons about system integration, Docker orchestration, data pipeline management, and import compatibility across different execution contexts.
