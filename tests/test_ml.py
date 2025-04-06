import pytest
from datetime import datetime, timedelta
from app.ml.utils import (
    preprocess_health_data,
    calculate_recovery_score,
    generate_nutrition_recommendations,
    classify_activity,
    aggregate_health_data
)

def test_preprocess_health_data():
    """Test health data preprocessing."""
    # Sample health data
    data = [
        {
            'heart_rate': 75,
            'steps': 5000,
            'calories': 200,
            'sleep_duration': 7,
            'stress_level': 30
        },
        {
            'heart_rate': 80,
            'steps': 6000,
            'calories': 250,
            'sleep_duration': 6,
            'stress_level': 40
        }
    ]
    
    # Preprocess data
    features = preprocess_health_data(data)
    
    # Check shape
    assert features.shape == (2, 5)
    
    # Check values
    assert features[0, 0] == 75  # heart_rate
    assert features[0, 1] == 5000  # steps
    assert features[0, 2] == 200  # calories
    assert features[0, 3] == 7  # sleep_duration
    assert features[0, 4] == 30  # stress_level

def test_calculate_recovery_score():
    """Test recovery score calculation."""
    # Sample health data
    health_data = {
        'heart_rate': 75,
        'sleep_duration': 7,
        'stress_level': 30,
        'activity_level': 60
    }
    
    # Calculate score
    score = calculate_recovery_score(health_data)
    
    # Check score range
    assert 0 <= score <= 100
    
    # Check score calculation
    expected_score = (
        0.3 * (75 / 100) +  # heart_rate
        0.3 * (7 / 8) +  # sleep
        0.2 * (1 - 30 / 100) +  # stress
        0.2 * (60 / 100)  # activity
    ) * 100
    
    assert abs(score - expected_score) < 0.01

def test_generate_nutrition_recommendations():
    """Test nutrition recommendations generation."""
    # Sample health and activity data
    health_data = {
        'recovery_score': 80
    }
    activity_data = {
        'calories_burned': 500,
        'duration': 60
    }
    
    # Generate recommendations
    recommendations = generate_nutrition_recommendations(health_data, activity_data)
    
    # Check structure
    assert 'daily_calories' in recommendations
    assert 'macronutrients' in recommendations
    assert 'hydration' in recommendations
    assert 'timing' in recommendations
    
    # Check macronutrient distribution
    assert recommendations['macronutrients']['protein']['percentage'] == 30
    assert recommendations['macronutrients']['carbohydrates']['percentage'] == 50
    assert recommendations['macronutrients']['fat']['percentage'] == 20
    
    # Check hydration
    assert 'daily_water' in recommendations['hydration']
    assert 'electrolytes' in recommendations['hydration']

def test_classify_activity():
    """Test activity classification."""
    # Sample sensor data
    sensor_data = {
        'acceleration': [1.0, 0.5, 0.2],
        'gyroscope': [0.3, 0.1, 0.05],
        'heart_rate': 120
    }
    
    # Classify activity
    classification = classify_activity(sensor_data)
    
    # Check structure
    assert 'activity_type' in classification
    assert 'intensity' in classification
    assert 'confidence' in classification
    assert 'heart_rate' in classification
    assert 'timestamp' in classification
    
    # Check activity type
    assert classification['activity_type'] in ['resting', 'walking', 'running', 'high_intensity']
    
    # Check confidence range
    assert 0 <= classification['confidence'] <= 1

def test_aggregate_health_data():
    """Test health data aggregation."""
    # Sample health data
    data = [
        {
            'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            'heart_rate': 75,
            'steps': 5000,
            'calories': 200,
            'sleep_duration': 7,
            'stress_level': 30,
            'activity_level': 60
        },
        {
            'timestamp': datetime.utcnow().isoformat(),
            'heart_rate': 80,
            'steps': 6000,
            'calories': 250,
            'sleep_duration': 6,
            'stress_level': 40,
            'activity_level': 70
        }
    ]
    
    # Aggregate data
    aggregated = aggregate_health_data(data)
    
    # Check structure
    assert 'heart_rate' in aggregated
    assert 'steps' in aggregated
    assert 'calories' in aggregated
    assert 'sleep_duration' in aggregated
    assert 'stress_level' in aggregated
    assert 'activity_level' in aggregated
    
    # Check heart rate aggregation
    assert aggregated['heart_rate']['min'] == 75
    assert aggregated['heart_rate']['max'] == 80
    assert aggregated['heart_rate']['avg'] == 77.5
    
    # Check sum aggregation
    assert aggregated['steps'] == 11000
    assert aggregated['calories'] == 450
    assert aggregated['sleep_duration'] == 13
    
    # Check average aggregation
    assert aggregated['stress_level'] == 35
    assert aggregated['activity_level'] == 65 