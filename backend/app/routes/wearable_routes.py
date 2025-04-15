from flask import Blueprint, request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.wearable_service import WearableService
from app.services.meal_service import MealService

wearable_bp = Blueprint('wearable', __name__)

@wearable_bp.route('/connect', methods=['POST'])
@jwt_required()
def connect_device():
    """
    Connect a wearable device for the current user
    Requires: device_type, auth_data
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    if not data or 'device_type' not in data or 'auth_data' not in data:
        return jsonify({
            'success': False, 
            'message': 'Missing required fields: device_type and auth_data'
        }), 400
    
    device_type = data.get('device_type')
    auth_data = data.get('auth_data')
    
    # Connect the device
    success = WearableService.connect_device(user_id, device_type, auth_data)
    
    if success:
        # Generate a meal plan based on the newly connected device data
        meal_plan = MealService.generate_meal_plan(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Device connected successfully',
            'meal_plan_generated': meal_plan is not None,
            'meal_plan_id': meal_plan.id if meal_plan else None
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to connect device'
        }), 500

@wearable_bp.route('/disconnect', methods=['POST'])
@jwt_required()
def disconnect_device():
    """
    Disconnect a wearable device for the current user
    """
    user_id = get_jwt_identity()
    
    # Disconnect the device
    success = WearableService.disconnect_device(user_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Device disconnected successfully'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to disconnect device'
        }), 500

@wearable_bp.route('/sync', methods=['POST'])
@jwt_required()
def sync_device():
    """
    Manually trigger a sync for the connected wearable device
    """
    user_id = get_jwt_identity()
    
    # Sync wearable data
    success = WearableService.sync_wearable_data(user_id)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Device data synced successfully'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to sync device data'
        }), 500

@wearable_bp.route('/data', methods=['GET'])
@jwt_required()
def get_wearable_data():
    """
    Get aggregated wearable data for the current user
    """
    user_id = get_jwt_identity()
    
    # Get latest aggregated wearable data
    wearable_data = WearableService.get_latest_aggregated_data(user_id)
    
    if wearable_data:
        # Convert ObjectId to string for JSON serialization
        wearable_data['_id'] = str(wearable_data['_id'])
        
        return jsonify({
            'success': True,
            'data': wearable_data
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'No wearable data found'
        }), 404