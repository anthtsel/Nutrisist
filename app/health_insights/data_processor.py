from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from .models import DataType

logger = logging.getLogger(__name__)

class GarminDataProcessor:
    """Processor for Garmin Connect data files"""
    
    def __init__(self, upload_folder: str):
        self.upload_folder = Path(upload_folder)
        if not self.upload_folder.exists():
            self.upload_folder.mkdir(parents=True)
    
    def process_file(self, filename: str, data_type: DataType) -> Dict:
        """Process a Garmin data file and return normalized data"""
        file_path = self.upload_folder / filename
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if data_type == DataType.HEART_RATE:
                return self._process_heart_rate(data)
            elif data_type == DataType.SLEEP:
                return self._process_sleep(data)
            elif data_type == DataType.STEPS:
                return self._process_steps(data)
            elif data_type == DataType.ACTIVITY:
                return self._process_activity(data)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
                
        except Exception as e:
            logger.error(f"Error processing file {filename}: {str(e)}")
            raise
    
    def _process_heart_rate(self, data: Dict) -> Dict:
        """Process heart rate data from Garmin format"""
        try:
            heart_rate_data = []
            for reading in data.get('heartRateData', []):
                heart_rate_data.append({
                    'timestamp': datetime.fromisoformat(reading['timestamp']),
                    'value': reading['value'],
                    'source': 'garmin'
                })
            
            return {
                'type': DataType.HEART_RATE.value,
                'data': heart_rate_data,
                'summary': {
                    'avg_heart_rate': sum(hr['value'] for hr in heart_rate_data) / len(heart_rate_data) if heart_rate_data else 0,
                    'max_heart_rate': max(hr['value'] for hr in heart_rate_data) if heart_rate_data else 0,
                    'min_heart_rate': min(hr['value'] for hr in heart_rate_data) if heart_rate_data else 0
                }
            }
        except Exception as e:
            logger.error(f"Error processing heart rate data: {str(e)}")
            raise
    
    def _process_sleep(self, data: Dict) -> Dict:
        """Process sleep data from Garmin format"""
        try:
            sleep_data = {
                'start_time': datetime.fromisoformat(data['sleepStartTime']),
                'end_time': datetime.fromisoformat(data['sleepEndTime']),
                'duration': data['sleepDuration'],
                'quality': data['sleepQuality'],
                'deep_sleep': data.get('deepSleepDuration', 0),
                'light_sleep': data.get('lightSleepDuration', 0),
                'rem_sleep': data.get('remSleepDuration', 0),
                'awake': data.get('awakeDuration', 0),
                'source': 'garmin'
            }
            
            return {
                'type': DataType.SLEEP.value,
                'data': sleep_data,
                'summary': {
                    'total_duration': sleep_data['duration'],
                    'sleep_score': sleep_data['quality'],
                    'deep_sleep_percentage': (sleep_data['deep_sleep'] / sleep_data['duration'] * 100) if sleep_data['duration'] else 0
                }
            }
        except Exception as e:
            logger.error(f"Error processing sleep data: {str(e)}")
            raise
    
    def _process_steps(self, data: Dict) -> Dict:
        """Process steps data from Garmin format"""
        try:
            steps_data = []
            for entry in data.get('stepsData', []):
                steps_data.append({
                    'timestamp': datetime.fromisoformat(entry['timestamp']),
                    'count': entry['steps'],
                    'source': 'garmin'
                })
            
            total_steps = sum(step['count'] for step in steps_data)
            
            return {
                'type': DataType.STEPS.value,
                'data': steps_data,
                'summary': {
                    'total_steps': total_steps,
                    'goal_progress': (total_steps / 10000 * 100) if total_steps else 0  # Assuming 10k steps goal
                }
            }
        except Exception as e:
            logger.error(f"Error processing steps data: {str(e)}")
            raise
    
    def _process_activity(self, data: Dict) -> Dict:
        """Process activity data from Garmin format"""
        try:
            activity_data = {
                'type': data['activityType'],
                'start_time': datetime.fromisoformat(data['startTime']),
                'duration': data['duration'],
                'distance': data.get('distance', 0),
                'calories': data.get('calories', 0),
                'avg_heart_rate': data.get('averageHeartRate', 0),
                'max_heart_rate': data.get('maxHeartRate', 0),
                'intensity': data.get('intensity', 0),
                'source': 'garmin'
            }
            
            return {
                'type': DataType.ACTIVITY.value,
                'data': activity_data,
                'summary': {
                    'duration_minutes': activity_data['duration'] / 60,
                    'calories_burned': activity_data['calories'],
                    'avg_heart_rate': activity_data['avg_heart_rate']
                }
            }
        except Exception as e:
            logger.error(f"Error processing activity data: {str(e)}")
            raise 