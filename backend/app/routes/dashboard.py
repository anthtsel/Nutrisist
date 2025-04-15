from flask import Blueprint, render_template, session, redirect, url_for
from app.models import User, MealPlan
from functools import wraps

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

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
    return render_template('dashboard.html', user=user)

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@bp.route('/meal-plan')
def meal_plan():
    return render_template('meal_plan.html') 