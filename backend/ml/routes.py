from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from app.ml.models import MLDataStore, RecoveryPredictor, NutritionAdvisor, ActivityClassifier

ml_bp = Blueprint('ml', __name__)
data_store = MLDataStore()
recovery_predictor = RecoveryPredictor()
nutrition_advisor = NutritionAdvisor()
activity_classifier = ActivityClassifier()

@ml_bp.route('/api/ml/health-data', methods=['POST'])
@login_required
def store_health_data():
    """Store health data from wearables."""
    try:
        data = request.get_json()
        data_type = data.get('type')
        health_data = data.get('data')
        
        if not data_type or not health_data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        result = data_store.store_health_data(
            user_id=current_user.id,
            data_type=data_type,
            data=health_data
        )
        
        return jsonify({
            'message': 'Health data stored successfully',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error storing health data: {str(e)}")
        return jsonify({'error': 'Failed to store health data'}), 500

@ml_bp.route('/api/ml/health-data', methods=['GET'])
@login_required
def get_health_data():
    """Retrieve health data for a specific time range."""
    try:
        data_type = request.args.get('type')
        days = int(request.args.get('days', 7))
        
        if not data_type:
            return jsonify({'error': 'Missing data type'}), 400
            
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        data = data_store.get_health_data(
            user_id=current_user.id,
            data_type=data_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify({'data': data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error retrieving health data: {str(e)}")
        return jsonify({'error': 'Failed to retrieve health data'}), 500

@ml_bp.route('/api/ml/recovery-prediction', methods=['GET'])
@login_required
def get_recovery_prediction():
    """Get recovery prediction for the user."""
    try:
        # Get recent health data
        health_data = data_store.get_health_data(
            user_id=current_user.id,
            data_type='recovery',
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow()
        )
        
        if not health_data:
            return jsonify({'error': 'No health data available'}), 404
            
        # Make prediction
        prediction = recovery_predictor.predict(health_data[-1])
        
        # Store prediction
        data_store.store_prediction(
            user_id=current_user.id,
            model_type='recovery',
            prediction=prediction
        )
        
        return jsonify({'prediction': prediction}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error generating recovery prediction: {str(e)}")
        return jsonify({'error': 'Failed to generate recovery prediction'}), 500

@ml_bp.route('/api/ml/nutrition-recommendations', methods=['GET'])
@login_required
def get_nutrition_recommendations():
    """Get personalized nutrition recommendations."""
    try:
        # Get recent health data and activity data
        health_data = data_store.get_health_data(
            user_id=current_user.id,
            data_type='nutrition',
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        if not health_data:
            return jsonify({'error': 'No health data available'}), 404
            
        # Make recommendations
        recommendations = nutrition_advisor.predict(health_data[-1])
        
        # Store recommendations
        data_store.store_prediction(
            user_id=current_user.id,
            model_type='nutrition',
            prediction=recommendations
        )
        
        return jsonify({'recommendations': recommendations}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error generating nutrition recommendations: {str(e)}")
        return jsonify({'error': 'Failed to generate nutrition recommendations'}), 500

@ml_bp.route('/api/ml/activity-classification', methods=['POST'])
@login_required
def classify_activity():
    """Classify physical activity based on sensor data."""
    try:
        data = request.get_json()
        sensor_data = data.get('sensor_data')
        
        if not sensor_data:
            return jsonify({'error': 'Missing sensor data'}), 400
            
        # Classify activity
        classification = activity_classifier.predict(sensor_data)
        
        # Store classification
        data_store.store_prediction(
            user_id=current_user.id,
            model_type='activity',
            prediction=classification
        )
        
        return jsonify({'classification': classification}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error classifying activity: {str(e)}")
        return jsonify({'error': 'Failed to classify activity'}), 500

@ml_bp.route('/api/ml/training-data', methods=['POST'])
@login_required
def store_training_data():
    """Store training data for ML models."""
    try:
        data = request.get_json()
        data_type = data.get('type')
        training_data = data.get('data')
        
        if not data_type or not training_data:
            return jsonify({'error': 'Missing required fields'}), 400
            
        result = data_store.store_training_data(
            data_type=data_type,
            data=training_data
        )
        
        return jsonify({
            'message': 'Training data stored successfully',
            'id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error storing training data: {str(e)}")
        return jsonify({'error': 'Failed to store training data'}), 500 