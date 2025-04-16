# routes/wearable_routes.py
from flask import Blueprint, request, jsonify, current_app, session
from services.wearable_service import WearableService
from services.meal_plan_generator import MealPlanGenerator
from models.user import User
from pymongo import MongoClient
from extensions import db
from flask_login import login_required, current_user
from app.models import WearableDevice, ActivityData
from datetime import datetime, timedelta
import requests
import json

wearable_bp = Blueprint('wearable', __name__)

@wearable_bp.route('/connect', methods=['POST'])
def connect_device():
    """Connect a wearable device"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
        
    user_id = session['user_id']
    data = request.json
    
    device_type = data.get('device_type')
    auth_token = data.get('auth_token')
    
    if not device_type or not auth_token:
        return jsonify({'error': 'Missing device_type or auth_token'}), 400
    
    # Initialize services
    mongo_client = MongoClient(current_app.config['MONGO_URI'])
    wearable_service = WearableService(current_app.config['MONGO_URI'], 'nutrisist')
    
    # Connect device
    result = wearable_service.connect_device(user_id, device_type, auth_token)
    
    if 'error' in result:
        return jsonify(result), 400
        
    return jsonify({'message': 'Device connected successfully', 'data': result}), 200
    
@wearable_bp.route('/generate-plan', methods=['POST'])
def generate_plan_from_wearable():
    """Generate a meal plan based on wearable data"""
    if 'user_id' not in session:
        return jsonify({'error': 'Authentication required'}), 401
        
    user_id = session['user_id']
    
    # Initialize services
    mongo_client = MongoClient(current_app.config['MONGO_URI'])
    meal_plan_generator = MealPlanGenerator(db.session, mongo_client.nutrisist)
    
    # Generate plan
    result = meal_plan_generator.generate_from_wearable(user_id)
    
    if isinstance(result, dict) and 'error' in result:
        return jsonify(result), 400
        
    return jsonify({
        'message': 'Meal plan generated successfully',
        'plan_id': result.id
    }), 200

@wearable_bp.route('/api/wearables/connect', methods=['POST'])
@login_required
def connect_wearable():
    try:
        data = request.get_json()
        device_type = data.get('device_type')
        auth_token = data.get('auth_token')

        if not device_type or not auth_token:
            return jsonify({'error': 'Missing required fields'}), 400

        # Check if user already has a connected device
        existing_device = WearableDevice.query.filter_by(user_id=current_user.id).first()
        if existing_device:
            return jsonify({'error': 'User already has a connected device'}), 400

        # Create new device connection
        new_device = WearableDevice(
            user_id=current_user.id,
            device_type=device_type,
            auth_token=auth_token,
            connected_at=datetime.utcnow()
        )
        db.session.add(new_device)
        db.session.commit()

        # Update user's wearable_connected status
        current_user.wearable_connected = True
        db.session.commit()

        return jsonify({'message': 'Device connected successfully'}), 200

    except Exception as e:
        current_app.logger.error(f'Error connecting wearable: {str(e)}')
        return jsonify({'error': 'Failed to connect device'}), 500

@wearable_bp.route('/api/wearables/activity/today', methods=['GET'])
@login_required
def get_today_activity():
    try:
        device = WearableDevice.query.filter_by(user_id=current_user.id).first()
        if not device:
            return jsonify({'error': 'No connected device found'}), 404

        # Fetch today's activity data
        today = datetime.utcnow().date()
        activity = ActivityData.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()

        if not activity:
            # If no data for today, fetch from wearable API
            activity_data = fetch_wearable_activity(device)
            if not activity_data:
                return jsonify({'error': 'Failed to fetch activity data'}), 500

            activity = ActivityData(
                user_id=current_user.id,
                date=today,
                steps=activity_data.get('steps', 0),
                calories=activity_data.get('calories', 0),
                sleep_minutes=activity_data.get('sleep_minutes', 0),
                heart_rate=activity_data.get('heart_rate', 0)
            )
            db.session.add(activity)
            db.session.commit()

        return jsonify({
            'steps': activity.steps,
            'calories': activity.calories,
            'sleep_minutes': activity.sleep_minutes,
            'heart_rate': activity.heart_rate
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching activity data: {str(e)}')
        return jsonify({'error': 'Failed to fetch activity data'}), 500

@wearable_bp.route('/api/wearables/activity/weekly', methods=['GET'])
@login_required
def get_weekly_activity():
    try:
        device = WearableDevice.query.filter_by(user_id=current_user.id).first()
        if not device:
            return jsonify({'error': 'No connected device found'}), 404

        # Calculate date range for the past week
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=6)

        # Fetch weekly activity data
        activities = ActivityData.query.filter(
            ActivityData.user_id == current_user.id,
            ActivityData.date >= start_date,
            ActivityData.date <= end_date
        ).order_by(ActivityData.date).all()

        # Prepare response data
        dates = []
        steps = []
        calories = []

        for activity in activities:
            dates.append(activity.date.strftime('%Y-%m-%d'))
            steps.append(activity.steps)
            calories.append(activity.calories)

        return jsonify({
            'dates': dates,
            'steps': steps,
            'calories': calories
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching weekly activity: {str(e)}')
        return jsonify({'error': 'Failed to fetch weekly activity data'}), 500

def fetch_wearable_activity(device):
    """Fetch activity data from wearable device API"""
    try:
        if device.device_type == 'fitbit':
            # Implement Fitbit API integration
            headers = {
                'Authorization': f'Bearer {device.auth_token}',
                'Accept': 'application/json'
            }
            response = requests.get(
                'https://api.fitbit.com/1/user/-/activities/date/today.json',
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    'steps': data['summary']['steps'],
                    'calories': data['summary']['caloriesOut'],
                    'sleep_minutes': data.get('summary', {}).get('totalMinutesAsleep', 0),
                    'heart_rate': data.get('summary', {}).get('restingHeartRate', 0)
                }
        elif device.device_type == 'apple_health':
            # Implement Apple Health API integration
            # Note: Apple Health requires different authentication and data access
            pass

        return None

    except Exception as e:
        current_app.logger.error(f'Error fetching from wearable API: {str(e)}')
        return None