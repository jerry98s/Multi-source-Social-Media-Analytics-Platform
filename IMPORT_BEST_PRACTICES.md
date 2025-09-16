# 📋 Import Best Practices - Quick Reference

## 🚨 **The Problem We Solved**

**Error**: `ImportError: attempted relative import with no known parent package`  
**Context**: DAG failed to load in Docker/Airflow but worked locally  
**Root Cause**: Relative imports break in container execution context  

---

## ✅ **The Solution: Dual Import Pattern**

### **For All Internal Modules**
```python
# ✅ CORRECT - Works everywhere
try:
    from .database import Database
except ImportError:
    from database import Database
```

### **❌ AVOID These Patterns**
```python
# ❌ WRONG - Breaks in Docker
from .database import Database

# ❌ WRONG - Breaks in tests  
from database import Database
```

---

## 🎯 **Quick Checklist**

### **Before Committing Code**
- [ ] Internal modules use dual import pattern
- [ ] External packages use absolute imports
- [ ] DAG files use absolute imports with sys.path
- [ ] Tested in both local and Docker contexts

### **When Adding New Modules**
1. **Create module** with dual imports
2. **Test locally** (relative imports work)
3. **Test in Docker** (absolute imports work)
4. **Update DAG** if needed

---

## 🔧 **Implementation Guide**

### **Step 1: Update Module Imports**
```python
# Replace this
from .database import Database

# With this
try:
    from .database import Database
except ImportError:
    from database import Database
```

### **Step 2: Test Both Contexts**
```bash
# Test 1: Local (relative imports)
python -m pytest tests/

# Test 2: Docker (absolute imports)
docker exec container python -c "from app.module import Class"
```

### **Step 3: Verify DAG Loading**
```bash
# Check DAG loads without errors
docker exec airflow-webserver airflow dags list-import-errors
```

---

## 📚 **Pattern Examples**

### **Internal Module Pattern**
```python
# app/collectors.py
try:
    from .database import Database
except ImportError:
    from database import Database

# External packages - always absolute
import pandas as pd
import numpy as np
```

### **DAG File Pattern**
```python
# dags/social_analytics_dag.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app'))

# Always absolute imports in DAGs
from collectors import collect_social_media_data
from processors import clean_raw_data
```

### **Test File Pattern**
```python
# tests/test_collectors.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Always absolute imports in tests
from app.collectors import RedditCollector
```

---

## 🚨 **Warning Signs**

### **Red Flags**
- Import errors in Docker but not locally
- `ModuleNotFoundError` in containers
- DAG fails to load with import errors
- Tests pass but DAG fails

### **Detection Commands**
```bash
# Check for import errors
docker exec airflow-webserver airflow dags list-import-errors

# Test module imports
docker exec airflow-webserver python -c "from app.module import Class"
```

---

## 🏆 **Success Metrics**

### **Before Fix**
- ❌ DAG loading: Failed
- ❌ Data collection: Stopped
- ❌ Error rate: 100%

### **After Fix**
- ✅ DAG loading: Success
- ✅ Data collection: +102 posts
- ✅ Error rate: 0%

---

## 📖 **Related Documentation**

- **Detailed Guide**: `DAG_IMPORT_ERROR_TROUBLESHOOTING.md`
- **Debugging Guide**: `DEBUGGING_GUIDE.md` (Mistake #17)
- **Status Report**: `DAG_STATUS_REPORT.md`

---

**Remember**: Always use dual imports for internal modules to ensure compatibility across all execution contexts! 🎯
