from flask import render_template, jsonify, current_app
from flask_login import login_required, current_user
from app.health_insights import bp
from app.health_insights.models import HealthInsightModel
from app.garmin.routes import get_garmin_data
import logging

logger = logging.getLogger(__name__)

@bp.route('/dashboard')
@login_required
def insights_dashboard():
    return render_template('health_insights/dashboard.html')

@bp.route('/analyze')
@login_required
def analyze_health():
    try:
        # Initialize the health insight model
        model = HealthInsightModel()
        
        # Get Garmin data
        garmin_response = get_garmin_data()
        if garmin_response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch Garmin data'
            }), 400
            
        garmin_data = garmin_response.get_json()['data']
        
        # Prepare user profile data
        user_profile = {
            'age': current_user.age,
            'gender': current_user.gender,
            'height': current_user.height,
            'weight': current_user.weight,
            'activity_level': current_user.activity_level,
            'health_goals': current_user.health_goals
        }
        
        # Analyze heart rate
        heart_rate_insights = model.analyze_heart_rate(
            garmin_data['heart_rate'],
            user_profile
        )
        
        # Analyze sleep quality
        sleep_insights = model.analyze_sleep_quality(
            garmin_data['sleep'],
            garmin_data['steps']
        )
        
        # Analyze recovery
        recovery_insights = model.analyze_recovery(
            garmin_data['steps'],
            garmin_data['sleep'],
            garmin_data['heart_rate']
        )
        
        # Calculate nutrition needs
        nutrition_needs = model.calculate_nutrition_needs(
            garmin_data['steps'],
            user_profile
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'heart_rate': heart_rate_insights,
                'sleep': sleep_insights,
                'recovery': recovery_insights,
                'nutrition': nutrition_needs
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing health data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error analyzing health data: {str(e)}'
        }), 400

@bp.route('/alerts')
@login_required
def get_alerts():
    try:
        # Initialize the health insight model
        model = HealthInsightModel()
        
        # Get Garmin data
        garmin_response = get_garmin_data()
        if garmin_response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch Garmin data'
            }), 400
            
        garmin_data = garmin_response.get_json()['data']
        
        # Prepare user profile data
        user_profile = {
            'age': current_user.age,
            'gender': current_user.gender,
            'height': current_user.height,
            'weight': current_user.weight,
            'activity_level': current_user.activity_level,
            'health_goals': current_user.health_goals
        }
        
        # Analyze heart rate for alerts
        heart_rate_insights = model.analyze_heart_rate(
            garmin_data['heart_rate'],
            user_profile
        )
        
        # Analyze sleep quality for alerts
        sleep_insights = model.analyze_sleep_quality(
            garmin_data['sleep'],
            garmin_data['steps']
        )
        
        # Generate alerts based on insights
        alerts = []
        
        # Heart rate alerts
        if heart_rate_insights['status'] == 'high':
            alerts.append({
                'type': 'heart_rate',
                'severity': 'high',
                'message': 'Your heart rate is significantly elevated. Consider taking a break.',
                'recommendations': heart_rate_insights['recommendations']
            })
        elif heart_rate_insights['status'] == 'elevated':
            alerts.append({
                'type': 'heart_rate',
                'severity': 'moderate',
                'message': 'Your heart rate is elevated. Monitor your activity level.',
                'recommendations': heart_rate_insights['recommendations']
            })
        
        # Sleep quality alerts
        if sleep_insights['status'] == 'poor':
            alerts.append({
                'type': 'sleep',
                'severity': 'high',
                'message': 'Your sleep quality was poor. Consider improving your sleep hygiene.',
                'recommendations': sleep_insights['recommendations']
            })
        elif sleep_insights['status'] == 'fair':
            alerts.append({
                'type': 'sleep',
                'severity': 'moderate',
                'message': 'Your sleep quality was fair. Try to improve your sleep habits.',
                'recommendations': sleep_insights['recommendations']
            })
        
        return jsonify({
            'status': 'success',
            'alerts': alerts
        })
        
    except Exception as e:
        logger.error(f"Error generating alerts: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error generating alerts: {str(e)}'
        }), 400 