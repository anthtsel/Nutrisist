from datetime import datetime
from typing import Dict, Any, List
from pymongo import MongoClient
from app import mongo_client

class AlertStore:
    """Handles storage and retrieval of alerts in MongoDB."""
    
    def __init__(self):
        self.db = mongo_client.get_default_database()
        self.alerts = self.db.alerts
        
    def create_alert(self, user_id: int, alert_type: str,
                    message: str, priority: str = 'medium',
                    metadata: Dict[str, Any] = None) -> str:
        """Create a new alert."""
        alert = {
            'user_id': user_id,
            'alert_type': alert_type,
            'message': message,
            'priority': priority,
            'status': 'active',
            'metadata': metadata or {},
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = self.alerts.insert_one(alert)
        return str(result.inserted_id)
    
    def get_user_alerts(self, user_id: int, status: str = None,
                       alert_type: str = None) -> List[Dict]:
        """Get alerts for a user with optional filters."""
        query = {'user_id': user_id}
        if status:
            query['status'] = status
        if alert_type:
            query['alert_type'] = alert_type
            
        return list(self.alerts.find(query)
                   .sort('created_at', -1))
    
    def update_alert_status(self, alert_id: str, status: str):
        """Update the status of an alert."""
        self.alerts.update_one(
            {'_id': alert_id},
            {
                '$set': {
                    'status': status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    def create_indexes(self):
        """Create necessary indexes for efficient querying."""
        self.alerts.create_index([('user_id', 1), ('status', 1)])
        self.alerts.create_index([('alert_type', 1)])
        self.alerts.create_index([('created_at', 1)])

class MealTracking:
    """Handles storage and retrieval of meal tracking data in MongoDB."""
    
    def __init__(self):
        self.db = mongo_client.get_default_database()
        self.tracking = self.db.meal_tracking
        
    def log_meal(self, user_id: int, meal_id: int,
                date: datetime, consumed: bool = True,
                notes: str = None, rating: int = None,
                metadata: Dict[str, Any] = None) -> str:
        """Log a meal consumption."""
        log = {
            'user_id': user_id,
            'meal_id': meal_id,
            'date': date,
            'consumed': consumed,
            'notes': notes,
            'rating': rating,
            'metadata': metadata or {},
            'created_at': datetime.utcnow()
        }
        result = self.tracking.insert_one(log)
        return str(result.inserted_id)
    
    def get_meal_history(self, user_id: int,
                        start_date: datetime,
                        end_date: datetime) -> List[Dict]:
        """Get meal history for a user within a date range."""
        query = {
            'user_id': user_id,
            'date': {
                '$gte': start_date,
                '$lte': end_date
            }
        }
        return list(self.tracking.find(query)
                   .sort('date', -1))
    
    def get_meal_ratings(self, meal_id: int) -> Dict[str, float]:
        """Get statistics for a specific meal."""
        pipeline = [
            {'$match': {'meal_id': meal_id, 'rating': {'$exists': True}}},
            {'$group': {
                '_id': None,
                'avg_rating': {'$avg': '$rating'},
                'total_ratings': {'$sum': 1}
            }}
        ]
        result = list(self.tracking.aggregate(pipeline))
        return result[0] if result else {'avg_rating': 0, 'total_ratings': 0}
    
    def create_indexes(self):
        """Create necessary indexes for efficient querying."""
        self.tracking.create_index([('user_id', 1), ('date', 1)])
        self.tracking.create_index([('meal_id', 1)])
        self.tracking.create_index([('rating', 1)]) 