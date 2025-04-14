import logging
import os
from logging.handlers import RotatingFileHandler
from app.ml.config import MLConfig

def setup_logger():
    """Setup logger for ML-related operations."""
    # Create logger
    logger = logging.getLogger('ml')
    logger.setLevel(getattr(logging, MLConfig.LOG_LEVEL))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler
    file_handler = RotatingFileHandler(
        MLConfig.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create logger instance
logger = setup_logger()

def log_health_data(user_id: int, data_type: str, data: dict):
    """Log health data storage."""
    logger.info(
        f"Storing health data - User: {user_id}, Type: {data_type}, "
        f"Data: {data}"
    )

def log_prediction(user_id: int, model_type: str, prediction: dict):
    """Log model prediction."""
    logger.info(
        f"Making prediction - User: {user_id}, Model: {model_type}, "
        f"Prediction: {prediction}"
    )

def log_training_data(data_type: str, data: dict):
    """Log training data storage."""
    logger.info(
        f"Storing training data - Type: {data_type}, "
        f"Data: {data}"
    )

def log_model_training(model_type: str, metrics: dict):
    """Log model training metrics."""
    logger.info(
        f"Training model - Type: {model_type}, "
        f"Metrics: {metrics}"
    )

def log_model_evaluation(model_type: str, metrics: dict):
    """Log model evaluation metrics."""
    logger.info(
        f"Evaluating model - Type: {model_type}, "
        f"Metrics: {metrics}"
    )

def log_error(error: Exception, context: str = None):
    """Log error with context."""
    logger.error(
        f"Error occurred{f' in {context}' if context else ''}: {str(error)}",
        exc_info=True
    )

def log_warning(message: str, context: str = None):
    """Log warning with context."""
    logger.warning(
        f"Warning{f' in {context}' if context else ''}: {message}"
    )

def log_info(message: str, context: str = None):
    """Log info message with context."""
    logger.info(
        f"Info{f' in {context}' if context else ''}: {message}"
    )

def log_debug(message: str, context: str = None):
    """Log debug message with context."""
    logger.debug(
        f"Debug{f' in {context}' if context else ''}: {message}"
    ) 