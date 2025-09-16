# 🚨 Quick Troubleshooting Reference

## 🔍 Common Issues & Quick Fixes

### 1. **DAG Failed - Database Connection Error**
```bash
# Check Airflow connections
docker exec airflow-webserver airflow connections list

# Fix PostgreSQL connection
docker exec airflow-webserver airflow connections delete postgres_default
docker exec airflow-webserver airflow connections add postgres_default \
  --conn-type postgres \
  --conn-host postgres \
  --conn-schema social_media_analytics \
  --conn-login postgres \
  --conn-password postgres \
  --conn-port 5432
```

### 2. **Container Won't Start**
```bash
# Check container status
docker-compose ps

# View logs
docker logs airflow-scheduler --tail 20
docker logs airflow-webserver --tail 20

# Restart services
docker-compose down
docker-compose up -d
```

### 3. **Database Connection Failed**
```bash
# Check if PostgreSQL is running
docker exec social-media-postgres pg_isready

# Test connection
python -c "from app.database import Database; db = Database(); print('Connected!')"

# Check environment variables
docker exec airflow-webserver env | grep POSTGRES
```

### 4. **Import Errors in Airflow**
```bash
# Check if app directory is mounted
docker exec airflow-webserver ls -la /opt/airflow/app/

# Check PYTHONPATH
docker exec airflow-webserver echo $PYTHONPATH

# Rebuild Airflow image
docker-compose build airflow-webserver
docker-compose up -d airflow-webserver
```

### 5. **No Data Collected**
```bash
# Check if collectors have API keys
docker exec airflow-webserver env | grep -E "(REDDIT|NEWS)_API"

# Test collectors manually
python -c "from app.collectors import RedditCollector; r = RedditCollector(); print('Reddit OK')"

# Check DAG execution logs
docker logs airflow-scheduler | grep "collect_social_media_data"
```

### 6. **Environment Variables Not Loading**
```bash
# Check .env file exists
ls -la .env

# Verify .env is mounted in container
docker exec airflow-webserver ls -la /opt/airflow/.env

# Test environment loading
docker exec airflow-webserver python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('REDDIT_CLIENT_ID'))"
```

## 🔧 Diagnostic Commands

### Container Health Check
```bash
# All containers status
docker-compose ps

# Individual container health
docker exec airflow-webserver curl -f http://localhost:8080/health
docker exec social-media-postgres pg_isready -U postgres
docker exec redis redis-cli ping
```

### Database Diagnostics
```bash
# Connect to database
docker exec -it social-media-postgres psql -U postgres -d social_media_analytics

# Check tables
\dt

# Check data
SELECT COUNT(*) FROM raw_posts;
SELECT COUNT(*) FROM clean_posts;
SELECT COUNT(*) FROM post_features;
```

### Airflow Diagnostics
```bash
# List DAGs
docker exec airflow-webserver airflow dags list

# Check DAG runs
docker exec airflow-webserver airflow dags list-runs -d social_media_analytics

# Check task states
docker exec airflow-webserver airflow tasks states-for-dag-run social_media_analytics <run_id>
```

## 🚀 Quick Recovery Procedures

### Complete Reset
```bash
# Stop everything
docker-compose down -v

# Remove all containers and volumes
docker system prune -a -f

# Rebuild and start
docker-compose up -d --build
```

### Database Reset
```bash
# Stop services
docker-compose stop postgres

# Remove database volume
docker volume rm multi-source-social-media-analytics-platform_postgres-data

# Restart with fresh database
docker-compose up -d postgres
python setup_database.py
```

### Airflow Reset
```bash
# Stop Airflow services
docker-compose stop airflow-webserver airflow-scheduler airflow-init

# Remove Airflow database volume
docker volume rm multi-source-social-media-analytics-platform_postgres-data

# Restart Airflow
docker-compose up -d airflow-init
docker-compose up -d airflow-webserver airflow-scheduler
```

## 📊 Data Verification Commands

### Check Data Collection
```bash
# Quick data summary
python check_data.py

# Detailed analysis
python analyze_data.py

# Manual data check
python -c "
from app.database import Database
db = Database()
result = db.execute_query('SELECT COUNT(*) FROM raw_posts')
print(f'Raw posts: {result[0][0]}')
"
```

### Verify Pipeline Steps
```bash
# Check each step
python -c "
from app.collectors import DataCollector
from app.processors import DataCleaner, FeatureExtractor
from app.ml_pipeline import MLPipeline

print('✅ All modules import successfully')
"
```

## 🎯 Success Indicators

### ✅ Platform is Working When:
- All containers show "Up" status: `docker-compose ps`
- Airflow web UI accessible: http://localhost:8080
- DAG shows "success" state in Airflow UI
- Data collection shows > 0 posts: `python check_data.py`
- All three tables have data: raw_posts, clean_posts, post_features

### ❌ Platform Needs Attention When:
- Any container shows "Exit" status
- Airflow web UI returns connection error
- DAG shows "failed" state
- Data collection shows 0 posts
- Database connection errors in logs

## 📞 Emergency Contacts

### If All Else Fails:
1. **Check the full debugging guide**: `DEBUGGING_GUIDE.md`
2. **Review container logs**: `docker logs <container_name>`
3. **Verify environment setup**: `python test_runner.py`
4. **Reset and rebuild**: Follow "Complete Reset" procedure above

### Key Files to Check:
- `docker-compose.yml` - Service configuration
- `.env` - Environment variables
- `app/database.py` - Database connection settings
- `dags/social_analytics_dag.py` - DAG definition
- `Dockerfile.airflow` - Airflow container setup
