from datetime import datetime
from typing import Dict, Any, List
from pymongo import MongoClient
from app import mongo_client

class DeviceDataStore:
    """Handles storage and retrieval of device data in MongoDB."""
    
    def __init__(self):
        self.db = mongo_client.get_default_database()
        self.device_data = self.db.device_data
        
    def store_garmin_data(self, user_id: int, data_type: str, data: Dict[str, Any]):
        """Store Garmin device data."""
        document = {
            'user_id': user_id,
            'device_type': 'garmin',
            'data_type': data_type,
            'data': data,
            'timestamp': datetime.utcnow(),
            'processed': False
        }
        return self.device_data.insert_one(document)
    
    def get_garmin_data(self, user_id: int, data_type: str = None, 
                       start_date: datetime = None, end_date: datetime = None,
                       limit: int = 100) -> List[Dict]:
        """Retrieve Garmin data for a specific time range."""
        query = {
            'user_id': user_id,
            'device_type': 'garmin'
        }
        
        if data_type:
            query['data_type'] = data_type
            
        if start_date and end_date:
            query['timestamp'] = {
                '$gte': start_date,
                '$lte': end_date
            }
            
        return list(self.device_data.find(query)
                   .sort('timestamp', -1)
                   .limit(limit))
    
    def mark_as_processed(self, document_id: str):
        """Mark device data as processed."""
        return self.device_data.update_one(
            {'_id': document_id},
            {'$set': {'processed': True}}
        )
    
    def get_unprocessed_data(self, limit: int = 100) -> List[Dict]:
        """Retrieve unprocessed device data."""
        return list(self.device_data.find({'processed': False})
                   .sort('timestamp', 1)
                   .limit(limit))
    
    def create_indexes(self):
        """Create necessary indexes for efficient querying."""
        self.device_data.create_index([('user_id', 1), ('timestamp', 1)])
        self.device_data.create_index([('device_type', 1), ('data_type', 1)])
        self.device_data.create_index([('processed', 1)]) 