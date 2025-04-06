from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.device_data.models import DeviceDataStore
from app import garmin_client

class GarminService:
    """Service for handling Garmin device data integration."""
    
    def __init__(self):
        self.device_store = DeviceDataStore()
        self.client = garmin_client
    
    def fetch_and_store_user_data(self, user_id: int, access_token: str):
        """Fetch and store Garmin data for a user."""
        # Set the access token
        self.client.set_access_token(access_token)
        
        # Fetch different types of data
        data_types = {
            'activities': self.client.get_activities,
            'steps': self.client.get_steps,
            'heart_rate': self.client.get_heart_rate,
            'sleep': self.client.get_sleep,
            'body_composition': self.client.get_body_composition
        }
        
        for data_type, fetch_method in data_types.items():
            try:
                data = fetch_method()
                if data:
                    self.device_store.store_garmin_data(user_id, data_type, data)
            except Exception as e:
                print(f"Error fetching {data_type} data: {str(e)}")
    
    def get_user_data(self, user_id: int, data_type: str = None,
                     start_date: datetime = None, end_date: datetime = None,
                     limit: int = 100) -> List[Dict]:
        """Retrieve stored Garmin data for a user."""
        return self.device_store.get_garmin_data(
            user_id, data_type, start_date, end_date, limit
        )
    
    def process_unprocessed_data(self, limit: int = 100):
        """Process unprocessed device data."""
        unprocessed_data = self.device_store.get_unprocessed_data(limit)
        
        for doc in unprocessed_data:
            try:
                # Process the data (implement your processing logic here)
                # For example, extract insights, update user metrics, etc.
                
                # Mark as processed
                self.device_store.mark_as_processed(str(doc['_id']))
            except Exception as e:
                print(f"Error processing document {doc['_id']}: {str(e)}")
    
    def sync_user_data(self, user_id: int, access_token: str):
        """Synchronize user data with Garmin."""
        # Get the last sync timestamp
        last_sync = self.get_last_sync_timestamp(user_id)
        
        # Fetch new data since last sync
        self.fetch_and_store_user_data(user_id, access_token)
        
        # Process the new data
        self.process_unprocessed_data()
    
    def get_last_sync_timestamp(self, user_id: int) -> datetime:
        """Get the timestamp of the last successful sync."""
        latest_data = self.device_store.get_garmin_data(user_id, limit=1)
        if latest_data:
            return latest_data[0]['timestamp']
        return datetime.utcnow() - timedelta(days=7)  # Default to 7 days ago 