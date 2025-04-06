import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta

def preprocess_health_data(data: List[Dict[str, Any]]) -> np.ndarray:
    """Preprocess health data for ML models."""
    # Extract relevant features
    features = []
    for entry in data:
        feature_vector = [
            entry.get('heart_rate', 0),
            entry.get('steps', 0),
            entry.get('calories', 0),
            entry.get('sleep_duration', 0),
            entry.get('stress_level', 0)
        ]
        features.append(feature_vector)
    
    return np.array(features)

def calculate_recovery_score(health_data: Dict[str, Any]) -> float:
    """Calculate recovery score based on health metrics."""
    # Extract metrics
    heart_rate = health_data.get('heart_rate', 0)
    sleep_duration = health_data.get('sleep_duration', 0)
    stress_level = health_data.get('stress_level', 0)
    activity_level = health_data.get('activity_level', 0)
    
    # Normalize metrics
    heart_rate_norm = min(max(heart_rate / 100, 0), 1)
    sleep_norm = min(max(sleep_duration / 8, 0), 1)
    stress_norm = min(max(1 - stress_level / 100, 0), 1)
    activity_norm = min(max(activity_level / 100, 0), 1)
    
    # Calculate weighted score
    weights = {
        'heart_rate': 0.3,
        'sleep': 0.3,
        'stress': 0.2,
        'activity': 0.2
    }
    
    score = (
        weights['heart_rate'] * heart_rate_norm +
        weights['sleep'] * sleep_norm +
        weights['stress'] * stress_norm +
        weights['activity'] * activity_norm
    )
    
    return round(score * 100, 2)

def generate_nutrition_recommendations(
    health_data: Dict[str, Any],
    activity_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Generate personalized nutrition recommendations."""
    # Extract metrics
    calories_burned = activity_data.get('calories_burned', 0)
    activity_duration = activity_data.get('duration', 0)
    recovery_score = health_data.get('recovery_score', 0)
    
    # Calculate daily calorie needs
    base_calories = 2000  # Base metabolic rate
    activity_multiplier = 1 + (activity_duration / 60) * 0.1
    recovery_multiplier = 1 + (recovery_score / 100) * 0.2
    
    daily_calories = base_calories * activity_multiplier * recovery_multiplier
    
    # Generate macronutrient distribution
    protein_percentage = 0.3
    carbs_percentage = 0.5
    fat_percentage = 0.2
    
    recommendations = {
        'daily_calories': round(daily_calories),
        'macronutrients': {
            'protein': {
                'grams': round(daily_calories * protein_percentage / 4),
                'percentage': protein_percentage * 100
            },
            'carbohydrates': {
                'grams': round(daily_calories * carbs_percentage / 4),
                'percentage': carbs_percentage * 100
            },
            'fat': {
                'grams': round(daily_calories * fat_percentage / 9),
                'percentage': fat_percentage * 100
            }
        },
        'hydration': {
            'daily_water': round(daily_calories / 30),  # ml per calorie
            'electrolytes': True if activity_duration > 60 else False
        },
        'timing': {
            'pre_workout': '1-2 hours before activity',
            'post_workout': 'Within 30 minutes after activity',
            'meal_frequency': '3-5 meals per day'
        }
    }
    
    return recommendations

def classify_activity(sensor_data: Dict[str, Any]) -> Dict[str, Any]:
    """Classify physical activity based on sensor data."""
    # Extract sensor metrics
    acceleration = sensor_data.get('acceleration', [0, 0, 0])
    gyroscope = sensor_data.get('gyroscope', [0, 0, 0])
    heart_rate = sensor_data.get('heart_rate', 0)
    
    # Calculate activity intensity
    acc_magnitude = np.sqrt(sum(x**2 for x in acceleration))
    gyro_magnitude = np.sqrt(sum(x**2 for x in gyroscope))
    
    intensity = (acc_magnitude + gyro_magnitude) / 2
    
    # Classify activity type
    if intensity < 1.0:
        activity_type = 'resting'
    elif intensity < 2.0:
        activity_type = 'walking'
    elif intensity < 3.0:
        activity_type = 'running'
    else:
        activity_type = 'high_intensity'
    
    # Calculate confidence score
    confidence = min(max(intensity / 4, 0), 1)
    
    return {
        'activity_type': activity_type,
        'intensity': round(intensity, 2),
        'confidence': round(confidence, 2),
        'heart_rate': heart_rate,
        'timestamp': datetime.utcnow().isoformat()
    }

def aggregate_health_data(
    data: List[Dict[str, Any]],
    window: timedelta = timedelta(days=1)
) -> Dict[str, Any]:
    """Aggregate health data over a time window."""
    if not data:
        return {}
    
    # Calculate time window boundaries
    end_time = datetime.utcnow()
    start_time = end_time - window
    
    # Filter data within time window
    window_data = [
        entry for entry in data
        if start_time <= datetime.fromisoformat(entry['timestamp']) <= end_time
    ]
    
    if not window_data:
        return {}
    
    # Aggregate metrics
    aggregated = {
        'heart_rate': {
            'min': min(entry.get('heart_rate', 0) for entry in window_data),
            'max': max(entry.get('heart_rate', 0) for entry in window_data),
            'avg': sum(entry.get('heart_rate', 0) for entry in window_data) / len(window_data)
        },
        'steps': sum(entry.get('steps', 0) for entry in window_data),
        'calories': sum(entry.get('calories', 0) for entry in window_data),
        'sleep_duration': sum(entry.get('sleep_duration', 0) for entry in window_data),
        'stress_level': sum(entry.get('stress_level', 0) for entry in window_data) / len(window_data),
        'activity_level': sum(entry.get('activity_level', 0) for entry in window_data) / len(window_data)
    }
    
    return aggregated 