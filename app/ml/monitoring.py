import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.ml.config import MLConfig
from app.ml.logger import logger
from app.ml.exceptions import MonitoringError
from app.ml.models import MLDataStore

class ModelMonitor:
    """Monitor ML model performance and health."""
    
    def __init__(self):
        self.data_store = MLDataStore()
        self.metrics = {
            'predictions': [],
            'latency': [],
            'errors': []
        }
    
    def log_prediction(
        self,
        model_type: str,
        input_data: Dict[str, Any],
        prediction: Dict[str, Any],
        latency: float
    ) -> None:
        """Log model prediction and performance metrics."""
        try:
            # Store prediction metrics
            prediction_metric = {
                'model_type': model_type,
                'timestamp': datetime.utcnow(),
                'input_data': input_data,
                'prediction': prediction,
                'latency': latency
            }
            
            self.metrics['predictions'].append(prediction_metric)
            self.metrics['latency'].append(latency)
            
            # Log prediction
            logger.info(
                f"Model prediction - Type: {model_type}, "
                f"Latency: {latency:.2f}s"
            )
            
        except Exception as e:
            logger.error(f"Error logging prediction: {str(e)}")
            raise MonitoringError("Failed to log prediction")
    
    def log_error(
        self,
        model_type: str,
        error: Exception,
        input_data: Dict[str, Any] = None
    ) -> None:
        """Log model error."""
        try:
            # Store error metrics
            error_metric = {
                'model_type': model_type,
                'timestamp': datetime.utcnow(),
                'error': str(error),
                'input_data': input_data
            }
            
            self.metrics['errors'].append(error_metric)
            
            # Log error
            logger.error(
                f"Model error - Type: {model_type}, "
                f"Error: {str(error)}"
            )
            
        except Exception as e:
            logger.error(f"Error logging error: {str(e)}")
            raise MonitoringError("Failed to log error")
    
    def get_performance_metrics(
        self,
        model_type: str = None,
        time_window: timedelta = timedelta(hours=1)
    ) -> Dict[str, Any]:
        """Get model performance metrics."""
        try:
            # Filter metrics by time window
            cutoff_time = datetime.utcnow() - time_window
            
            predictions = [
                m for m in self.metrics['predictions']
                if m['timestamp'] >= cutoff_time
                and (model_type is None or m['model_type'] == model_type)
            ]
            
            latency = [
                m for m in self.metrics['latency']
                if m['timestamp'] >= cutoff_time
            ]
            
            errors = [
                m for m in self.metrics['errors']
                if m['timestamp'] >= cutoff_time
                and (model_type is None or m['model_type'] == model_type)
            ]
            
            # Calculate metrics
            total_predictions = len(predictions)
            total_errors = len(errors)
            
            if total_predictions > 0:
                avg_latency = sum(l['latency'] for l in latency) / len(latency)
                error_rate = total_errors / total_predictions
            else:
                avg_latency = 0
                error_rate = 0
            
            return {
                'total_predictions': total_predictions,
                'total_errors': total_errors,
                'error_rate': error_rate,
                'avg_latency': avg_latency,
                'time_window': str(time_window)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            raise MonitoringError("Failed to get performance metrics")
    
    def get_error_analysis(
        self,
        model_type: str = None,
        time_window: timedelta = timedelta(hours=1)
    ) -> List[Dict[str, Any]]:
        """Get detailed error analysis."""
        try:
            # Filter errors by time window
            cutoff_time = datetime.utcnow() - time_window
            
            errors = [
                m for m in self.metrics['errors']
                if m['timestamp'] >= cutoff_time
                and (model_type is None or m['model_type'] == model_type)
            ]
            
            # Group errors by type
            error_counts = {}
            for error in errors:
                error_type = error['error']
                if error_type not in error_counts:
                    error_counts[error_type] = 0
                error_counts[error_type] += 1
            
            # Format error analysis
            analysis = []
            for error_type, count in error_counts.items():
                analysis.append({
                    'error_type': error_type,
                    'count': count,
                    'percentage': count / len(errors) if errors else 0
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting error analysis: {str(e)}")
            raise MonitoringError("Failed to get error analysis")
    
    def get_latency_analysis(
        self,
        model_type: str = None,
        time_window: timedelta = timedelta(hours=1)
    ) -> Dict[str, Any]:
        """Get detailed latency analysis."""
        try:
            # Filter latency metrics by time window
            cutoff_time = datetime.utcnow() - time_window
            
            latency = [
                m for m in self.metrics['latency']
                if m['timestamp'] >= cutoff_time
            ]
            
            if not latency:
                return {
                    'min': 0,
                    'max': 0,
                    'avg': 0,
                    'p95': 0,
                    'p99': 0
                }
            
            # Calculate latency statistics
            latency_values = [l['latency'] for l in latency]
            latency_values.sort()
            
            return {
                'min': min(latency_values),
                'max': max(latency_values),
                'avg': sum(latency_values) / len(latency_values),
                'p95': latency_values[int(len(latency_values) * 0.95)],
                'p99': latency_values[int(len(latency_values) * 0.99)]
            }
            
        except Exception as e:
            logger.error(f"Error getting latency analysis: {str(e)}")
            raise MonitoringError("Failed to get latency analysis")
    
    def check_model_health(
        self,
        model_type: str = None,
        time_window: timedelta = timedelta(hours=1)
    ) -> Dict[str, Any]:
        """Check model health status."""
        try:
            # Get performance metrics
            metrics = self.get_performance_metrics(model_type, time_window)
            
            # Get error analysis
            error_analysis = self.get_error_analysis(model_type, time_window)
            
            # Get latency analysis
            latency_analysis = self.get_latency_analysis(model_type, time_window)
            
            # Determine health status
            health_status = 'healthy'
            if metrics['error_rate'] > 0.1:  # 10% error rate threshold
                health_status = 'unhealthy'
            elif metrics['avg_latency'] > 1.0:  # 1 second latency threshold
                health_status = 'degraded'
            
            return {
                'status': health_status,
                'metrics': metrics,
                'error_analysis': error_analysis,
                'latency_analysis': latency_analysis
            }
            
        except Exception as e:
            logger.error(f"Error checking model health: {str(e)}")
            raise MonitoringError("Failed to check model health")
    
    def cleanup_old_metrics(self, max_age: timedelta = timedelta(days=7)):
        """Clean up old metrics data."""
        try:
            cutoff_time = datetime.utcnow() - max_age
            
            # Clean up predictions
            self.metrics['predictions'] = [
                m for m in self.metrics['predictions']
                if m['timestamp'] >= cutoff_time
            ]
            
            # Clean up latency
            self.metrics['latency'] = [
                m for m in self.metrics['latency']
                if m['timestamp'] >= cutoff_time
            ]
            
            # Clean up errors
            self.metrics['errors'] = [
                m for m in self.metrics['errors']
                if m['timestamp'] >= cutoff_time
            ]
            
            logger.info("Cleaned up old metrics data")
            
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {str(e)}")
            raise MonitoringError("Failed to clean up old metrics") 