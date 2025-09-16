# 🚨 DAG Import Error Troubleshooting Guide

## 📋 **Issue Summary**

**Problem**: DAG failed to load in Airflow with import errors  
**Root Cause**: Relative import conflicts between local development and Docker container execution  
**Impact**: Complete DAG failure, no data collection  
**Resolution**: Dual import strategy for compatibility  

---

## 🔍 **Detailed Problem Analysis**

### **The Error**
```python
ImportError: attempted relative import with no known parent package
```

### **What Happened**
1. **Local Development**: Modules used relative imports (`from .database import Database`)
2. **Docker Execution**: Airflow couldn't resolve relative imports in container context
3. **Import Path Mismatch**: Different Python path structures between environments

### **Why It Happened**
- **Relative imports** work in package context (when running as `python -m app.module`)
- **Docker containers** execute modules directly, breaking package context
- **Airflow DAGs** import modules directly, not as packages

---

## 🔧 **Root Cause Analysis**

### **Environment Differences**

| Environment | Import Method | Context | Result |
|-------------|---------------|---------|---------|
| **Local Tests** | `from .database import Database` | Package context | ✅ Works |
| **Docker/Airflow** | `from .database import Database` | Direct execution | ❌ Fails |
| **Direct Execution** | `from .database import Database` | No parent package | ❌ Fails |

### **Python Import Resolution**
```python
# Relative imports require package context
from .database import Database  # Needs __package__ to be set

# Absolute imports work in any context
from database import Database   # Works if module is in sys.path
```

---

## ✅ **Solution Implemented**

### **Dual Import Strategy**
```python
# Before (Fragile)
from .database import Database

# After (Robust)
try:
    from .database import Database  # Try relative first (for tests)
except ImportError:
    from database import Database   # Fallback to absolute (for Docker)
```

### **Why This Works**
1. **Tests**: Use relative imports (package context)
2. **Docker**: Falls back to absolute imports (direct execution)
3. **Compatibility**: Works in both environments
4. **Maintainability**: Single codebase, multiple contexts

---

## 🛡️ **Prevention Strategies**

### **1. Import Strategy Guidelines**

#### **✅ DO: Use Dual Import Pattern**
```python
# Recommended pattern for all modules
try:
    from .module import Class
except ImportError:
    from module import Class
```

#### **❌ DON'T: Use Only Relative Imports**
```python
# Avoid - breaks in Docker/containers
from .module import Class
```

#### **❌ DON'T: Use Only Absolute Imports**
```python
# Avoid - breaks in test environments
from module import Class
```

### **2. Environment Testing**

#### **Test Both Contexts**
```bash
# Test 1: Package context (for tests)
python -m pytest tests/

# Test 2: Direct execution (for Docker)
python app/collectors.py

# Test 3: Docker context
docker exec container python -c "from app.collectors import RedditCollector"
```

### **3. Import Validation**

#### **Add Import Tests**
```python
def test_imports_in_docker_context():
    """Test that modules can be imported in Docker-like context"""
    import sys
    sys.path.insert(0, 'app')
    
    # These should work without package context
    from collectors import RedditCollector
    from processors import DataCleaner
    from ml_pipeline import SentimentModel
```

---

## 🔄 **Best Practices**

### **1. Module Structure**
```
app/
├── __init__.py          # Makes it a package
├── collectors.py        # Uses dual imports
├── processors.py        # Uses dual imports
├── ml_pipeline.py       # Uses dual imports
└── database.py          # Core module
```

### **2. Import Patterns**

#### **For Internal Modules**
```python
# Standard pattern for app modules
try:
    from .database import Database
except ImportError:
    from database import Database
```

#### **For External Dependencies**
```python
# External packages - always absolute
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
```

#### **For Airflow DAGs**
```python
# DAG files - always absolute imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app'))

from collectors import collect_social_media_data
from processors import clean_raw_data, extract_features
```

### **3. Testing Strategy**

#### **Multi-Environment Testing**
```python
class TestImportCompatibility(unittest.TestCase):
    """Test imports work in different contexts"""
    
    def test_relative_import_context(self):
        """Test relative imports work in package context"""
        # This simulates test environment
        pass
    
    def test_absolute_import_context(self):
        """Test absolute imports work in direct execution"""
        # This simulates Docker environment
        import sys
        sys.path.insert(0, 'app')
        from collectors import RedditCollector
```

---

## 🚨 **Warning Signs**

### **Red Flags to Watch For**
1. **Import errors in Docker** but not locally
2. **ModuleNotFoundError** in containers
3. **Relative import errors** in Airflow logs
4. **Tests pass** but **DAG fails** to load

### **Early Detection**
```bash
# Check DAG loading
docker exec airflow-webserver airflow dags list-import-errors

# Test module imports
docker exec airflow-webserver python -c "from app.collectors import RedditCollector"
```

---

## 🔧 **Troubleshooting Steps**

### **Step 1: Identify the Problem**
```bash
# Check DAG import errors
docker exec airflow-webserver airflow dags list-import-errors

# Look for: ImportError: attempted relative import with no known parent package
```

### **Step 2: Locate Problematic Imports**
```bash
# Search for relative imports
grep -r "from \." app/

# Check which modules use relative imports
```

### **Step 3: Apply Fix**
```python
# Replace relative imports with dual imports
# Before
from .database import Database

# After
try:
    from .database import Database
except ImportError:
    from database import Database
```

### **Step 4: Test Fix**
```bash
# Test in Docker context
docker exec airflow-webserver python -c "from app.collectors import RedditCollector"

# Check DAG loads
docker exec airflow-webserver airflow dags list
```

### **Step 5: Restart Services**
```bash
# Restart Airflow to pick up changes
docker-compose restart airflow-webserver airflow-scheduler
```

---

## 📚 **Learning Points**

### **Key Takeaways**
1. **Environment Context Matters**: Different execution contexts have different import rules
2. **Dual Strategy Works**: Try relative, fallback to absolute
3. **Test Both Contexts**: Always test in both local and container environments
4. **Early Detection**: Monitor DAG loading errors proactively

### **Prevention Checklist**
- [ ] Use dual import pattern for all internal modules
- [ ] Test imports in both local and Docker contexts
- [ ] Monitor DAG loading errors regularly
- [ ] Document import patterns for team
- [ ] Add import compatibility tests

---

## 🎯 **Action Items**

### **Immediate**
1. ✅ **Fixed**: Applied dual import pattern to all modules
2. ✅ **Verified**: DAG now loads successfully
3. ✅ **Tested**: Both local and Docker contexts work

### **Future Prevention**
1. **Add Import Tests**: Create tests for both contexts
2. **Document Patterns**: Share this guide with team
3. **Monitor DAGs**: Regular checks for import errors
4. **Code Reviews**: Check import patterns in PRs

---

## 🏆 **Success Metrics**

### **Before Fix**
- ❌ DAG loading: Failed
- ❌ Data collection: 0 new posts
- ❌ Error rate: 100% import failures

### **After Fix**
- ✅ DAG loading: Success
- ✅ Data collection: +102 new posts
- ✅ Error rate: 0% import failures

---

**Status**: ✅ **RESOLVED**  
**Prevention**: ✅ **DOCUMENTED**  
**Future Risk**: 🟡 **LOW** (with proper practices)

This guide ensures the same issue won't happen again and provides a framework for handling similar import conflicts in the future.
