#!/usr/bin/env python3
"""
Unit tests for ML pipeline module
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml_pipeline import SentimentModel, MLPipeline


class TestSentimentModel(unittest.TestCase):
    """Test SentimentModel class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = SentimentModel()
    
    def test_initialization(self):
        """Test SentimentModel initialization"""
        self.assertIsNotNone(self.model.vectorizer)
        self.assertIsNotNone(self.model.model)
        self.assertFalse(self.model.is_trained)
        self.assertEqual(self.model.model_dir, 'models')
    
    @patch('app.ml_pipeline.Database')
    def test_prepare_training_data(self, mock_database):
        """Test training data preparation"""
        # Mock database response
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = [
            ('Title 1', 'Content 1', 'positive'),
            ('Title 2', 'Content 2', 'negative'),
            ('Title 3', 'Content 3', 'neutral'),
            ('Title 4', 'Content 4', 'positive'),
            ('Title 5', 'Content 5', 'negative')
        ]
        mock_database.return_value = mock_db_instance
        
        model = SentimentModel()
        model.db = mock_db_instance
        
        texts, labels = model.prepare_training_data(mock_db_instance)
        
        self.assertEqual(len(texts), 5)
        self.assertEqual(len(labels), 5)
        self.assertEqual(texts[0], 'Title 1 Content 1')
        self.assertEqual(labels[0], 'positive')
    
    @patch('app.ml_pipeline.Database')
    def test_prepare_training_data_empty(self, mock_database):
        """Test training data preparation with empty result"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = []
        mock_database.return_value = mock_db_instance
        
        model = SentimentModel()
        model.db = mock_db_instance
        
        texts, labels = model.prepare_training_data(mock_db_instance)
        
        self.assertEqual(len(texts), 0)
        self.assertEqual(len(labels), 0)
    
    @patch('app.ml_pipeline.Database')
    def test_prepare_training_data_error(self, mock_database):
        """Test training data preparation with error"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("Database error")
        mock_database.return_value = mock_db_instance
        
        model = SentimentModel()
        model.db = mock_db_instance
        
        texts, labels = model.prepare_training_data(mock_db_instance)
        
        self.assertEqual(len(texts), 0)
        self.assertEqual(len(labels), 0)
    
    def test_train_insufficient_data(self):
        """Test training with insufficient data"""
        texts = ['short'] * 5  # Less than 20 samples
        labels = ['positive'] * 5
        
        result = self.model.train(texts, labels)
        
        self.assertEqual(result['status'], 'insufficient_data')
        self.assertEqual(result['accuracy'], 0.0)
    
    def test_train_success(self):
        """Test successful training"""
        # Create sample training data
        texts = [
            'This is great and amazing!' * 5,
            'This is terrible and awful!' * 5,
            'This is just normal text.' * 5,
            'I love this so much!' * 5,
            'I hate this completely!' * 5,
            'This is okay I guess.' * 5,
            'Fantastic and wonderful!' * 5,
            'Disgusting and horrible!' * 5,
            'Pretty good overall.' * 5,
            'Really bad experience.' * 5,
            'Excellent work done!' * 5,
            'Poor quality product.' * 5,
            'Average performance.' * 5,
            'Outstanding results!' * 5,
            'Disappointing outcome.' * 5,
            'Satisfactory service.' * 5,
            'Brilliant idea!' * 5,
            'Pathetic attempt.' * 5,
            'Decent enough.' * 5,
            'Perfect solution!' * 5
        ]
        labels = ['positive', 'negative', 'neutral'] * 6 + ['positive', 'negative']
        
        result = self.model.train(texts, labels)
        
        self.assertEqual(result['status'], 'success')
        self.assertGreater(result['accuracy'], 0.0)
        self.assertLessEqual(result['accuracy'], 1.0)
        self.assertEqual(result['training_samples'], 20)
        self.assertIn('classification_report', result)
        self.assertTrue(self.model.is_trained)
    
    def test_train_error(self):
        """Test training with error"""
        # Create invalid data that will cause an error
        texts = ['valid text'] * 25
        labels = ['invalid_label'] * 25  # Invalid labels
        
        result = self.model.train(texts, labels)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('error', result)
    
    def test_predict_not_trained(self):
        """Test prediction without training"""
        prediction, confidence = self.model.predict("This is a test")
        
        self.assertEqual(prediction, 'neutral')
        self.assertEqual(confidence, 0.0)
    
    def test_predict_trained(self):
        """Test prediction after training"""
        # Train the model first
        texts = ['This is great!'] * 25
        labels = ['positive'] * 25
        self.model.train(texts, labels)
        
        prediction, confidence = self.model.predict("This is great!")
        
        self.assertIn(prediction, ['positive', 'negative', 'neutral'])
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_predict_error(self):
        """Test prediction with error"""
        # Train the model first
        texts = ['This is great!'] * 25
        labels = ['positive'] * 25
        self.model.train(texts, labels)
        
        # Mock vectorizer to cause error
        with patch.object(self.model.vectorizer, 'transform', side_effect=Exception("Vectorizer error")):
            prediction, confidence = self.model.predict("This is great!")
        
        self.assertEqual(prediction, 'neutral')
        self.assertEqual(confidence, 0.0)
    
    def test_save_model(self):
        """Test model saving"""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        self.model.model_dir = temp_dir
        
        try:
            # Train the model first
            texts = ['This is great!'] * 25
            labels = ['positive'] * 25
            self.model.train(texts, labels)
            
            # Save the model
            self.model.save_model()
            
            # Check if file was created
            model_file = os.path.join(temp_dir, 'sentiment_model.pkl')
            self.assertTrue(os.path.exists(model_file))
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
    
    def test_load_model_not_found(self):
        """Test loading non-existent model"""
        temp_dir = tempfile.mkdtemp()
        self.model.model_dir = temp_dir
        
        try:
            result = self.model.load_model()
            self.assertFalse(result)
        finally:
            shutil.rmtree(temp_dir)
    
    def test_load_model_success(self):
        """Test successful model loading"""
        temp_dir = tempfile.mkdtemp()
        self.model.model_dir = temp_dir
        
        try:
            # Train and save model
            texts = ['This is great!'] * 15 + ['This is terrible!'] * 15
            labels = ['positive'] * 15 + ['negative'] * 15
            self.model.train(texts, labels)
            self.model.save_model()
            
            # Create new model and load
            new_model = SentimentModel()
            new_model.model_dir = temp_dir
            result = new_model.load_model()
            
            self.assertTrue(result)
            self.assertTrue(new_model.is_trained)
            
        finally:
            shutil.rmtree(temp_dir)
    
    @patch('app.ml_pipeline.Database')
    def test_save_model_info(self, mock_database):
        """Test saving model info to database"""
        mock_db_instance = Mock()
        mock_database.return_value = mock_db_instance
        
        model = SentimentModel()
        model.db = mock_db_instance
        
        model.save_model_info(0.85, 100)
        
        # Check that database operations were called
        self.assertEqual(mock_db_instance.execute_query.call_count, 2)
        
        # Check the insert query
        calls = mock_db_instance.execute_query.call_args_list
        insert_call = calls[1]  # Second call should be the insert
        self.assertIn('INSERT INTO ml_models', insert_call[0][0])


class TestMLPipeline(unittest.TestCase):
    """Test MLPipeline class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.pipeline = MLPipeline()
    
    @patch('app.ml_pipeline.Database')
    def test_initialization(self, mock_database):
        """Test MLPipeline initialization"""
        pipeline = MLPipeline()
        mock_database.assert_called_once()
        self.assertIsNotNone(pipeline.sentiment_model)
    
    @patch('app.ml_pipeline.Database')
    def test_train_sentiment_model_no_data(self, mock_database):
        """Test training sentiment model with no data"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = []
        mock_database.return_value = mock_db_instance
        
        pipeline = MLPipeline()
        pipeline.db = mock_db_instance
        
        result = pipeline.train_sentiment_model()
        
        self.assertEqual(result['status'], 'no_data')
        self.assertIn('message', result)
    
    @patch('app.ml_pipeline.Database')
    def test_train_sentiment_model_success(self, mock_database):
        """Test successful sentiment model training"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = [
            ('Title 1', 'Content 1', 'positive'),
            ('Title 2', 'Content 2', 'negative'),
            ('Title 3', 'Content 3', 'neutral')
        ] * 10  # 30 samples total
        mock_database.return_value = mock_db_instance
        
        pipeline = MLPipeline()
        pipeline.db = mock_db_instance
        
        result = pipeline.train_sentiment_model()
        
        self.assertEqual(result['status'], 'success')
        self.assertIn('accuracy', result)
        self.assertIn('training_samples', result)
        self.assertIn('test_samples', result)
    
    @patch('app.ml_pipeline.Database')
    def test_predict_new_data_no_model(self, mock_database):
        """Test prediction with no trained model"""
        mock_db_instance = Mock()
        mock_database.return_value = mock_db_instance
        
        pipeline = MLPipeline()
        pipeline.db = mock_db_instance
        
        # Mock load_model to return False
        pipeline.sentiment_model.load_model = Mock(return_value=False)
        
        result = pipeline.predict_new_data()
        
        self.assertEqual(result['status'], 'no_model')
        self.assertIn('message', result)
    
    @patch('app.ml_pipeline.Database')
    def test_predict_new_data_success(self, mock_database):
        """Test successful prediction on new data"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.return_value = [
            (1, 'Test Title', 'Test content'),
            (2, 'Another Title', 'Another content')
        ]
        mock_database.return_value = mock_db_instance
        
        pipeline = MLPipeline()
        pipeline.db = mock_db_instance
        
        # Mock load_model to return True
        pipeline.sentiment_model.load_model = Mock(return_value=True)
        pipeline.sentiment_model.predict = Mock(return_value=('positive', 0.8))
        
        result = pipeline.predict_new_data(limit=10)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['predictions_made'], 2)
    
    @patch('app.ml_pipeline.Database')
    def test_get_analytics(self, mock_database):
        """Test analytics generation"""
        mock_db_instance = Mock()
        
        # Mock different query results
        def side_effect(query, params=None):
            if 'sentiment_label' in query:
                return [('positive', 10), ('negative', 5), ('neutral', 15)]
            elif 'engagement_score' in query:
                return [('Post 1', 5.5, 'positive'), ('Post 2', 4.2, 'negative')]
            elif 'source' in query and 'COUNT' in query:
                return [('reddit', 20), ('news', 10)]
            return []
        
        mock_db_instance.execute_query.side_effect = side_effect
        mock_database.return_value = mock_db_instance
        
        pipeline = MLPipeline()
        pipeline.db = mock_db_instance
        
        analytics = pipeline.get_analytics()
        
        self.assertIn('sentiment_distribution', analytics)
        self.assertIn('top_engaging_posts', analytics)
        self.assertIn('source_statistics', analytics)
        self.assertIn('total_posts', analytics)
        self.assertEqual(analytics['total_posts'], 30)
    
    @patch('app.ml_pipeline.Database')
    def test_get_analytics_error(self, mock_database):
        """Test analytics generation with error"""
        mock_db_instance = Mock()
        mock_db_instance.execute_query.side_effect = Exception("Database error")
        mock_database.return_value = mock_db_instance
        
        pipeline = MLPipeline()
        pipeline.db = mock_db_instance
        
        analytics = pipeline.get_analytics()
        
        self.assertIn('error', analytics)
    
    def test_close(self):
        """Test close method"""
        mock_db = Mock()
        pipeline = MLPipeline()
        pipeline.db = mock_db
        
        pipeline.close()
        mock_db.close.assert_called_once()


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    @patch('app.ml_pipeline.MLPipeline')
    def test_train_ml_model_function(self, mock_pipeline):
        """Test train_ml_model utility function"""
        from app.ml_pipeline import train_ml_model
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.train_sentiment_model.return_value = {
            'status': 'success',
            'accuracy': 0.85
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        result = train_ml_model()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['accuracy'], 0.85)
        mock_pipeline_instance.train_sentiment_model.assert_called_once()
        mock_pipeline_instance.close.assert_called_once()
    
    @patch('app.ml_pipeline.MLPipeline')
    def test_predict_sentiment_function(self, mock_pipeline):
        """Test predict_sentiment utility function"""
        from app.ml_pipeline import predict_sentiment
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.predict_new_data.return_value = {
            'status': 'success',
            'predictions_made': 5
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        result = predict_sentiment()
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['predictions_made'], 5)
        mock_pipeline_instance.predict_new_data.assert_called_once()
        mock_pipeline_instance.close.assert_called_once()
    
    @patch('app.ml_pipeline.MLPipeline')
    def test_generate_analytics_function(self, mock_pipeline):
        """Test generate_analytics utility function"""
        from app.ml_pipeline import generate_analytics
        
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.get_analytics.return_value = {
            'sentiment_distribution': {'positive': 10, 'negative': 5},
            'total_posts': 15
        }
        mock_pipeline.return_value = mock_pipeline_instance
        
        result = generate_analytics()
        
        self.assertEqual(result['total_posts'], 15)
        self.assertIn('sentiment_distribution', result)
        mock_pipeline_instance.get_analytics.assert_called_once()
        mock_pipeline_instance.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
