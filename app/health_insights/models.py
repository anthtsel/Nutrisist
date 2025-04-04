from .. import db
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, Any

class DataType(Enum):
    HEART_RATE = "heart_rate"
    SLEEP = "sleep"
    STEPS = "steps"
    ACTIVITY = "activity"
    NUTRITION = "nutrition"
    RECOVERY = "recovery"
    STRESS = "stress"

class HealthPlatform(ABC):
    """Abstract base class for health data platforms."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.last_sync = None
        self.sync_interval = 6  # hours
        self.auto_sync = True
    
    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Connect to the health platform."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the health platform."""
        pass
    
    @abstractmethod
    def fetch_data(self, data_type: DataType, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch health data from the platform."""
        pass
    
    @abstractmethod
    def normalize_data(self, data: Dict[str, Any], data_type: DataType) -> Dict[str, Any]:
        """Normalize platform-specific data to unified format."""
        pass

class UserProfile(db.Model):
    """User health profile model."""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)  # in kg
    height = db.Column(db.Integer, nullable=False)  # in cm
    gender = db.Column(db.String(20), nullable=False)
    activity_level = db.Column(db.String(20), nullable=False)
    goal_type = db.Column(db.String(20), nullable=False)
    weekly_activity_target = db.Column(db.Float, nullable=False)  # in hours
    medical_conditions = db.Column(db.Text)
    medications = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserProfile {self.name}>'

class HealthInsightModel:
    """Model for generating health insights."""
    
    def analyze_heart_rate(self, heart_rate_data, user_profile):
        """Analyze heart rate data and generate insights."""
        if not heart_rate_data:
            return {
                'status': 'no_data',
                'confidence': 0,
                'recommendations': ['Start tracking your heart rate to get insights']
            }
            
        # Calculate average heart rate
        heart_rates = [hr['value'] for hr in heart_rate_data]
        avg_hr = sum(heart_rates) / len(heart_rates)
        
        # Determine status based on average heart rate
        if avg_hr > 100:
            status = 'elevated'
            recommendations = [
                'Consider consulting a healthcare provider',
                'Practice relaxation techniques',
                'Monitor your caffeine intake'
            ]
        elif avg_hr < 60:
            status = 'low'
            recommendations = [
                'This could be normal for athletes',
                'Monitor for symptoms like dizziness',
                'Ensure adequate hydration'
            ]
        else:
            status = 'normal'
            recommendations = [
                'Maintain your current lifestyle',
                'Continue regular exercise',
                'Keep tracking your heart rate'
            ]
            
        return {
            'status': status,
            'confidence': 0.8,
            'recommendations': recommendations
        }
        
    def analyze_sleep_quality(self, sleep_data, activity_data):
        """Analyze sleep quality and generate insights."""
        if not sleep_data:
            return {
                'quality_score': 0,
                'status': 'no_data',
                'recommendations': ['Start tracking your sleep to get insights']
            }
            
        # Calculate average sleep duration
        sleep_durations = [sleep['duration'] for sleep in sleep_data]
        avg_duration = sum(sleep_durations) / len(sleep_durations)
        
        # Calculate quality score (0-1)
        quality_score = min(avg_duration / (8 * 3600), 1)  # 8 hours as target
        
        # Generate recommendations
        if quality_score < 0.6:
            status = 'poor'
            recommendations = [
                'Aim for 7-9 hours of sleep',
                'Maintain a consistent sleep schedule',
                'Create a relaxing bedtime routine'
            ]
        elif quality_score < 0.8:
            status = 'fair'
            recommendations = [
                'You\'re getting close to optimal sleep',
                'Try to get to bed 30 minutes earlier',
                'Limit screen time before bed'
            ]
        else:
            status = 'good'
            recommendations = [
                'Maintain your current sleep schedule',
                'Keep your bedroom cool and dark',
                'Continue monitoring your sleep quality'
            ]
            
        return {
            'quality_score': quality_score,
            'status': status,
            'recommendations': recommendations
        }
        
    def analyze_recovery(self, activity_data, sleep_data, heart_rate_data):
        """Analyze recovery status based on activity, sleep, and heart rate."""
        if not activity_data or not sleep_data or not heart_rate_data:
            return {
                'status': 'unknown',
                'confidence': 0,
                'recommendations': ['Track more data to get recovery insights']
            }
            
        # Simple recovery score based on sleep quality and heart rate
        sleep_quality = self.analyze_sleep_quality(sleep_data, activity_data)
        hr_analysis = self.analyze_heart_rate(heart_rate_data, None)
        
        if sleep_quality['status'] == 'good' and hr_analysis['status'] == 'normal':
            status = 'ready'
            recommendations = [
                'You\'re ready for high-intensity training',
                'Focus on performance goals',
                'Stay hydrated during workouts'
            ]
        elif sleep_quality['status'] == 'poor' or hr_analysis['status'] == 'elevated':
            status = 'needs_rest'
            recommendations = [
                'Take a rest day',
                'Focus on light activities',
                'Prioritize sleep tonight'
            ]
        else:
            status = 'moderate'
            recommendations = [
                'Moderate intensity activities recommended',
                'Listen to your body',
                'Focus on technique over intensity'
            ]
            
        return {
            'status': status,
            'confidence': 0.7,
            'recommendations': recommendations
        }
        
    def calculate_nutrition_needs(self, activity_data, user_profile):
        """Calculate nutrition needs based on activity and profile."""
        # Base metabolic rate using Harris-Benedict equation
        if user_profile['gender'] == 'male':
            bmr = 88.362 + (13.397 * user_profile['weight']) + \
                  (4.799 * user_profile['height']) - (5.677 * user_profile['age'])
        else:
            bmr = 447.593 + (9.247 * user_profile['weight']) + \
                  (3.098 * user_profile['height']) - (4.330 * user_profile['age'])
                  
        # Activity multiplier
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'high': 1.725,
            'athlete': 1.9
        }
        
        multiplier = activity_multipliers.get(user_profile['activity_level'], 1.2)
        daily_calories = bmr * multiplier
        
        # Adjust based on goal
        if user_profile.get('goal_type') == 'weight_loss':
            daily_calories *= 0.85  # 15% deficit
        elif user_profile.get('goal_type') == 'muscle_gain':
            daily_calories *= 1.1   # 10% surplus
            
        # Calculate macros
        protein = user_profile['weight'] * 2  # 2g per kg
        fat = (daily_calories * 0.25) / 9     # 25% of calories from fat
        carbs = (daily_calories - (protein * 4 + fat * 9)) / 4  # Remainder from carbs
        
        return {
            'daily_calories': int(daily_calories),
            'macros': {
                'protein': int(protein),
                'fat': int(fat),
                'carbs': int(carbs)
            },
            'hydration': int(user_profile['weight'] * 35)  # 35ml per kg
        } 