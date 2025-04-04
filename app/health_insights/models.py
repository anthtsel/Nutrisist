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
    
    def analyze_heart_rate(self, heart_rate_data):
        """Analyze heart rate data and generate insights."""
        if not heart_rate_data:
            return {
                'status': 'NO_DATA',
                'confidence': 0,
                'recommendations': ['Start tracking your heart rate to get insights']
            }
            
        # Calculate average heart rate
        heart_rates = [hr['value'] for hr in heart_rate_data if isinstance(hr, dict) and 'value' in hr]
        if not heart_rates:
            return {
                'status': 'NO_DATA',
                'confidence': 0,
                'recommendations': ['No valid heart rate measurements found']
            }
            
        avg_hr = sum(heart_rates) / len(heart_rates)
        
        # Determine status based on average heart rate
        if avg_hr > 100:
            status = 'WARNING'
            recommendations = [
                'Consider consulting a healthcare provider',
                'Practice relaxation techniques',
                'Monitor your caffeine intake'
            ]
        elif avg_hr < 60:
            status = 'INFO'
            recommendations = [
                'This could be normal for athletes',
                'Monitor for symptoms like dizziness',
                'Ensure adequate hydration'
            ]
        else:
            status = 'SUCCESS'
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
        
    def analyze_sleep(self, sleep_data):
        """Analyze sleep quality and generate insights."""
        if not sleep_data:
            return {
                'quality_score': 0,
                'status': 'NO_DATA',
                'recommendations': ['Start tracking your sleep to get insights']
            }
            
        # Calculate average sleep duration
        sleep_durations = [sleep['duration'] for sleep in sleep_data if isinstance(sleep, dict) and 'duration' in sleep]
        if not sleep_durations:
            return {
                'quality_score': 0,
                'status': 'NO_DATA',
                'recommendations': ['No valid sleep measurements found']
            }
            
        avg_duration = sum(sleep_durations) / len(sleep_durations)
        
        # Calculate quality score (0-1)
        quality_score = min(avg_duration / (8 * 3600), 1)  # 8 hours as target
        
        # Generate recommendations
        if quality_score < 0.6:
            status = 'WARNING'
            recommendations = [
                'Aim for 7-9 hours of sleep',
                'Maintain a consistent sleep schedule',
                'Create a relaxing bedtime routine'
            ]
        elif quality_score < 0.8:
            status = 'INFO'
            recommendations = [
                'You\'re getting close to optimal sleep',
                'Try to get to bed 30 minutes earlier',
                'Limit screen time before bed'
            ]
        else:
            status = 'SUCCESS'
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
        
    def analyze_recovery(self, profile):
        """Analyze recovery status based on user profile."""
        if not profile:
            return {
                'status': 'NO_DATA',
                'confidence': 0,
                'recommendations': ['Complete your profile to get recovery insights']
            }
            
        # Base recovery analysis on activity level and goals
        if profile.activity_level in ['high', 'athlete']:
            status = 'WARNING'
            recommendations = [
                'Ensure adequate rest between intense workouts',
                'Focus on proper nutrition and hydration',
                'Monitor for signs of overtraining'
            ]
        elif profile.activity_level == 'moderate':
            status = 'SUCCESS'
            recommendations = [
                'Your activity level is well-balanced',
                'Continue with your current routine',
                'Consider gradually increasing intensity'
            ]
        else:
            status = 'INFO'
            recommendations = [
                'Consider increasing your activity level',
                'Start with low-impact exercises',
                'Set realistic weekly goals'
            ]
            
        return {
            'status': status,
            'confidence': 0.7,
            'recommendations': recommendations
        }
        
    def analyze_nutrition(self, profile):
        """Calculate nutrition needs based on profile."""
        if not profile:
            return None
            
        # Calculate BMR using Harris-Benedict equation
        if profile.gender.lower() == 'male':
            bmr = 88.362 + (13.397 * profile.weight) + (4.799 * profile.height) - (5.677 * profile.age)
        else:
            bmr = 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age)
            
        # Activity multiplier
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'high': 1.725,
            'athlete': 1.9
        }
        
        multiplier = activity_multipliers.get(profile.activity_level.lower(), 1.2)
        daily_calories = bmr * multiplier
        
        # Adjust based on goal
        if profile.goal_type == 'weight_loss':
            daily_calories *= 0.85  # 15% deficit
            macros = {'protein': 40, 'carbs': 30, 'fat': 30}
        elif profile.goal_type == 'muscle_gain':
            daily_calories *= 1.1  # 10% surplus
            macros = {'protein': 30, 'carbs': 50, 'fat': 20}
        else:  # maintenance or fitness
            macros = {'protein': 30, 'carbs': 40, 'fat': 30}
            
        # Calculate water needs (ml) - basic calculation
        hydration = profile.weight * 35  # 35ml per kg of body weight
        
        return {
            'daily_calories': daily_calories,
            'macros': macros,
            'hydration': hydration
        } 