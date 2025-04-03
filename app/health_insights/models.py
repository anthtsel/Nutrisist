import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import joblib
import os

class HealthInsightModel:
    def __init__(self):
        self.heart_rate_model = None
        self.sleep_quality_model = None
        self.recovery_model = None
        self.scaler = StandardScaler()
        self.models_dir = os.path.join(os.path.dirname(__file__), 'trained_models')
        self._load_models()

    def _load_models(self):
        """Load pre-trained models if they exist"""
        try:
            self.heart_rate_model = joblib.load(os.path.join(self.models_dir, 'heart_rate_model.joblib'))
            self.sleep_quality_model = joblib.load(os.path.join(self.models_dir, 'sleep_quality_model.joblib'))
            self.recovery_model = joblib.load(os.path.join(self.models_dir, 'recovery_model.joblib'))
            self.scaler = joblib.load(os.path.join(self.models_dir, 'scaler.joblib'))
        except:
            self._initialize_models()

    def _initialize_models(self):
        """Initialize new models if pre-trained ones don't exist"""
        # Heart Rate Model (Random Forest)
        self.heart_rate_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        # Sleep Quality Model (LSTM)
        self.sleep_quality_model = Sequential([
            LSTM(64, input_shape=(24, 5)),  # 24 hours of data, 5 features
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        self.sleep_quality_model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )

        # Recovery Model (Random Forest)
        self.recovery_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

    def analyze_heart_rate(self, heart_rate_data, user_profile):
        """Analyze heart rate data and provide insights"""
        # Prepare features
        features = self._prepare_heart_rate_features(heart_rate_data, user_profile)
        
        # Scale features
        scaled_features = self.scaler.transform(features)
        
        # Predict heart rate status
        prediction = self.heart_rate_model.predict_proba(scaled_features)[0]
        
        # Generate insights
        insights = {
            'status': 'normal' if prediction[0] > 0.7 else 'elevated' if prediction[0] > 0.3 else 'high',
            'confidence': float(max(prediction)),
            'recommendations': self._generate_heart_rate_recommendations(prediction[0], user_profile)
        }
        
        return insights

    def analyze_sleep_quality(self, sleep_data, activity_data):
        """Analyze sleep quality and provide recovery insights"""
        # Prepare features
        features = self._prepare_sleep_features(sleep_data, activity_data)
        
        # Scale features
        scaled_features = self.scaler.transform(features)
        
        # Reshape for LSTM
        lstm_features = scaled_features.reshape(1, 24, 5)
        
        # Predict sleep quality
        quality_score = self.sleep_quality_model.predict(lstm_features)[0][0]
        
        # Generate insights
        insights = {
            'quality_score': float(quality_score),
            'status': 'good' if quality_score > 0.7 else 'fair' if quality_score > 0.4 else 'poor',
            'recommendations': self._generate_sleep_recommendations(quality_score, sleep_data)
        }
        
        return insights

    def analyze_recovery(self, activity_data, sleep_data, heart_rate_data):
        """Analyze recovery status and provide recommendations"""
        # Prepare features
        features = self._prepare_recovery_features(activity_data, sleep_data, heart_rate_data)
        
        # Scale features
        scaled_features = self.scaler.transform(features)
        
        # Predict recovery status
        prediction = self.recovery_model.predict_proba(scaled_features)[0]
        
        # Generate insights
        insights = {
            'status': 'ready' if prediction[0] > 0.7 else 'moderate' if prediction[0] > 0.3 else 'rest_needed',
            'confidence': float(max(prediction)),
            'recommendations': self._generate_recovery_recommendations(prediction[0], activity_data)
        }
        
        return insights

    def calculate_nutrition_needs(self, activity_data, user_profile):
        """Calculate personalized nutrition needs based on activity and goals"""
        # Calculate daily calorie burn
        daily_calories = self._calculate_daily_calories(activity_data, user_profile)
        
        # Calculate macronutrient ratios based on goals
        macros = self._calculate_macros(daily_calories, user_profile)
        
        # Calculate hydration needs
        hydration = self._calculate_hydration_needs(activity_data, user_profile)
        
        return {
            'daily_calories': daily_calories,
            'macros': macros,
            'hydration': hydration
        }

    def _prepare_heart_rate_features(self, heart_rate_data, user_profile):
        """Prepare features for heart rate analysis"""
        features = []
        for hr in heart_rate_data:
            features.append([
                hr['value'],
                user_profile['age'],
                user_profile['weight'],
                user_profile['height'],
                hr['timestamp'].hour,
                hr['timestamp'].minute
            ])
        return np.array(features)

    def _prepare_sleep_features(self, sleep_data, activity_data):
        """Prepare features for sleep quality analysis"""
        features = []
        for hour in range(24):
            hour_data = {
                'sleep_duration': sleep_data.get(hour, {}).get('duration', 0),
                'sleep_quality': sleep_data.get(hour, {}).get('quality', 0),
                'activity_level': activity_data.get(hour, {}).get('level', 0),
                'heart_rate': activity_data.get(hour, {}).get('heart_rate', 0),
                'temperature': activity_data.get(hour, {}).get('temperature', 0)
            }
            features.append(list(hour_data.values()))
        return np.array(features)

    def _prepare_recovery_features(self, activity_data, sleep_data, heart_rate_data):
        """Prepare features for recovery analysis"""
        features = []
        for hour in range(24):
            hour_data = {
                'activity_intensity': activity_data.get(hour, {}).get('intensity', 0),
                'sleep_quality': sleep_data.get(hour, {}).get('quality', 0),
                'heart_rate_variability': heart_rate_data.get(hour, {}).get('hrv', 0),
                'rest_duration': activity_data.get(hour, {}).get('rest_duration', 0),
                'stress_level': activity_data.get(hour, {}).get('stress', 0)
            }
            features.append(list(hour_data.values()))
        return np.array(features)

    def _calculate_daily_calories(self, activity_data, user_profile):
        """Calculate daily calorie burn based on activity and user profile"""
        # BMR calculation using Mifflin-St Jeor Equation
        if user_profile['gender'] == 'male':
            bmr = 10 * user_profile['weight'] + 6.25 * user_profile['height'] - 5 * user_profile['age'] + 5
        else:
            bmr = 10 * user_profile['weight'] + 6.25 * user_profile['height'] - 5 * user_profile['age'] - 161

        # Activity multiplier based on activity level
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'very': 1.725,
            'extra': 1.9
        }
        
        # Calculate activity calories
        activity_calories = sum(activity_data.get(hour, {}).get('calories', 0) for hour in range(24))
        
        # Total daily calories
        total_calories = bmr * activity_multipliers.get(user_profile['activity_level'], 1.2) + activity_calories
        
        return round(total_calories)

    def _calculate_macros(self, daily_calories, user_profile):
        """Calculate macronutrient ratios based on goals"""
        goals = user_profile.get('health_goals', '').lower()
        
        if 'weight loss' in goals:
            protein_ratio = 0.4
            carb_ratio = 0.3
            fat_ratio = 0.3
        elif 'muscle gain' in goals:
            protein_ratio = 0.4
            carb_ratio = 0.4
            fat_ratio = 0.2
        else:  # maintenance
            protein_ratio = 0.3
            carb_ratio = 0.4
            fat_ratio = 0.3
        
        return {
            'protein': round(daily_calories * protein_ratio / 4),  # 4 calories per gram
            'carbs': round(daily_calories * carb_ratio / 4),      # 4 calories per gram
            'fat': round(daily_calories * fat_ratio / 9)          # 9 calories per gram
        }

    def _calculate_hydration_needs(self, activity_data, user_profile):
        """Calculate hydration needs based on activity and user profile"""
        # Base hydration (30ml per kg of body weight)
        base_hydration = user_profile['weight'] * 30
        
        # Activity hydration (500ml per hour of moderate activity)
        activity_hydration = sum(
            500 * (activity_data.get(hour, {}).get('intensity', 0) / 100)
            for hour in range(24)
        )
        
        # Temperature adjustment (increase by 10% for every 5°C above 25°C)
        avg_temperature = sum(
            activity_data.get(hour, {}).get('temperature', 25)
            for hour in range(24)
        ) / 24
        
        if avg_temperature > 25:
            temp_adjustment = 1 + ((avg_temperature - 25) / 5) * 0.1
        else:
            temp_adjustment = 1
        
        total_hydration = (base_hydration + activity_hydration) * temp_adjustment
        
        return round(total_hydration)

    def _generate_heart_rate_recommendations(self, prediction, user_profile):
        """Generate heart rate recommendations"""
        recommendations = []
        
        if prediction < 0.3:  # High heart rate
            recommendations.append("Your heart rate is elevated. Consider taking a break and practicing deep breathing.")
            recommendations.append("Avoid strenuous activities until your heart rate returns to normal.")
        elif prediction < 0.7:  # Elevated heart rate
            recommendations.append("Your heart rate is slightly elevated. Monitor your activity level.")
            recommendations.append("Stay hydrated and consider reducing intensity if symptoms persist.")
        
        return recommendations

    def _generate_sleep_recommendations(self, quality_score, sleep_data):
        """Generate sleep quality recommendations"""
        recommendations = []
        
        if quality_score < 0.4:  # Poor sleep
            recommendations.append("Your sleep quality was poor. Consider improving your sleep hygiene:")
            recommendations.append("- Maintain a consistent sleep schedule")
            recommendations.append("- Create a relaxing bedtime routine")
            recommendations.append("- Avoid screens and caffeine before bed")
        elif quality_score < 0.7:  # Fair sleep
            recommendations.append("Your sleep quality was fair. Try to:")
            recommendations.append("- Get more deep sleep")
            recommendations.append("- Ensure your bedroom is dark and quiet")
            recommendations.append("- Exercise during the day but not close to bedtime")
        
        return recommendations

    def _generate_recovery_recommendations(self, prediction, activity_data):
        """Generate recovery recommendations"""
        recommendations = []
        
        if prediction < 0.3:  # Rest needed
            recommendations.append("Your body needs rest. Consider:")
            recommendations.append("- Taking a rest day")
            recommendations.append("- Focusing on light activities like walking or stretching")
            recommendations.append("- Prioritizing sleep and recovery")
        elif prediction < 0.7:  # Moderate recovery
            recommendations.append("Your recovery is moderate. You can:")
            recommendations.append("- Engage in light to moderate activities")
            recommendations.append("- Focus on mobility and flexibility")
            recommendations.append("- Monitor your energy levels")
        
        return recommendations 