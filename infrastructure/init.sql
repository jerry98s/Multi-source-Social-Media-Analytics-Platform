-- Initialize Airflow database
-- This file is used by docker-compose to initialize the Airflow database

-- Create Airflow database if it doesn't exist
SELECT 'CREATE DATABASE airflow_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow_db')\gexec

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO postgres;
