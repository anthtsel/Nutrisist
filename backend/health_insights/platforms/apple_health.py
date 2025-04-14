import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from pathlib import Path
from app.health_insights.models import HealthPlatform, DataType

logger = logging.getLogger(__name__)

class AppleHealthPlatform(HealthPlatform):
    """Apple Health platform integration.
    
    This class handles Apple Health data exported from iOS devices.
    Users need to export their health data from the Health app and upload
    the exported file to our platform.
    """
    
    def __init__(self, user_id: int, upload_folder: str = None):
        super().__init__(user_id)
        self.upload_folder = Path(upload_folder) if upload_folder else Path('uploads')
        if not self.upload_folder.exists():
            self.upload_folder.mkdir(parents=True)
        self.data_file = None
    
    def connect(self, filename: str = None) -> bool:
        """Connect to Apple Health data file.
        
        Args:
            filename: Name of the uploaded Apple Health export file
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if filename:
                self.data_file = self.upload_folder / filename
                if not self.data_file.exists():
                    logger.error(f"Apple Health data file not found: {filename}")
                    return False
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error connecting to Apple Health data: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Apple Health data.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        try:
            self.data_file = None
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting from Apple Health: {str(e)}")
            return False
    
    def fetch_data(self, data_type: DataType, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch health data from Apple Health export.
        
        Args:
            data_type: Type of data to fetch
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            dict: Health data in platform-specific format
        """
        try:
            if not self.data_file:
                raise ValueError("No Apple Health data file connected")
                
            if data_type == DataType.HEART_RATE:
                return self._fetch_heart_rate(start_date, end_date)
            elif data_type == DataType.SLEEP:
                return self._fetch_sleep(start_date, end_date)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Error fetching {data_type} data: {str(e)}")
            return {}
    
    def _fetch_heart_rate(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch heart rate data from Apple Health export."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            heart_rate_data = []
            for record in data.get('HeartRate', []):
                record_date = datetime.fromisoformat(record['date'])
                if start_date <= record_date <= end_date:
                    heart_rate_data.append({
                        "date": record['date'],
                        "value": record['value'],
                        "source": "apple_health"
                    })
            
            # Group by date and calculate metrics
            data_by_date = {}
            for record in heart_rate_data:
                date = record['date'].split('T')[0]
                if date not in data_by_date:
                    data_by_date[date] = []
                data_by_date[date].append(record['value'])
            
            processed_data = []
            for date, values in data_by_date.items():
                entry = {
                    "date": date,
                    "resting_heart_rate": min(values),
                    "max_heart_rate": max(values),
                    "avg_heart_rate": sum(values) / len(values),
                    "samples": values
                }
                processed_data.append(entry)
            
            return {"heart_rate": processed_data}
            
        except Exception as e:
            logger.error(f"Error fetching heart rate data: {str(e)}")
            return {}
    
    def _fetch_sleep(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch sleep data from Apple Health export."""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            sleep_data = []
            for record in data.get('Sleep', []):
                start_time = datetime.fromisoformat(record['startDate'])
                end_time = datetime.fromisoformat(record['endDate'])
                
                if (start_date <= start_time <= end_date or 
                    start_date <= end_time <= end_date):
                    duration = (end_time - start_time).total_seconds()
                    entry = {
                        "date": start_time.date().isoformat(),
                        "start_time": record['startDate'],
                        "end_time": record['endDate'],
                        "duration": duration,
                        "type": record.get('value', 'unknown'),
                        "source": "apple_health"
                    }
                    sleep_data.append(entry)
            
            return {"sleep": sleep_data}
            
        except Exception as e:
            logger.error(f"Error fetching sleep data: {str(e)}")
            return {}
    
    def normalize_data(self, data: Dict[str, Any], data_type: DataType) -> Dict[str, Any]:
        """Normalize Apple Health data to unified format."""
        if data_type == DataType.HEART_RATE:
            return self._normalize_heart_rate(data)
        elif data_type == DataType.SLEEP:
            return self._normalize_sleep(data)
        return {}
    
    def _normalize_heart_rate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Apple Health heart rate data."""
        normalized = {"heart_rate": []}
        
        try:
            for entry in data.get("heart_rate", []):
                normalized_entry = {
                    "date": entry["date"],
                    "resting_heart_rate": entry["resting_heart_rate"],
                    "max_heart_rate": entry["max_heart_rate"],
                    "avg_heart_rate": entry["avg_heart_rate"],
                    "source": "apple_health"
                }
                normalized["heart_rate"].append(normalized_entry)
                
        except Exception as e:
            logger.error(f"Error normalizing heart rate data: {str(e)}")
            
        return normalized
    
    def _normalize_sleep(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Apple Health sleep data."""
        normalized = {"sleep": []}
        
        try:
            for entry in data.get("sleep", []):
                normalized_entry = {
                    "date": entry["date"],
                    "start_time": entry["start_time"],
                    "end_time": entry["end_time"],
                    "duration": entry["duration"],
                    "type": entry["type"],
                    "source": "apple_health"
                }
                normalized["sleep"].append(normalized_entry)
                
        except Exception as e:
            logger.error(f"Error normalizing sleep data: {str(e)}")
            
        return normalized 