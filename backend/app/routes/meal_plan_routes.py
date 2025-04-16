from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.meal_service import MealService
from flask_login import login_required, current_user
from app.models import db, User, MealPlan, ActivityData
from datetime import datetime, timedelta
import requests
import json

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

@meal_plan_bp.route('/api/meal-plans/generate', methods=['POST'])
@login_required
def generate_meal_plan():
    try:
        data = request.get_json()
        dietary_restrictions = data.get('dietary_restrictions', [])
        meal_frequency = data.get('meal_frequency', 3)
        calorie_goal = data.get('calorie_goal')

        if not calorie_goal:
            return jsonify({'error': 'Calorie goal is required'}), 400

        # Get user's activity data
        activity_data = get_user_activity_data()
        if not activity_data:
            return jsonify({'error': 'Failed to fetch activity data'}), 500

        # Calculate adjusted calorie goal based on activity
        adjusted_calories = calculate_adjusted_calories(calorie_goal, activity_data)

        # Generate meal plan using AI service
        meal_plan_data = generate_ai_meal_plan(
            adjusted_calories,
            dietary_restrictions,
            meal_frequency
        )

        if not meal_plan_data:
            return jsonify({'error': 'Failed to generate meal plan'}), 500

        # Save meal plan to database
        new_meal_plan = MealPlan(
            user_id=current_user.id,
            calories=adjusted_calories,
            meal_frequency=meal_frequency,
            dietary_restrictions=json.dumps(dietary_restrictions),
            meals=json.dumps(meal_plan_data['meals']),
            generated_at=datetime.utcnow()
        )
        db.session.add(new_meal_plan)
        db.session.commit()

        return jsonify({
            'message': 'Meal plan generated successfully',
            'meal_plan': {
                'id': new_meal_plan.id,
                'calories': adjusted_calories,
                'meal_frequency': meal_frequency,
                'dietary_restrictions': dietary_restrictions,
                'meals': meal_plan_data['meals']
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error generating meal plan: {str(e)}')
        return jsonify({'error': 'Failed to generate meal plan'}), 500

@meal_plan_bp.route('/api/meal-plans/current', methods=['GET'])
@login_required
def get_current_meal_plan():
    try:
        # Get the most recent meal plan
        meal_plan = MealPlan.query.filter_by(
            user_id=current_user.id
        ).order_by(MealPlan.generated_at.desc()).first()

        if not meal_plan:
            return jsonify({'error': 'No meal plan found'}), 404

        return jsonify({
            'id': meal_plan.id,
            'calories': meal_plan.calories,
            'meal_frequency': meal_plan.meal_frequency,
            'dietary_restrictions': json.loads(meal_plan.dietary_restrictions),
            'meals': json.loads(meal_plan.meals),
            'generated_at': meal_plan.generated_at.isoformat()
        }), 200

    except Exception as e:
        current_app.logger.error(f'Error fetching meal plan: {str(e)}')
        return jsonify({'error': 'Failed to fetch meal plan'}), 500

def get_user_activity_data():
    """Get user's recent activity data"""
    try:
        # Get activity data for the past week
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=6)

        activities = ActivityData.query.filter(
            ActivityData.user_id == current_user.id,
            ActivityData.date >= start_date,
            ActivityData.date <= end_date
        ).all()

        if not activities:
            return None

        # Calculate average daily activity
        total_steps = sum(activity.steps for activity in activities)
        total_calories = sum(activity.calories for activity in activities)
        avg_steps = total_steps / len(activities)
        avg_calories = total_calories / len(activities)

        return {
            'avg_steps': avg_steps,
            'avg_calories': avg_calories
        }

    except Exception as e:
        current_app.logger.error(f'Error getting activity data: {str(e)}')
        return None

def calculate_adjusted_calories(base_calories, activity_data):
    """Adjust calorie goal based on activity level"""
    try:
        # Calculate activity multiplier based on steps
        steps = activity_data['avg_steps']
        if steps < 5000:
            multiplier = 1.0  # Sedentary
        elif steps < 10000:
            multiplier = 1.2  # Lightly active
        elif steps < 15000:
            multiplier = 1.4  # Moderately active
        else:
            multiplier = 1.6  # Very active

        # Adjust calories
        adjusted_calories = base_calories * multiplier
        return round(adjusted_calories)

    except Exception as e:
        current_app.logger.error(f'Error calculating adjusted calories: {str(e)}')
        return base_calories

def generate_ai_meal_plan(calories, dietary_restrictions, meal_frequency):
    """Generate meal plan using AI service"""
    try:
        # TODO: Implement actual AI service integration
        # This is a placeholder implementation
        meals = []
        calories_per_meal = calories / meal_frequency

        for i in range(meal_frequency):
            meal = {
                'name': f'Meal {i+1}',
                'calories': round(calories_per_meal),
                'ingredients': ['Ingredient 1', 'Ingredient 2', 'Ingredient 3'],
                'instructions': 'Sample cooking instructions',
                'dietary_tags': dietary_restrictions
            }
            meals.append(meal)

        return {
            'meals': meals,
            'total_calories': calories
        }

    except Exception as e:
        current_app.logger.error(f'Error generating AI meal plan: {str(e)}')
        return None