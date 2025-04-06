import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MLConfig:
    """Configuration for ML-related settings."""
    
    # Model paths
    MODEL_DIR = os.getenv('ML_MODEL_DIR', 'models')
    RECOVERY_MODEL_PATH = os.path.join(MODEL_DIR, 'recovery_model.h5')
    NUTRITION_MODEL_PATH = os.path.join(MODEL_DIR, 'nutrition_model.h5')
    ACTIVITY_MODEL_PATH = os.path.join(MODEL_DIR, 'activity_model.h5')
    
    # Training settings
    TRAINING_DATA_DIR = os.getenv('TRAINING_DATA_DIR', 'training_data')
    BATCH_SIZE = int(os.getenv('ML_BATCH_SIZE', 32))
    EPOCHS = int(os.getenv('ML_EPOCHS', 100))
    LEARNING_RATE = float(os.getenv('ML_LEARNING_RATE', 0.001))
    
    # Feature settings
    FEATURE_SCALER_PATH = os.path.join(MODEL_DIR, 'feature_scaler.pkl')
    TARGET_SCALER_PATH = os.path.join(MODEL_DIR, 'target_scaler.pkl')
    
    # Recovery model settings
    RECOVERY_FEATURES = [
        'heart_rate',
        'sleep_duration',
        'stress_level',
        'activity_level'
    ]
    RECOVERY_TARGET = 'recovery_score'
    
    # Nutrition model settings
    NUTRITION_FEATURES = [
        'calories_burned',
        'activity_duration',
        'recovery_score',
        'weight',
        'height',
        'age',
        'gender'
    ]
    NUTRITION_TARGETS = [
        'daily_calories',
        'protein_percentage',
        'carbs_percentage',
        'fat_percentage'
    ]
    
    # Activity model settings
    ACTIVITY_FEATURES = [
        'acceleration_x',
        'acceleration_y',
        'acceleration_z',
        'gyroscope_x',
        'gyroscope_y',
        'gyroscope_z',
        'heart_rate'
    ]
    ACTIVITY_TARGET = 'activity_type'
    
    # Data processing settings
    WINDOW_SIZE = int(os.getenv('ML_WINDOW_SIZE', 24))  # hours
    STRIDE = int(os.getenv('ML_STRIDE', 1))  # hours
    MIN_SAMPLES = int(os.getenv('ML_MIN_SAMPLES', 100))
    
    # Database settings
    POSTGRES_URI = os.getenv('POSTGRES_URI', 'postgresql://postgres:postgres@localhost:5432/health_diet_plan')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'health_ml')
    
    # Collection names
    HEALTH_DATA_COLLECTION = 'health_data'
    PREDICTIONS_COLLECTION = 'predictions'
    TRAINING_DATA_COLLECTION = 'training_data'
    
    # API settings
    API_RATE_LIMIT = int(os.getenv('ML_API_RATE_LIMIT', 100))
    API_RATE_LIMIT_WINDOW = int(os.getenv('ML_API_RATE_LIMIT_WINDOW', 3600))  # seconds
    API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'your-secret-key')
    API_TOKEN_EXPIRY = int(os.getenv('API_TOKEN_EXPIRY', 3600))  # seconds
    API_TOKEN_ALGORITHM = os.getenv('API_TOKEN_ALGORITHM', 'HS256')
    
    # Logging settings
    LOG_LEVEL = os.getenv('ML_LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('ML_LOG_FILE', 'ml.log')
    
    @classmethod
    def create_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.MODEL_DIR, exist_ok=True)
        os.makedirs(cls.TRAINING_DATA_DIR, exist_ok=True)
        
    @classmethod
    def validate_config(cls):
        """Validate configuration settings."""
        # Check required environment variables
        required_vars = [
            'POSTGRES_URI',
            'MONGO_URI',
            'MONGO_DB',
            'API_SECRET_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Validate numeric settings
        if cls.BATCH_SIZE <= 0:
            raise ValueError("BATCH_SIZE must be positive")
        if cls.EPOCHS <= 0:
            raise ValueError("EPOCHS must be positive")
        if cls.LEARNING_RATE <= 0:
            raise ValueError("LEARNING_RATE must be positive")
        if cls.WINDOW_SIZE <= 0:
            raise ValueError("WINDOW_SIZE must be positive")
        if cls.STRIDE <= 0:
            raise ValueError("STRIDE must be positive")
        if cls.MIN_SAMPLES <= 0:
            raise ValueError("MIN_SAMPLES must be positive")
        if cls.API_RATE_LIMIT <= 0:
            raise ValueError("API_RATE_LIMIT must be positive")
        if cls.API_RATE_LIMIT_WINDOW <= 0:
            raise ValueError("API_RATE_LIMIT_WINDOW must be positive")
        if cls.API_TOKEN_EXPIRY <= 0:
            raise ValueError("API_TOKEN_EXPIRY must be positive")
        
        # Create directories
        cls.create_directories() 