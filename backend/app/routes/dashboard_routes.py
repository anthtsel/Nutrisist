from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.models import User, UserProfile
from app.services.wearable_service import WearableService
from app.services.meal_service import MealService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/', methods=['GET'])
@jwt_required()
def get_dashboard():
    """
    Get dashboard data for the current user
    """
    user_id = get_jwt_identity()
    
    # Get user profile
    user = User.query.get(user_id)
    if not user:
        return jsonify({
            'success': False,
            'message': 'User not found'
        }), 404
    
    profile = user.profile
    
    # Check if wearable is connected
    wearable_connected = False
    if profile and profile.wearable_connected:
        wearable_connected = True
    
    # Get latest wearable data if connected
    wearable_data = None
    if wearable_connected:
        wearable_data = WearableService.get_latest_aggregated_data(user_id)
        if wearable_data:
            # Convert ObjectId to string for JSON serialization
            wearable_data['_id'] = str(wearable_data['_id'])
    
    # Get recent meal plans (limit to 2)
    recent_meal_plans = MealService.get_user_meal_plans(user_id, limit=2)
    
    # Prepare dashboard data
    dashboard_data = {
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        },
        'profile': None,
        'wearable': {
            'connected': wearable_connected,
            'device_type': profile.wearable_type if profile and profile.wearable_type else None,
            'last_sync': profile.last_sync.isoformat() if profile and profile.last_sync else None,
            'data': wearable_data
        },
        'meal_plans': recent_meal_plans
    }
    
    # Add profile data if it exists
    if profile:
        dashboard_data['profile'] = {
            'first_name': profile.first_name,
            'last_name': profile.last_name,
            'age': profile.age,
            'gender': profile.gender,
            'weight': profile.weight,
            'height': profile.height,
            'activity_level': profile.activity_level,
            'calorie_goal': profile.calorie_goal,
            'protein_goal': profile.protein_goal,
            'carb_goal': profile.carb_goal,
            'fat_goal': profile.fat_goal,
            'meals_per_day': profile.meals_per_day,
            'preferred_cuisines': profile.preferred_cuisines.split(',') if profile.preferred_cuisines else []
        }
    
    return jsonify({
        'success': True,
        'data': dashboard_data
    }), 200