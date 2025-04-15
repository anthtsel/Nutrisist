from flask import Blueprint, jsonify
from flask_login import login_required

meal_plan_bp = Blueprint('meal_plan', __name__)

@meal_plan_bp.route('/')
@login_required
def get_meal_plans():
    return jsonify({"message": "Meal plans feature coming soon"}) 