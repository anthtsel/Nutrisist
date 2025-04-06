from datetime import datetime
from typing import Dict, Any, List
from pymongo import MongoClient
from app import mongo_client

class TimeSeriesMetrics:
    """Handles storage and retrieval of time-series metrics in MongoDB."""
    
    def __init__(self):
        self.db = mongo_client.get_default_database()
        self.metrics = self.db.time_series_metrics
        
    def store_metric(self, user_id: int, metric_type: str, 
                    timestamp: datetime, value: float,
                    metadata: Dict[str, Any] = None):
        """Store a time-series metric point."""
        document = {
            'user_id': user_id,
            'metric_type': metric_type,
            'timestamp': timestamp,
            'value': value,
            'metadata': metadata or {},
            'created_at': datetime.utcnow()
        }
        return self.metrics.insert_one(document)
    
    def get_metrics(self, user_id: int, metric_type: str,
                   start_time: datetime, end_time: datetime,
                   aggregation: str = None) -> List[Dict]:
        """Retrieve time-series metrics with optional aggregation."""
        query = {
            'user_id': user_id,
            'metric_type': metric_type,
            'timestamp': {
                '$gte': start_time,
                '$lte': end_time
            }
        }
        
        if aggregation:
            pipeline = [
                {'$match': query},
                {'$group': {
                    '_id': {
                        'year': {'$year': '$timestamp'},
                        'month': {'$month': '$timestamp'},
                        'day': {'$dayOfMonth': '$timestamp'}
                    },
                    'avg_value': {'$avg': '$value'},
                    'min_value': {'$min': '$value'},
                    'max_value': {'$max': '$value'},
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            return list(self.metrics.aggregate(pipeline))
        
        return list(self.metrics.find(query)
                   .sort('timestamp', 1))
    
    def get_latest_metric(self, user_id: int, metric_type: str) -> Dict:
        """Get the latest metric value for a user."""
        return self.metrics.find_one(
            {'user_id': user_id, 'metric_type': metric_type},
            sort=[('timestamp', -1)]
        )
    
    def create_indexes(self):
        """Create necessary indexes for efficient querying."""
        self.metrics.create_index([('user_id', 1), ('metric_type', 1), ('timestamp', 1)])
        self.metrics.create_index([('timestamp', 1)]) 