"""
Machine Learning Pipeline
Simple sentiment analysis and model training
"""

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from datetime import datetime
import logging
from typing import Dict, List, Any, Tuple
try:
    from .database import Database
except ImportError:
    from database import Database

logger = logging.getLogger(__name__)


class SentimentModel:
    """Simple sentiment analysis model"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.model = LogisticRegression(random_state=42, max_iter=1000)
        self.is_trained = False
        self.model_dir = 'models'
        
        # Ensure models directory exists
        os.makedirs(self.model_dir, exist_ok=True)
    
    def prepare_training_data(self, db: Database) -> Tuple[List[str], List[str]]:
        """Prepare training data from database"""
        query = """
        SELECT cp.title, cp.content, pf.sentiment_label
        FROM clean_posts cp
        JOIN post_features pf ON cp.id = pf.clean_id
        WHERE cp.title IS NOT NULL 
        AND cp.content IS NOT NULL
        AND pf.sentiment_label IS NOT NULL
        AND LENGTH(cp.title || ' ' || cp.content) > 10
        """
        
        try:
            result = db.execute_query(query)
            
            texts = []
            labels = []
            
            for row in result:
                title, content, sentiment_label = row
                combined_text = f"{title} {content}".strip()
                
                if len(combined_text) > 10:  # Minimum text length
                    texts.append(combined_text)
                    labels.append(sentiment_label)
            
            logger.info(f"Prepared {len(texts)} training samples")
            return texts, labels
            
        except Exception as e:
            logger.error(f"Failed to prepare training data: {e}")
            return [], []
    
    def train(self, texts: List[str], labels: List[str]) -> Dict[str, Any]:
        """Train the sentiment model"""
        try:
            if len(texts) < 20:
                logger.warning("Insufficient training data")
                return {'status': 'insufficient_data', 'accuracy': 0.0}
            
            # Vectorize texts
            X = self.vectorizer.fit_transform(texts)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Get classification report
            report = classification_report(y_test, y_pred, output_dict=True)
            
            self.is_trained = True
            
            # Save model
            self.save_model()
            
            # Save model info to database
            self.save_model_info(accuracy, len(texts))
            
            logger.info(f"Model trained with accuracy: {accuracy:.3f}")
            
            return {
                'status': 'success',
                'accuracy': accuracy,
                'classification_report': report,
                'training_samples': len(texts),
                'test_samples': len(y_test)
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def predict(self, text: str) -> Tuple[str, float]:
        """Predict sentiment for a single text"""
        try:
            if not self.is_trained:
                return 'neutral', 0.0
            
            X = self.vectorizer.transform([text])
            prediction = self.model.predict(X)[0]
            probability = np.max(self.model.predict_proba(X))
            
            return prediction, probability
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return 'neutral', 0.0
    
    def save_model(self):
        """Save the trained model"""
        try:
            model_data = {
                'vectorizer': self.vectorizer,
                'model': self.model,
                'is_trained': self.is_trained,
                'created_at': datetime.now().isoformat()
            }
            
            filepath = os.path.join(self.model_dir, 'sentiment_model.pkl')
            joblib.dump(model_data, filepath)
            logger.info(f"Model saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def load_model(self) -> bool:
        """Load a trained model"""
        try:
            filepath = os.path.join(self.model_dir, 'sentiment_model.pkl')
            
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found: {filepath}")
                return False
            
            model_data = joblib.load(filepath)
            self.vectorizer = model_data['vectorizer']
            self.model = model_data['model']
            self.is_trained = model_data['is_trained']
            
            logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def save_model_info(self, accuracy: float, training_count: int):
        """Save model information to database"""
        try:
            db = Database()
            
            # Deactivate previous models
            db.execute_query("UPDATE ml_models SET is_active = FALSE WHERE name = 'sentiment_model'")
            
            # Insert new model info
            query = """
            INSERT INTO ml_models (name, version, model_type, accuracy, training_data_count, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            version = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            db.execute_query(query, (
                'sentiment_model',
                version,
                'logistic_regression',
                accuracy,
                training_count,
                True
            ))
            
            db.close()
            logger.info("Model info saved to database")
            
        except Exception as e:
            logger.error(f"Failed to save model info: {e}")


class MLPipeline:
    """Main ML pipeline orchestrator"""
    
    def __init__(self):
        self.db = Database()
        self.sentiment_model = SentimentModel()
    
    def train_sentiment_model(self) -> Dict[str, Any]:
        """Train sentiment analysis model"""
        logger.info("Starting sentiment model training")
        
        # Prepare training data
        texts, labels = self.sentiment_model.prepare_training_data(self.db)
        
        if not texts:
            return {'status': 'no_data', 'message': 'No training data available'}
        
        # Train model
        results = self.sentiment_model.train(texts, labels)
        
        return results
    
    def predict_new_data(self, limit: int = 1000) -> Dict[str, Any]:
        """Apply trained model to predict sentiment for new data"""
        if not self.sentiment_model.load_model():
            return {'status': 'no_model', 'message': 'No trained model available'}
        
        # Get data without sentiment predictions
        query = """
        SELECT cp.id, cp.title, cp.content
        FROM clean_posts cp
        LEFT JOIN post_features pf ON cp.id = pf.clean_id
        WHERE pf.sentiment_label IS NULL
        AND cp.title IS NOT NULL
        AND cp.content IS NOT NULL
        LIMIT %s
        """
        
        try:
            result = self.db.execute_query(query, (limit,))
            predictions_made = 0
            
            for row in result:
                clean_id, title, content = row
                combined_text = f"{title} {content}".strip()
                
                if len(combined_text) > 10:
                    sentiment_label, confidence = self.sentiment_model.predict(combined_text)
                    
                    # Update the post_features table
                    update_query = """
                    UPDATE post_features 
                    SET sentiment_label = %s, sentiment_score = %s
                    WHERE clean_id = %s
                    """
                    
                    score = confidence if sentiment_label == 'positive' else -confidence if sentiment_label == 'negative' else 0.0
                    
                    self.db.execute_query(update_query, (sentiment_label, score, clean_id))
                    predictions_made += 1
            
            logger.info(f"Made predictions for {predictions_made} records")
            return {'status': 'success', 'predictions_made': predictions_made}
            
        except Exception as e:
            logger.error(f"Prediction pipeline failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics and insights from processed data"""
        try:
            # Sentiment distribution
            sentiment_query = """
            SELECT sentiment_label, COUNT(*) as count
            FROM post_features
            WHERE sentiment_label IS NOT NULL
            GROUP BY sentiment_label
            """
            sentiment_dist = dict(self.db.execute_query(sentiment_query))
            
            # Top engaging posts
            engaging_query = """
            SELECT cp.title, pf.engagement_score, pf.sentiment_label
            FROM clean_posts cp
            JOIN post_features pf ON cp.id = pf.clean_id
            WHERE pf.engagement_score > 0
            ORDER BY pf.engagement_score DESC
            LIMIT 10
            """
            top_posts = self.db.execute_query(engaging_query)
            
            # Source statistics
            source_query = """
            SELECT source, COUNT(*) as count
            FROM clean_posts
            GROUP BY source
            """
            source_stats = dict(self.db.execute_query(source_query))
            
            return {
                'sentiment_distribution': sentiment_dist,
                'top_engaging_posts': top_posts,
                'source_statistics': source_stats,
                'total_posts': sum(source_stats.values())
            }
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close database connection"""
        self.db.close()


# Utility functions for Airflow
def train_ml_model() -> Dict[str, Any]:
    """Function to be called by Airflow DAG"""
    pipeline = MLPipeline()
    try:
        return pipeline.train_sentiment_model()
    finally:
        pipeline.close()


def predict_sentiment() -> Dict[str, Any]:
    """Function to be called by Airflow DAG"""
    pipeline = MLPipeline()
    try:
        return pipeline.predict_new_data()
    finally:
        pipeline.close()


def generate_analytics() -> Dict[str, Any]:
    """Function to be called by Airflow DAG"""
    pipeline = MLPipeline()
    try:
        return pipeline.get_analytics()
    finally:
        pipeline.close()