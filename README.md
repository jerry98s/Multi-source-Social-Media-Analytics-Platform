# Multi-source Social Media Analytics Platform

A comprehensive data engineering platform that ingests, processes, and analyzes social media data from multiple sources in real-time.

## 🏗️ Architecture Overview

```
Data Sources → Ingestion Layer → Data Lake → Processing Layer → Feature Store → Analytics/ML
```

### Data Flow
1. **Data Sources**: Reddit, News APIs (Twitter collector in development)
2. **Ingestion Layer**: Python collectors with PostgreSQL storage
3. **Data Lake**: Bronze (Raw) → Silver (Cleaned) → Gold (Curated)
4. **Processing**: Data cleaning and feature extraction pipelines
5. **Feature Store**: ML-ready features with PostgreSQL
6. **Analytics**: Sentiment analysis and engagement metrics

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 15+
- Docker & Docker Compose (optional)
- API keys for Reddit and News APIs

### Option 1: Basic Setup (Recommended for first run)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure environment variables
cp env.example .env
# Edit .env with your API keys

# 3. Start PostgreSQL (if not running)
# On Windows: Start PostgreSQL service
# On Linux/Mac: sudo systemctl start postgresql

# 4. Initialize database
python setup_database.py

# 5. Test data collection
python check_data.py
```

### Option 2: Full Platform with Airflow

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure environment variables
cp env.example .env
# Edit .env with your API keys

# 3. Initialize database
python setup_database.py

# 4. Start Airflow
python start_airflow.py

# 5. Access Airflow UI at http://localhost:8080 (admin/admin)
```

## 📁 Project Structure

```
├── app/                          # Core application modules
│   ├── collectors.py             # Data collection (Reddit, News)
│   ├── database.py               # PostgreSQL operations
│   ├── processors.py             # Data cleaning and feature extraction
│   └── ml_pipeline.py            # Machine learning pipeline
├── dags/                         # Airflow DAGs
│   └── social_analytics_dag.py   # Main pipeline orchestration
├── tests/                        # Test suite
│   ├── test_collectors.py        # Data collection tests
│   ├── test_database.py          # Database operation tests
│   ├── test_processors.py       # Data processing tests
│   ├── test_ml_pipeline.py      # ML pipeline tests
│   └── test_suite.py             # Comprehensive test runner
├── sql/                          # Database schema
│   └── schema.sql                # Database schema definition
├── infrastructure/               # Infrastructure configuration
│   ├── init.sql                  # Database initialization
│   ├── prometheus.yml            # Monitoring configuration
│   └── grafana/                  # Grafana dashboards
├── models/                       # Trained ML models
│   └── sentiment_model.pkl       # Sentiment analysis model
├── docker-compose.yml            # Infrastructure orchestration
├── requirements.txt              # Python dependencies
├── env.example                   # Environment variables template
├── setup_database.py            # Database initialization
├── start_airflow.py             # Airflow launcher
├── test_runner.py               # Test execution
├── check_data.py                # Data status checker
└── analyze_data.py              # Data analysis utilities
```

## 🔧 Technology Stack

- **Languages**: Python 3.9+
- **Database**: PostgreSQL 15+
- **Orchestration**: Apache Airflow 2.7+
- **Processing**: pandas, numpy
- **ML**: scikit-learn, joblib
- **APIs**: PRAW (Reddit), News API
- **Infrastructure**: Docker, Docker Compose
- **Monitoring**: Prometheus, Grafana (with Docker)

## 📊 Current Implementation Status

### ✅ Completed Components

#### Data Collection Layer
- **Reddit Collector**: Full PRAW integration for posts and comments
- **News Collector**: News API integration for articles
- **Data Orchestrator**: Coordinates collection from multiple sources

#### Data Processing Pipeline
- **Bronze Layer**: Raw data storage with JSONB
- **Silver Layer**: Cleaned and structured data
- **Gold Layer**: ML-ready features and analytics

#### Machine Learning
- **Sentiment Analysis**: Keyword-based and ML models
- **Feature Engineering**: Text, temporal, and engagement features
- **Model Training**: Logistic regression with scikit-learn

#### Infrastructure
- **Database Schema**: Complete Bronze-Silver-Gold architecture
- **Airflow Integration**: Pipeline orchestration
- **Docker Setup**: Multi-service infrastructure

#### Testing & Quality Assurance
- **Comprehensive Test Suite**: 5 test modules covering all core functionality
- **Unit Tests**: All modules thoroughly tested
- **Integration Tests**: End-to-end pipeline validation
- **Mock Testing**: Proper external dependency handling

### ⚠️ Known Issues

1. **Twitter Collector**: Not yet implemented (Reddit and News only)
2. **Docker Services**: Some infrastructure services may need manual setup
3. **API Rate Limits**: Reddit (60 req/min), News API (100 req/day free tier)

## 🎯 Usage Examples

### Data Collection Test
```bash
python check_data.py
# Shows current data status and collection info
```

### Run Test Suite
```bash
python test_runner.py
# Runs comprehensive test suite
```

### Start Airflow Platform
```bash
python start_airflow.py
# Starts Airflow webserver and scheduler
# Access at http://localhost:8080 (admin/admin)
```

### Analyze Collected Data
```bash
python analyze_data.py
# Performs data analysis on collected social media data
```

## 🧪 Testing

### Quick Test Suite
```bash
# Run main test runner
python test_runner.py

# Run comprehensive test suite
python tests/test_suite.py

# Check current data status
python check_data.py
```

### Individual Module Tests
```bash
# Test specific modules
python -m unittest tests.test_database
python -m unittest tests.test_collectors
python -m unittest tests.test_processors
python -m unittest tests.test_ml_pipeline

# Run with verbose output
python tests/test_suite.py --verbose
```

### Test Coverage
- **Test Files**: 5 comprehensive test modules
- **Coverage**: All core modules tested
- **Status**: ✅ Production Ready

## 📈 Data Pipeline

### Bronze Layer (Raw Data)
- Stores original API responses as JSONB
- Includes metadata: source, external_id, collected_at
- Handles deduplication with unique constraints

### Silver Layer (Cleaned Data)
- Structured data with proper types
- Cleaned text content
- Standardized engagement metrics
- Author and publication information

### Gold Layer (Features)
- ML-ready features
- Sentiment analysis results
- Text statistics (word count, hashtags, mentions)
- Temporal features (hour, day, weekend)
- Engagement scoring

## 🤖 Machine Learning Features

### Sentiment Analysis
- **Keyword-based**: Simple positive/negative word matching
- **ML Model**: Logistic regression with TF-IDF features
- **Training**: Uses collected data for model improvement

### Feature Engineering
- Text length and complexity metrics
- Social media specific features (hashtags, mentions)
- Temporal patterns
- Engagement scoring algorithms

## 🔧 Configuration

### Environment Variables (.env)
```bash
# API Configuration
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_app_name/1.0

NEWS_API_KEY=your_news_api_key

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=social_media_analytics
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Application Settings
LOG_LEVEL=INFO
DEBUG=true
```

### API Keys Required
- **Reddit API**: Client ID, Client Secret, User Agent
- **News API**: API Key (free tier: 100 requests/day)

## 🐳 Docker Services

The platform includes these services:
- **PostgreSQL**: Main database
- **Redis**: Caching layer
- **Kafka**: Message streaming
- **MinIO**: S3-compatible storage
- **Prometheus**: Metrics collection
- **Grafana**: Monitoring dashboards
- **Airflow**: Workflow orchestration
- **Jupyter**: Data exploration

## 📊 Monitoring & Analytics

### Available Metrics
- Data collection rates by source
- Processing pipeline performance
- ML model accuracy and training metrics
- Database statistics and health

### Views and Reports
- Sentiment distribution by source
- Top engaging posts
- Source statistics
- Temporal analysis

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   ```bash
   # Ensure PostgreSQL is running
   # Check connection parameters in .env
   # Run setup.py to initialize database
   ```

2. **API Rate Limits**:
   - Reddit: 60 requests/minute
   - News API: 100 requests/day (free tier)
   - Adjust collection intervals in configuration

3. **Missing Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Airflow Issues**:
   - Ensure PostgreSQL is running
   - Check if ports 8080 and 5432 are available
   - Run `python setup_database.py` to initialize database

## 🔄 Development Roadmap

### Phase 1: Data Collection & Ingestion ✅
- [x] Project structure setup
- [x] Reddit and News API integration
- [x] Basic data storage
- [x] Data collection orchestration

### Phase 2: Data Lake Architecture ✅
- [x] Bronze layer (raw data storage)
- [x] Silver layer (cleaned data)
- [x] Gold layer (curated data)
- [x] Data quality monitoring

### Phase 3: Processing Pipeline ✅
- [x] Data transformation pipelines
- [x] Feature extraction
- [x] Basic aggregation jobs

### Phase 4: ML Feature Store ✅
- [x] Feature engineering
- [x] Sentiment analysis models
- [x] Model training and evaluation

### Phase 5: Analytics & Deployment (In Progress)
- [x] Data analysis utilities (`analyze_data.py`)
- [x] Airflow monitoring and orchestration
- [ ] Real-time monitoring dashboard
- [ ] Production deployment optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the known issues
3. Open a GitHub issue
4. Contact the development team

## 🎉 Getting Started Checklist

- [ ] Install Python 3.9+
- [ ] Install PostgreSQL 15+
- [ ] Copy `env.example` to `.env`
- [ ] Configure API keys in `.env`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Initialize database: `python setup_database.py`
- [ ] Test the platform: `python check_data.py`
- [ ] Start Airflow: `python start_airflow.py`

**Ready to collect and analyze social media data!** 🚀
