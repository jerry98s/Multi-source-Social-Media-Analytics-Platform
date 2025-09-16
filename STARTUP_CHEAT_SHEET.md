# 🚀 STARTUP CHEAT SHEET

## ⚡ **5-MINUTE STARTUP**

```powershell
# 1. Navigate to project
cd "C:\Users\User\OneDrive\Documents\Multi-source Social Media Analytics Platform"

# 2. Activate environment
.\venv\Scripts\Activate.ps1

# 3. Start services
docker-compose up -d

# 4. Wait 60 seconds
Start-Sleep -Seconds 60

# 5. Check status
docker-compose ps
python check_data.py
```

## 🔍 **QUICK CHECKS**

```powershell
# All containers running?
docker-compose ps

# Data collected?
python check_data.py

# Airflow working?
# Open: http://localhost:8080 (admin/admin)
```

## 🚨 **IF SOMETHING'S WRONG**

```powershell
# Restart everything
docker-compose down
docker-compose up -d

# Check logs
docker logs airflow-scheduler --tail 20
docker logs airflow-webserver --tail 20
```

## 📊 **CURRENT STATUS**
- **Data**: 327 posts collected
- **Schedule**: Every 2 hours
- **Runtime**: ~15 seconds per run
- **Sources**: Reddit + News APIs

## 🎯 **SUCCESS = ALL GREEN**
- ✅ Containers: Up
- ✅ Data: > 0 posts
- ✅ Airflow: http://localhost:8080
- ✅ DAG: Success state

**That's it! You're ready to go! 🚀**
