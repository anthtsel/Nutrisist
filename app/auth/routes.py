from flask import render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, RegistrationForm
from ..models import User, UserRole
from .. import db
from datetime import datetime
from .decorators import check_locked
import jwt
from time import time

def get_reset_password_token(user, expires_in=600):
    """Generate password reset token."""
    return jwt.encode(
        {'reset_password': user.id, 'exp': time() + expires_in},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_reset_password_token(token):
    """Verify password reset token."""
    try:
        id = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )['reset_password']
    except:
        return None
    return User.query.get(id)

@auth.route('/login', methods=['GET', 'POST'])
@check_locked
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            if user:
                user.record_login_attempt(success=False)
                db.session.commit()
                
                if user.is_locked():
                    flash('Account is temporarily locked due to too many failed attempts. Please try again later.', 'danger')
                    return redirect(url_for('auth.login'))
                    
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.is_active:
            flash('This account has been deactivated. Please contact support.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Successful login
        user.record_login_attempt(success=True)
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Sign In', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=UserRole.USER.value
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            token = get_reset_password_token(user)
            # TODO: Implement email sending
            # send_verification_email(user.email, token)
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'danger')
            current_app.logger.error(f"Registration error: {str(e)}")
            
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/verify/<token>')
def verify_email(token):
    """Handle email verification."""
    user = verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired verification link.', 'danger')
        return redirect(url_for('auth.login'))
        
    user.email_verified = True
    db.session.commit()
    flash('Your email has been verified! You can now log in.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Handle password reset request."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = get_reset_password_token(user)
            # TODO: Implement email sending
            # send_password_reset_email(user.email, token)
            
        flash('Check your email for instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    user = verify_reset_password_token(token)
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.failed_login_attempts = 0
        user.locked_until = None
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', title='Reset Password', form=form) 