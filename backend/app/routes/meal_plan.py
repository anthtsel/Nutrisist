from flask import Blueprint, render_template, session, request, jsonify
from app.models import User, MealPlan
from app.services.meal_generator import generate_meal_plan
from functools import wraps

bp = Blueprint('meal_plan', __name__, url_prefix='/meal-plan')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    user = User.query.get(session['user_id'])
    meal_plans = MealPlan.query.filter_by(user_id=user.id).all()
    return render_template('meal_plan.html', meal_plans=meal_plans)

@bp.route('/generate', methods=['POST'])
@login_required
def generate():
    user = User.query.get(session['user_id'])
    preferences = request.json.get('preferences', {})
    new_plan = generate_meal_plan(user.id, preferences)
    return jsonify(new_plan) 