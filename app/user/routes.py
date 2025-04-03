from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.user import bp
from app.models import User, HealthMetric
from app import db
from datetime import datetime

@bp.route('/profile')
@login_required
def profile():
    return render_template('user/profile.html', user=current_user)

@bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form['username']
        current_user.email = request.form['email']
        
        if request.form['new_password']:
            current_user.set_password(request.form['new_password'])
        
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('user.profile'))
    
    return render_template('user/edit_profile.html', user=current_user)

@bp.route('/profile/health/edit', methods=['GET', 'POST'])
@login_required
def edit_health_info():
    if request.method == 'POST':
        current_user.age = request.form.get('age', type=int)
        current_user.gender = request.form.get('gender')
        current_user.height = request.form.get('height', type=float)
        current_user.weight = request.form.get('weight', type=float)
        current_user.activity_level = request.form.get('activity_level')
        current_user.health_goals = request.form.get('health_goals')
        
        db.session.commit()
        flash('Your health information has been updated.')
        return redirect(url_for('user.profile'))
    
    return render_template('user/edit_health_info.html', user=current_user)

@bp.route('/health-metrics')
@login_required
def health_metrics():
    metrics = HealthMetric.query.filter_by(user_id=current_user.id).order_by(HealthMetric.date.desc()).all()
    return render_template('user/health_metrics.html', metrics=metrics)

@bp.route('/health-metrics/add', methods=['GET', 'POST'])
@login_required
def add_health_metric():
    if request.method == 'POST':
        metric = HealthMetric(
            user_id=current_user.id,
            weight=request.form.get('weight', type=float),
            body_fat_percentage=request.form.get('body_fat_percentage', type=float),
            muscle_mass_percentage=request.form.get('muscle_mass_percentage', type=float),
            bmi=request.form.get('bmi', type=float),
            notes=request.form.get('notes')
        )
        
        db.session.add(metric)
        db.session.commit()
        flash('Health metric has been recorded.')
        return redirect(url_for('user.health_metrics'))
    
    return render_template('user/add_health_metric.html') 