class MLException(Exception):
    """Base exception for ML-related errors."""
    pass

class ModelTrainingError(MLException):
    """Exception raised when model training fails."""
    pass

class ModelPredictionError(MLException):
    """Exception raised when model prediction fails."""
    pass

class DataProcessingError(MLException):
    """Exception raised when data processing fails."""
    pass

class InvalidDataError(MLException):
    """Exception raised when invalid data is provided."""
    pass

class ModelNotFoundError(MLException):
    """Exception raised when a model is not found."""
    pass

class ModelSaveError(MLException):
    """Exception raised when saving a model fails."""
    pass

class ModelLoadError(MLException):
    """Exception raised when loading a model fails."""
    pass

class DataStoreError(MLException):
    """Exception raised when data storage/retrieval fails."""
    pass

class ConfigurationError(MLException):
    """Exception raised when configuration is invalid."""
    pass

class APIError(MLException):
    """Exception raised when API calls fail."""
    pass

class RateLimitError(APIError):
    """Exception raised when API rate limit is exceeded."""
    pass

class AuthenticationError(APIError):
    """Exception raised when API authentication fails."""
    pass

class ValidationError(MLException):
    """Exception raised when data validation fails."""
    pass

class FeatureExtractionError(MLException):
    """Exception raised when feature extraction fails."""
    pass

class PreprocessingError(MLException):
    """Exception raised when data preprocessing fails."""
    pass

class PostprocessingError(MLException):
    """Exception raised when data postprocessing fails."""
    pass

class ModelEvaluationError(MLException):
    """Exception raised when model evaluation fails."""
    pass

class HyperparameterError(MLException):
    """Exception raised when hyperparameter tuning fails."""
    pass

class DeploymentError(MLException):
    """Exception raised when model deployment fails."""
    pass

class MonitoringError(MLException):
    """Exception raised when model monitoring fails."""
    pass

class VersioningError(MLException):
    """Exception raised when model versioning fails."""
    pass

class ScalingError(MLException):
    """Exception raised when model scaling fails."""
    pass 