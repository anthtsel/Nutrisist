from flask import Blueprint, render_template, redirect, url_for, flash, request, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User
from app import db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        error = None
        user = User.query.filter_by(username=username).first()
        
        if user is None:
            error = 'Invalid username.'
        elif not check_password_hash(user.password_hash, password):
            error = 'Invalid password.'
            
        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('dashboard.index'))
            
        flash(error, 'error')
    
    return render_template('login.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        
        if error is None:
            try:
                user = User(
                    username=username,
                    email=email,
                    password_hash=generate_password_hash(password)
                )
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('auth.login'))
            except:
                error = 'User already exists.'
        
        flash(error, 'error')
    
    return render_template('register.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id) 