from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.meal_service import MealService

meal_plan_bp = Blueprint('meal_plan', __name__)

@meal_plan_bp.route('/', methods=['GET'])
@jwt_required()
def get_meal_plans():
    """
    Get all meal plans for the current user
    """
    user_id = get_jwt_identity()
    
    # Get limit from query params, default to 10
    limit = request.args.get('limit', 10, type=int)
    
    # Get meal plans
    meal_plans = MealService.get_user_meal_plans(user_id, limit)
    
    return jsonify({
        'success': True,
        'data': meal_plans
    }), 200

@meal_plan_bp.route('/<int:meal_plan_id>', methods=['GET'])
@jwt_required()
def get_meal_plan(meal_plan_id):
    """
    Get a specific meal plan with its meals
    """
    user_id = get_jwt_identity()
    
    # Get meal plan
    meal_plan = MealService.get_meal_plan(meal_plan_id, user_id)
    
    if meal_plan:
        return jsonify({
            'success': True,
            'data': meal_plan
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Meal plan not found'
        }), 404

@meal_plan_bp.route('/', methods=['POST'])
@jwt_required()
def create_meal_plan():
    """
    Generate a new meal plan
    """
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # Get parameters
    days = data.get('days', 7)
    name = data.get('name')
    
    # Generate meal plan
    meal_plan = MealService.generate_meal_plan(user_id, days, name)
    
    if meal_plan:
        return jsonify({
            'success': True,
            'message': 'Meal plan generated successfully',
            'meal_plan_id': meal_plan.id
        }), 201
    else:
        return jsonify({
            'success': False,
            'message': 'Failed to generate meal plan'
        }), 500