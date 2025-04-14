from datetime import datetime, timedelta
from typing import Dict, Any, List
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import tensorflow as tf
from app.ml.models import MLDataStore, MLModel
from app.ml.config import MLConfig
from app.models.historical_metrics import HistoricalMetrics
from app.models.time_series_metrics import TimeSeriesMetrics

class MLService:
    """Service for handling ML predictions and model management."""
    
    def __init__(self):
        self.data_store = MLDataStore()
        self.time_series = TimeSeriesMetrics()
        self.config = MLConfig()
        
        # Load or initialize models
        self.recovery_model = self._load_or_create_model('recovery')
        self.nutrition_model = self._load_or_create_model('nutrition')
        self.activity_model = self._load_or_create_model('activity')
        
        # Load or create scalers
        self.feature_scaler = self._load_or_create_scaler('feature')
        self.target_scaler = self._load_or_create_scaler('target')
    
    def _load_or_create_model(self, model_type: str) -> MLModel:
        """Load an existing model or create a new one."""
        model_path = getattr(self.config, f'{model_type.upper()}_MODEL_PATH')
        try:
            model = tf.keras.models.load_model(model_path)
            print(f"Loaded {model_type} model from {model_path}")
        except:
            print(f"Creating new {model_type} model")
            model = self._create_model(model_type)
        return model
    
    def _create_model(self, model_type: str) -> tf.keras.Model:
        """Create a new model based on type."""
        if model_type == 'recovery':
            return self._create_recovery_model()
        elif model_type == 'nutrition':
            return self._create_nutrition_model()
        elif model_type == 'activity':
            return self._create_activity_model()
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_recovery_model(self) -> tf.keras.Model:
        """Create a model for recovery prediction."""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(len(self.config.RECOVERY_FEATURES),)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model
    
    def _create_nutrition_model(self) -> tf.keras.Model:
        """Create a model for nutrition recommendations."""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(len(self.config.NUTRITION_FEATURES),)),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(len(self.config.NUTRITION_TARGETS))
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def _create_activity_model(self) -> tf.keras.Model:
        """Create a model for activity classification."""
        model = tf.keras.Sequential([
            tf.keras.layers.Conv1D(64, 3, activation='relu', input_shape=(self.config.WINDOW_SIZE, len(self.config.ACTIVITY_FEATURES))),
            tf.keras.layers.MaxPooling1D(2),
            tf.keras.layers.Conv1D(32, 3, activation='relu'),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(5, activation='softmax')  # 5 activity types
        ])
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return model
    
    def _load_or_create_scaler(self, scaler_type: str) -> StandardScaler:
        """Load an existing scaler or create a new one."""
        scaler_path = getattr(self.config, f'{scaler_type.upper()}_SCALER_PATH')
        try:
            scaler = joblib.load(scaler_path)
            print(f"Loaded {scaler_type} scaler from {scaler_path}")
        except:
            print(f"Creating new {scaler_type} scaler")
            scaler = StandardScaler()
        return scaler
    
    def predict_recovery(self, user_id: int) -> Dict[str, Any]:
        """Predict recovery status based on recent health data."""
        # Get recent health data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=self.config.WINDOW_SIZE)
        
        health_data = self.time_series.get_metrics(
            user_id=user_id,
            metric_type='health_metrics',
            start_time=start_date,
            end_time=end_date
        )
        
        if not health_data:
            return {'error': 'Insufficient health data'}
        
        # Prepare features
        features = np.array([
            [d['data'][f] for f in self.config.RECOVERY_FEATURES]
            for d in health_data
        ])
        
        # Scale features
        features = self.feature_scaler.transform(features)
        
        # Make prediction
        prediction = self.recovery_model.predict(features)
        
        # Store prediction
        self.data_store.store_prediction(
            user_id=user_id,
            model_type='recovery',
            prediction={
                'recovery_score': float(prediction[-1][0]),
                'confidence': float(np.max(prediction[-1])),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'recovery_score': float(prediction[-1][0]),
            'confidence': float(np.max(prediction[-1])),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_nutrition_recommendations(self, user_id: int) -> Dict[str, Any]:
        """Get personalized nutrition recommendations."""
        # Get user metrics
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        metrics = HistoricalMetrics.get_user_metrics(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not metrics:
            return {'error': 'Insufficient user data'}
        
        # Prepare features
        features = np.array([
            [m.value for m in metrics if m.metric_type in self.config.NUTRITION_FEATURES]
        ])
        
        # Scale features
        features = self.feature_scaler.transform(features)
        
        # Make prediction
        prediction = self.nutrition_model.predict(features)
        
        # Store prediction
        self.data_store.store_prediction(
            user_id=user_id,
            model_type='nutrition',
            prediction={
                'recommendations': {
                    'daily_calories': float(prediction[0][0]),
                    'protein_percentage': float(prediction[0][1]),
                    'carbs_percentage': float(prediction[0][2]),
                    'fat_percentage': float(prediction[0][3])
                },
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'recommendations': {
                'daily_calories': float(prediction[0][0]),
                'protein_percentage': float(prediction[0][1]),
                'carbs_percentage': float(prediction[0][2]),
                'fat_percentage': float(prediction[0][3])
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def classify_activity(self, user_id: int, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify physical activity based on sensor data."""
        # Prepare features
        features = np.array([
            [sensor_data[f] for f in self.config.ACTIVITY_FEATURES]
        ])
        
        # Reshape for CNN input
        features = features.reshape(1, self.config.WINDOW_SIZE, len(self.config.ACTIVITY_FEATURES))
        
        # Make prediction
        prediction = self.activity_model.predict(features)
        
        # Get activity type
        activity_types = ['walking', 'running', 'cycling', 'swimming', 'resting']
        activity_type = activity_types[np.argmax(prediction)]
        
        # Store prediction
        self.data_store.store_prediction(
            user_id=user_id,
            model_type='activity',
            prediction={
                'activity_type': activity_type,
                'confidence': float(np.max(prediction)),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'activity_type': activity_type,
            'confidence': float(np.max(prediction)),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def train_models(self):
        """Train all ML models with latest data."""
        # Get training data
        training_data = self.data_store.get_training_data('health_metrics')
        
        if not training_data:
            print("No training data available")
            return
        
        # Train recovery model
        self._train_recovery_model(training_data)
        
        # Train nutrition model
        self._train_nutrition_model(training_data)
        
        # Train activity model
        self._train_activity_model(training_data)
        
        # Save models and scalers
        self._save_models()
        self._save_scalers()
    
    def _train_recovery_model(self, training_data: List[Dict]):
        """Train the recovery prediction model."""
        # Prepare features and targets
        X = np.array([
            [d['data'][f] for f in self.config.RECOVERY_FEATURES]
            for d in training_data
        ])
        y = np.array([d['data'][self.config.RECOVERY_TARGET] for d in training_data])
        
        # Scale features and targets
        X = self.feature_scaler.fit_transform(X)
        y = self.target_scaler.fit_transform(y.reshape(-1, 1))
        
        # Train model
        self.recovery_model.fit(
            X, y,
            batch_size=self.config.BATCH_SIZE,
            epochs=self.config.EPOCHS,
            validation_split=0.2
        )
    
    def _train_nutrition_model(self, training_data: List[Dict]):
        """Train the nutrition recommendation model."""
        # Prepare features and targets
        X = np.array([
            [d['data'][f] for f in self.config.NUTRITION_FEATURES]
            for d in training_data
        ])
        y = np.array([
            [d['data'][t] for t in self.config.NUTRITION_TARGETS]
            for d in training_data
        ])
        
        # Scale features and targets
        X = self.feature_scaler.fit_transform(X)
        y = self.target_scaler.fit_transform(y)
        
        # Train model
        self.nutrition_model.fit(
            X, y,
            batch_size=self.config.BATCH_SIZE,
            epochs=self.config.EPOCHS,
            validation_split=0.2
        )
    
    def _train_activity_model(self, training_data: List[Dict]):
        """Train the activity classification model."""
        # Prepare features and targets
        X = np.array([
            [d['data'][f] for f in self.config.ACTIVITY_FEATURES]
            for d in training_data
        ])
        y = np.array([d['data'][self.config.ACTIVITY_TARGET] for d in training_data])
        
        # Reshape for CNN input
        X = X.reshape(-1, self.config.WINDOW_SIZE, len(self.config.ACTIVITY_FEATURES))
        
        # One-hot encode targets
        y = tf.keras.utils.to_categorical(y, num_classes=5)
        
        # Scale features
        X = self.feature_scaler.fit_transform(X.reshape(-1, len(self.config.ACTIVITY_FEATURES)))
        X = X.reshape(-1, self.config.WINDOW_SIZE, len(self.config.ACTIVITY_FEATURES))
        
        # Train model
        self.activity_model.fit(
            X, y,
            batch_size=self.config.BATCH_SIZE,
            epochs=self.config.EPOCHS,
            validation_split=0.2
        )
    
    def _save_models(self):
        """Save trained models to disk."""
        self.recovery_model.save(self.config.RECOVERY_MODEL_PATH)
        self.nutrition_model.save(self.config.NUTRITION_MODEL_PATH)
        self.activity_model.save(self.config.ACTIVITY_MODEL_PATH)
    
    def _save_scalers(self):
        """Save feature and target scalers to disk."""
        joblib.dump(self.feature_scaler, self.config.FEATURE_SCALER_PATH)
        joblib.dump(self.target_scaler, self.config.TARGET_SCALER_PATH) 