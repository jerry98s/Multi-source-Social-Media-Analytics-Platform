# 📦 Requirements Documentation

## 📋 **Requirements Files Overview**

This project uses multiple requirements files for different purposes:

### **1. `requirements.txt` - Main Requirements**
- **Purpose**: Core dependencies with exact versions
- **Usage**: `pip install -r requirements.txt`
- **Contains**: Essential packages for the platform

### **2. `requirements_frozen.txt` - Complete Environment**
- **Purpose**: Complete pip freeze output
- **Usage**: `pip install -r requirements_frozen.txt`
- **Contains**: All packages with exact versions (130+ packages)

---

## 🔧 **Core Dependencies**

### **Apache Airflow**
- **apache-airflow==2.6.3** - Workflow orchestration
- **apache-airflow-providers-postgres==5.7.1** - PostgreSQL integration

### **Data Processing**
- **pandas==2.3.2** - Data manipulation and analysis
- **numpy==2.2.6** - Numerical computing

### **Database**
- **psycopg2-binary==2.9.10** - PostgreSQL adapter

### **API Integrations**
- **praw==7.8.1** - Reddit API wrapper
- **newsapi-python==0.2.7** - News API client
- **requests==2.32.5** - HTTP library

### **Machine Learning**
- **scikit-learn==1.7.2** - ML algorithms and tools
- **joblib==1.5.2** - Model persistence

### **Utilities**
- **python-dotenv==1.1.1** - Environment variable management

---

## 📊 **Environment Statistics**

### **Total Packages**: 130+
### **Key Categories**:
- **Airflow Ecosystem**: 20+ packages
- **Flask/Web**: 15+ packages  
- **Data Science**: 10+ packages
- **Database**: 5+ packages
- **Utilities**: 80+ packages

---

## 🚀 **Installation Commands**

### **For Development**
```bash
# Install core dependencies
pip install -r requirements.txt

# Or install complete environment
pip install -r requirements_frozen.txt
```

### **For Production**
```bash
# Use exact versions for reproducibility
pip install -r requirements_frozen.txt
```

### **For Docker**
```dockerfile
# In Dockerfile
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
```

---

## 🔄 **Version Management**

### **When to Update Requirements**
1. **After adding new features** that require new packages
2. **After fixing compatibility issues** with specific versions
3. **Before major releases** to ensure stability
4. **When upgrading Airflow** or other core dependencies

### **How to Update**
```bash
# 1. Update packages
pip install --upgrade package_name

# 2. Freeze new versions
pip freeze > requirements_frozen.txt

# 3. Update requirements.txt with new versions
# 4. Test thoroughly
# 5. Commit changes
```

---

## ⚠️ **Important Notes**

### **Version Compatibility**
- **Airflow 2.6.3**: Compatible with Python 3.8-3.11
- **Pandas 2.3.2**: Requires numpy >= 1.24.0
- **Scikit-learn 1.7.2**: Compatible with numpy 2.2.6

### **Known Issues**
- **Flask-Limiter**: Version 3.13 works with Airflow 2.6.3
- **SQLAlchemy**: Version 1.4.54 (Airflow requirement)
- **Python**: Tested with Python 3.10

---

## 🧪 **Testing Requirements**

### **Test Dependencies**
All test dependencies are included in the main requirements:
- **unittest** (built-in)
- **pytest** (if needed, install separately)
- **mock** (built-in as unittest.mock)

### **Test Installation**
```bash
# Install test environment
pip install -r requirements.txt

# Run tests
python test_runner.py
python tests/test_suite.py
```

---

## 📈 **Performance Considerations**

### **Package Sizes**
- **Total installation**: ~500MB
- **Airflow**: ~200MB
- **Data Science stack**: ~150MB
- **Utilities**: ~150MB

### **Installation Time**
- **Fresh install**: 5-10 minutes
- **Cached install**: 1-2 minutes
- **Docker build**: 2-5 minutes

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Version Conflicts**
```bash
# Check for conflicts
pip check

# Resolve conflicts
pip install --upgrade conflicting-package
```

#### **2. Missing Dependencies**
```bash
# Install missing packages
pip install -r requirements_frozen.txt

# Or install specific package
pip install package_name==version
```

#### **3. Airflow Issues**
```bash
# Reinstall Airflow
pip uninstall apache-airflow
pip install apache-airflow==2.6.3
```

---

## 📚 **References**

- **Airflow Documentation**: https://airflow.apache.org/docs/
- **Pandas Documentation**: https://pandas.pydata.org/docs/
- **Scikit-learn Documentation**: https://scikit-learn.org/stable/
- **PRAW Documentation**: https://praw.readthedocs.io/

---

**Last Updated**: September 16, 2025  
**Environment**: Python 3.10, Windows 10  
**Status**: ✅ **Production Ready**
