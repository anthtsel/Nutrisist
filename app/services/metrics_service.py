from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.models.historical_metrics import HistoricalMetrics
from app.models.time_series_metrics import TimeSeriesMetrics
from app.device_data.models import DeviceDataStore

class MetricsService:
    """Service for handling metrics aggregation and storage."""
    
    def __init__(self):
        self.device_store = DeviceDataStore()
        self.time_series = TimeSeriesMetrics()
    
    def process_device_data(self, user_id: int):
        """Process device data and store aggregated metrics."""
        # Get unprocessed device data
        unprocessed_data = self.device_store.get_unprocessed_data()
        
        for doc in unprocessed_data:
            try:
                # Store raw time-series data
                self._store_time_series_metrics(user_id, doc)
                
                # Aggregate and store daily metrics
                self._aggregate_daily_metrics(user_id, doc)
                
                # Mark as processed
                self.device_store.mark_as_processed(str(doc['_id']))
            except Exception as e:
                print(f"Error processing document {doc['_id']}: {str(e)}")
    
    def _store_time_series_metrics(self, user_id: int, doc: Dict[str, Any]):
        """Store time-series metrics from device data."""
        data = doc['data']
        timestamp = doc['timestamp']
        
        # Example: Store heart rate data
        if 'heart_rate' in data:
            self.time_series.store_metric(
                user_id=user_id,
                metric_type='heart_rate',
                timestamp=timestamp,
                value=data['heart_rate'],
                metadata={'source': 'device'}
            )
        
        # Example: Store steps data
        if 'steps' in data:
            self.time_series.store_metric(
                user_id=user_id,
                metric_type='steps',
                timestamp=timestamp,
                value=data['steps'],
                metadata={'source': 'device'}
            )
    
    def _aggregate_daily_metrics(self, user_id: int, doc: Dict[str, Any]):
        """Aggregate and store daily metrics."""
        date = doc['timestamp'].date()
        data = doc['data']
        
        # Example: Store daily steps
        if 'steps' in data:
            metric = HistoricalMetrics(
                user_id=user_id,
                date=date,
                metric_type='daily_steps',
                value=data['steps']
            )
            db.session.merge(metric)  # Update if exists, insert if not
        
        # Example: Store daily activity minutes
        if 'active_minutes' in data:
            metric = HistoricalMetrics(
                user_id=user_id,
                date=date,
                metric_type='daily_activity_minutes',
                value=data['active_minutes']
            )
            db.session.merge(metric)
        
        db.session.commit()
    
    def get_user_metrics(self, user_id: int, metric_type: str,
                        start_date: datetime, end_date: datetime,
                        granularity: str = 'daily') -> Dict[str, Any]:
        """Get metrics for a user with specified granularity."""
        if granularity == 'raw':
            # Get raw time-series data
            return {
                'data': self.time_series.get_metrics(
                    user_id, metric_type, start_date, end_date
                )
            }
        elif granularity == 'daily':
            # Get daily aggregated data
            return {
                'data': HistoricalMetrics.get_user_metrics(
                    user_id, start_date, end_date, metric_type
                )
            }
        elif granularity == 'aggregated':
            # Get aggregated data with min/max/avg
            return {
                'data': self.time_series.get_metrics(
                    user_id, metric_type, start_date, end_date,
                    aggregation='daily'
                )
            }
    
    def get_metric_trends(self, user_id: int, metric_type: str,
                         days: int = 30) -> Dict[str, Any]:
        """Get metric trends over a period."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily aggregated data
        daily_data = HistoricalMetrics.get_user_metrics(
            user_id, start_date, end_date, metric_type
        )
        
        # Calculate trends
        if len(daily_data) > 1:
            first_value = daily_data[0].value
            last_value = daily_data[-1].value
            trend = (last_value - first_value) / first_value * 100
        else:
            trend = 0
        
        return {
            'current_value': last_value if daily_data else None,
            'trend_percentage': trend,
            'daily_data': daily_data
        } 