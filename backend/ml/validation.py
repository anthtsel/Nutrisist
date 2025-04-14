from typing import Dict, Any, List
from app.ml.exceptions import ValidationError, InvalidDataError
from app.ml.config import MLConfig
from app.ml.logger import logger

def validate_health_data(data: Dict[str, Any]) -> None:
    """Validate health data structure and values."""
    required_fields = [
        'heart_rate',
        'steps',
        'calories',
        'sleep_duration',
        'stress_level',
        'activity_level'
    ]
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate numeric fields
    numeric_fields = {
        'heart_rate': (0, 300),
        'steps': (0, 100000),
        'calories': (0, 10000),
        'sleep_duration': (0, 24),
        'stress_level': (0, 100),
        'activity_level': (0, 100)
    }
    
    for field, (min_val, max_val) in numeric_fields.items():
        value = data.get(field)
        if not isinstance(value, (int, float)):
            raise ValidationError(f"{field} must be numeric")
        if not min_val <= value <= max_val:
            raise ValidationError(f"{field} must be between {min_val} and {max_val}")

def validate_sensor_data(data: Dict[str, Any]) -> None:
    """Validate sensor data structure and values."""
    required_fields = [
        'acceleration',
        'gyroscope',
        'heart_rate'
    ]
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate acceleration
    acceleration = data.get('acceleration')
    if not isinstance(acceleration, list) or len(acceleration) != 3:
        raise ValidationError("Acceleration must be a list of 3 values")
    if not all(isinstance(x, (int, float)) for x in acceleration):
        raise ValidationError("Acceleration values must be numeric")
    
    # Validate gyroscope
    gyroscope = data.get('gyroscope')
    if not isinstance(gyroscope, list) or len(gyroscope) != 3:
        raise ValidationError("Gyroscope must be a list of 3 values")
    if not all(isinstance(x, (int, float)) for x in gyroscope):
        raise ValidationError("Gyroscope values must be numeric")
    
    # Validate heart rate
    heart_rate = data.get('heart_rate')
    if not isinstance(heart_rate, (int, float)):
        raise ValidationError("Heart rate must be numeric")
    if not 0 <= heart_rate <= 300:
        raise ValidationError("Heart rate must be between 0 and 300")

def validate_training_data(data: List[Dict[str, Any]]) -> None:
    """Validate training data structure and values."""
    if not data:
        raise ValidationError("Training data cannot be empty")
    
    # Check minimum samples
    if len(data) < MLConfig.MIN_SAMPLES:
        raise ValidationError(
            f"Training data must have at least {MLConfig.MIN_SAMPLES} samples"
        )
    
    # Validate each sample
    for i, sample in enumerate(data):
        try:
            validate_health_data(sample)
        except ValidationError as e:
            raise ValidationError(f"Invalid sample at index {i}: {str(e)}")

def validate_model_config(config: Dict[str, Any]) -> None:
    """Validate model configuration."""
    required_fields = [
        'model_type',
        'input_shape',
        'output_shape',
        'architecture'
    ]
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate model type
    valid_types = ['recovery', 'nutrition', 'activity']
    if config['model_type'] not in valid_types:
        raise ValidationError(f"Invalid model type. Must be one of: {', '.join(valid_types)}")
    
    # Validate input shape
    input_shape = config['input_shape']
    if not isinstance(input_shape, tuple) or len(input_shape) != 2:
        raise ValidationError("Input shape must be a tuple of length 2")
    
    # Validate output shape
    output_shape = config['output_shape']
    if not isinstance(output_shape, tuple) or len(output_shape) != 2:
        raise ValidationError("Output shape must be a tuple of length 2")
    
    # Validate architecture
    architecture = config['architecture']
    if not isinstance(architecture, list):
        raise ValidationError("Architecture must be a list")
    if not architecture:
        raise ValidationError("Architecture cannot be empty")

def validate_prediction_request(data: Dict[str, Any]) -> None:
    """Validate prediction request data."""
    required_fields = ['model_type', 'input_data']
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate model type
    valid_types = ['recovery', 'nutrition', 'activity']
    if data['model_type'] not in valid_types:
        raise ValidationError(f"Invalid model type. Must be one of: {', '.join(valid_types)}")
    
    # Validate input data based on model type
    if data['model_type'] == 'recovery':
        validate_health_data(data['input_data'])
    elif data['model_type'] == 'activity':
        validate_sensor_data(data['input_data'])
    elif data['model_type'] == 'nutrition':
        if not isinstance(data['input_data'], dict):
            raise ValidationError("Nutrition input data must be a dictionary")
        required_nutrition_fields = [
            'calories_burned',
            'activity_duration',
            'recovery_score'
        ]
        missing_fields = [
            field for field in required_nutrition_fields
            if field not in data['input_data']
        ]
        if missing_fields:
            raise ValidationError(
                f"Missing required nutrition fields: {', '.join(missing_fields)}"
            )

def validate_api_request(request_data: Dict[str, Any]) -> None:
    """Validate API request data."""
    try:
        # Check request type
        if 'type' not in request_data:
            raise ValidationError("Missing request type")
        
        request_type = request_data['type']
        if request_type == 'prediction':
            validate_prediction_request(request_data)
        elif request_type == 'training':
            validate_training_data(request_data.get('data', []))
        elif request_type == 'health_data':
            validate_health_data(request_data.get('data', {}))
        elif request_type == 'sensor_data':
            validate_sensor_data(request_data.get('data', {}))
        else:
            raise ValidationError(f"Invalid request type: {request_type}")
            
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        raise ValidationError("Invalid request data") 