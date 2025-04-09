from flask import render_template, request, jsonify, current_app, redirect, url_for, flash, session
from flask_login import login_required, current_user
from .. import db
import os
import json
from datetime import datetime, timedelta
import logging
from werkzeug.utils import secure_filename
from .models import HealthInsightModel, DataType, UserProfile, RecoveryAssistant, NutritionAdvisor, MealPlanner
from app.models import Device, DeviceConnection
from .platforms.apple_health import AppleHealthPlatform
from .platforms.fitbit import FitbitPlatform
from .platforms.google_fit import GoogleFitPlatform
from . import health_insights
from app.health_insights.platforms.garmin import GarminPlatform
import requests

logger = logging.getLogger(__name__)

# Platform instances
platforms = {}

# Custom template filters
@health_insights.app_template_filter('datetime')
def format_datetime(value):
    """Format datetime for display."""
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime('%Y-%m-%d %H:%M:%S')

@health_insights.route('/profile')
@login_required
def profile():
    """Show user profile page."""
    try:
        # Get user profile from database
        user_profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        return render_template('health_insights/profile.html', profile=user_profile)
    except Exception as e:
        logger.error(f"Error loading profile: {str(e)}")
        flash('Error loading profile', 'danger')
        return redirect(url_for('health_insights.dashboard'))

@health_insights.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'age', 'weight', 'height', 'gender', 'activity_level', 'goal_type', 'weekly_activity_target']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Get or create user profile
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            profile = UserProfile(user_id=current_user.id)
        
        try:
            # Update profile fields with type validation
            profile.name = str(data['name']).strip()
            profile.age = int(data['age'])
            profile.weight = float(data['weight'])
            profile.height = int(data['height'])
            profile.gender = str(data['gender'])
            profile.activity_level = str(data['activity_level'])
            profile.goal_type = str(data['goal_type'])
            profile.weekly_activity_target = float(data['weekly_activity_target'])
            profile.medical_conditions = str(data.get('medical_conditions', '')).strip()
            profile.medications = str(data.get('medications', '')).strip()
            profile.updated_at = datetime.now()
        except (ValueError, TypeError) as e:
            return jsonify({
                'success': False,
                'error': f'Invalid data format: {str(e)}'
            }), 400
        
        # Save to database
        try:
            db.session.add(profile)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully'
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error while updating profile: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to save profile changes. Please try again.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

@health_insights.route('/connect')
@login_required
def connect():
    """Show platform connection options."""
    apple_platform = platforms.get(f'apple_{current_user.id}')
    garmin_platform = platforms.get(f'garmin_{current_user.id}')
    fitbit_platform = platforms.get(f'fitbit_{current_user.id}')
    google_fit_platform = platforms.get(f'google_fit_{current_user.id}')
    
    return render_template('health_insights/connect.html',
                         apple_connected=bool(apple_platform),
                         garmin_connected=bool(garmin_platform),
                         fitbit_connected=bool(fitbit_platform),
                         google_fit_connected=bool(google_fit_platform),
                         apple_last_sync=getattr(apple_platform, 'last_sync', None),
                         garmin_last_sync=getattr(garmin_platform, 'last_sync', None),
                         fitbit_last_sync=getattr(fitbit_platform, 'last_sync', None),
                         google_fit_last_sync=getattr(google_fit_platform, 'last_sync', None))

@health_insights.route('/connect-apple')
@login_required
def connect_apple():
    """Connect to Apple Health."""
    try:
        platform = AppleHealthPlatform(current_user.id)
        if platform.connect():
            platforms[f'apple_{current_user.id}'] = platform
            return redirect(url_for('health_insights.connect'))
        else:
            flash('Failed to connect to Apple Health', 'danger')
            return redirect(url_for('health_insights.connect'))
    except Exception as e:
        logger.error(f"Error connecting to Apple Health: {str(e)}")
        flash('Error connecting to Apple Health', 'danger')
        return redirect(url_for('health_insights.connect'))

@health_insights.route('/connect-garmin')
@login_required
def connect_garmin():
    """Connect to Garmin using OAuth."""
    garmin = GarminPlatform(current_user.id)
    
    # Get request token
    response = requests.post(
        garmin.request_token_url,
        auth=(current_app.config['GARMIN_CLIENT_ID'], current_app.config['GARMIN_CLIENT_SECRET'])
    )
    
    if response.status_code == 200:
        request_token = response.text.split('&')[0].split('=')[1]
        session['garmin_request_token'] = request_token
        
        # Redirect to Garmin authorization page
        auth_url = f"{garmin.authorize_url}?oauth_token={request_token}"
        return redirect(auth_url)
    
    flash('Failed to connect to Garmin. Please try again.', 'error')
    return redirect(url_for('health_insights.connect'))

@health_insights.route('/connect-fitbit')
@login_required
def connect_fitbit():
    """Connect to Fitbit."""
    try:
        platform = FitbitPlatform(current_user.id)
        if platform.connect():
            platforms[f'fitbit_{current_user.id}'] = platform
            return redirect(url_for('health_insights.connect'))
        else:
            flash('Failed to connect to Fitbit', 'danger')
            return redirect(url_for('health_insights.connect'))
    except Exception as e:
        logger.error(f"Error connecting to Fitbit: {str(e)}")
        flash('Error connecting to Fitbit', 'danger')
        return redirect(url_for('health_insights.connect'))

@health_insights.route('/connect-google-fit')
@login_required
def connect_google_fit():
    """Connect to Google Fit."""
    try:
        platform = GoogleFitPlatform(current_user.id)
        if platform.connect():
            platforms[f'google_fit_{current_user.id}'] = platform
            return redirect(url_for('health_insights.connect'))
        else:
            flash('Failed to connect to Google Fit', 'danger')
            return redirect(url_for('health_insights.connect'))
    except Exception as e:
        logger.error(f"Error connecting to Google Fit: {str(e)}")
        flash('Error connecting to Google Fit', 'danger')
        return redirect(url_for('health_insights.connect'))

@health_insights.route('/disconnect/<platform>', methods=['POST'])
@login_required
def disconnect_platform(platform):
    """Disconnect from a health platform."""
    try:
        platform_key = f'{platform}_{current_user.id}'
        if platform_key in platforms:
            platform_instance = platforms[platform_key]
            if platform_instance.disconnect():
                del platforms[platform_key]
                return jsonify({'success': True})
                
        return jsonify({'error': 'Platform not connected'}), 400
            
    except Exception as e:
        logger.error(f"Error disconnecting from {platform}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@health_insights.route('/update-sync-settings', methods=['POST'])
@login_required
def update_sync_settings():
    """Update platform sync settings."""
    try:
        data = request.get_json()
        interval = data.get('interval', 6)
        auto_sync = data.get('autoSync', True)
        
        # Update settings for all connected platforms
        for platform_key, platform in platforms.items():
            if platform_key.endswith(str(current_user.id)):
                platform.sync_interval = interval
                platform.auto_sync = auto_sync
                
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating sync settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@health_insights.route('/sync-now', methods=['POST'])
@login_required
def sync_now():
    """Trigger immediate sync for all connected platforms."""
    try:
        success = True
        for platform_key, platform in platforms.items():
            if platform_key.endswith(str(current_user.id)):
                if not platform.sync():
                    success = False
                    logger.error(f"Failed to sync platform: {platform_key}")
                    
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Some platforms failed to sync'}), 500
            
    except Exception as e:
        logger.error(f"Error during sync: {str(e)}")
        return jsonify({'error': str(e)}), 500

@health_insights.route('/upload')
@login_required
def upload():
    """Show manual data upload form."""
    return render_template('health_insights/upload.html')

@health_insights.route('/garmin/callback')
@login_required
def garmin_callback():
    """Handle Garmin OAuth callback."""
    oauth_token = request.args.get('oauth_token')
    oauth_verifier = request.args.get('oauth_verifier')
    
    if not oauth_token or not oauth_verifier:
        flash('Invalid Garmin callback parameters.', 'error')
        return redirect(url_for('health_insights.connect'))
    
    garmin = GarminPlatform(current_user.id)
    
    # Exchange request token for access token
    data = {
        'oauth_token': oauth_token,
        'oauth_verifier': oauth_verifier
    }
    
    response = requests.post(
        garmin.token_url,
        auth=(current_app.config['GARMIN_CLIENT_ID'], current_app.config['GARMIN_CLIENT_SECRET']),
        data=data
    )
    
    if response.status_code == 200:
        token_data = response.json()
        
        # Update user with Garmin tokens
        current_user.garmin_access_token = token_data['access_token']
        current_user.garmin_refresh_token = token_data['refresh_token']
        current_user.garmin_token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        current_user.garmin_connected = True
        
        # Create or update device entry
        device = Device.query.filter_by(
            user_id=current_user.id,
            platform='garmin'
        ).first()
        
        if not device:
            device = Device(
                user_id=current_user.id,
                platform='garmin',
                device_name='Garmin Connect',
                last_sync=datetime.utcnow()
            )
            db.session.add(device)
        
        db.session.commit()
        flash('Successfully connected to Garmin!', 'success')
    else:
        flash('Failed to connect to Garmin. Please try again.', 'error')
    
    return redirect(url_for('health_insights.connect'))

@health_insights.route('/dashboard')
@login_required
def dashboard():
    """Show health insights dashboard."""
    return render_template('health_insights/dashboard.html')

@health_insights.route('/analyze')
@login_required
def analyze():
    """Show health data analysis."""
    try:
        # Get user profile
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            return render_template('health_insights/analyze.html', 
                                error="Please complete your profile first to get personalized insights.")

        # Initialize health insight model
        insight_model = HealthInsightModel()
        
        # Get data from connected platforms
        apple_data = {}
        garmin_data = {}
        
        apple_platform = platforms.get(f'apple_{current_user.id}')
        if apple_platform:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            apple_data = {
                'heart_rate': apple_platform.fetch_data(DataType.HEART_RATE, start_date, end_date),
                'sleep': apple_platform.fetch_data(DataType.SLEEP, start_date, end_date)
            }
            
        garmin_platform = platforms.get(f'garmin_{current_user.id}')
        if garmin_platform:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            garmin_data = {
                'heart_rate': garmin_platform.fetch_data(DataType.HEART_RATE, start_date, end_date),
                'sleep': garmin_platform.fetch_data(DataType.SLEEP, start_date, end_date)
            }

        # Generate insights
        insights = {
            'heart_rate': insight_model.analyze_heart_rate(apple_data.get('heart_rate', []) + garmin_data.get('heart_rate', [])),
            'sleep': insight_model.analyze_sleep(apple_data.get('sleep', []) + garmin_data.get('sleep', [])),
            'recovery': insight_model.analyze_recovery(profile),
            'nutrition': insight_model.analyze_nutrition(profile)
        }

        return render_template('health_insights/analyze.html', insights=insights)
        
    except Exception as e:
        logger.error(f"Error generating health insights: {str(e)}")
        return render_template('health_insights/analyze.html', 
                             error="An error occurred while generating your health insights. Please try again later.")

@health_insights.route('/alerts')
@login_required
def alerts():
    """Show health alerts."""
    return render_template('health_insights/alerts.html')

@health_insights.route('/recovery-status')
@login_required
def recovery_status():
    """Get personalized recovery status and recommendations."""
    try:
        # Get user's recent sleep and HRV data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Get data from connected platforms
        sleep_data = []
        hrv_data = []
        
        # Fetch from Apple Health if connected
        apple_platform = platforms.get(f'apple_{current_user.id}')
        if apple_platform:
            sleep_data.extend(apple_platform.fetch_data(DataType.SLEEP, start_date, end_date))
            hrv_data.extend(apple_platform.fetch_data(DataType.HEART_RATE, start_date, end_date))
            
        # Fetch from Garmin if connected
        garmin_platform = platforms.get(f'garmin_{current_user.id}')
        if garmin_platform:
            sleep_data.extend(garmin_platform.fetch_data(DataType.SLEEP, start_date, end_date))
            hrv_data.extend(garmin_platform.fetch_data(DataType.HEART_RATE, start_date, end_date))
        
        # Calculate average scores
        sleep_scores = [data.get('sleep_score', 0) for data in sleep_data if isinstance(data, dict)]
        hrv_scores = [data.get('hrv_score', 0) for data in hrv_data if isinstance(data, dict)]
        
        current_sleep_score = sleep_scores[-1] if sleep_scores else 0
        current_hrv_score = hrv_scores[-1] if hrv_scores else 0
        
        user_data = {
            'sleep_score': current_sleep_score,
            'hrv_score': current_hrv_score,
            'user_averages': {
                'sleep_score': sum(sleep_scores) / len(sleep_scores) if sleep_scores else 0,
                'hrv_score': sum(hrv_scores) / len(hrv_scores) if hrv_scores else 0
            }
        }
        
        # Get recovery recommendations
        recovery_assistant = RecoveryAssistant()
        recovery_status = recovery_assistant.analyze_recovery_status(user_data)
        
        return jsonify({
            'status': 'success',
            'data': recovery_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in recovery status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to analyze recovery status'
        }), 500

@health_insights.route('/nutrition-advice')
@login_required
def nutrition_advice():
    """Get personalized nutrition advice."""
    try:
        # Get user profile and activity data
        profile = UserProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            return jsonify({
                'status': 'error',
                'message': 'Please complete your profile first'
            }), 400
        
        # Get recent activity data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        calories_burned = 0
        # Fetch from connected platforms
        for platform_id in ['apple', 'garmin']:
            platform = platforms.get(f'{platform_id}_{current_user.id}')
            if platform:
                activity_data = platform.fetch_data(DataType.ACTIVITY, start_date, end_date)
                calories_burned += sum(
                    activity.get('calories_burned', 0) 
                    for activity in activity_data 
                    if isinstance(activity, dict)
                )
        
        # Average daily calories burned
        avg_daily_calories_burned = calories_burned / 7
        
        # Prepare user data for nutrition advisor
        user_data = {
            'weight': profile.weight,
            'height': profile.height,
            'age': profile.age,
            'gender': profile.gender,
            'activity_level': profile.activity_level,
            'goal': profile.goal_type,
            'calories_burned': avg_daily_calories_burned
        }
        
        # Get nutrition recommendations
        nutrition_advisor = NutritionAdvisor()
        nutrition_advice = nutrition_advisor.calculate_nutrition_needs(user_data)
        
        return jsonify({
            'status': 'success',
            'data': nutrition_advice
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in nutrition advice: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate nutrition advice'
        }), 500

@health_insights.route('/meal-plan', methods=['POST'])
@login_required
def generate_meal_plan():
    """Generate a personalized meal plan."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
            
        # Get user's nutrition needs
        nutrition_response = nutrition_advice()
        if isinstance(nutrition_response, tuple):
            nutrition_response = nutrition_response[0]
            
        if nutrition_response.status_code != 200:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get nutrition advice'
            }), 500
            
        nutrition_data = nutrition_response.get_json()
        if nutrition_data['status'] != 'success':
            return jsonify({
                'status': 'error',
                'message': nutrition_data.get('message', 'Failed to get nutrition advice')
            }), 500
            
        # Get user preferences from request
        preferences = {
            'dietary_type': data.get('dietary_type', 'balanced'),
            'excluded_foods': data.get('excluded_foods', []),
            'meal_count': data.get('meal_count', 4),
            'servings': data.get('servings', 1)
        }
        
        # Generate meal plan
        meal_planner = MealPlanner()
        meal_plan = meal_planner.generate_meal_plan(
            nutrition_data['data'],
            preferences
        )
        
        if not meal_plan:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate meal plan'
            }), 500
        
        # Generate shopping links
        shopping_links = meal_planner.generate_shopping_links(meal_plan['grocery_list'])
        
        # Save meal plan to database
        try:
            meal_service = MealService()
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=6)
            
            # Create meal plan in database
            db_meal_plan = meal_service.create_meal_plan(
                user_id=current_user.id,
                name=f"Weekly Meal Plan - {start_date.strftime('%Y-%m-%d')}",
                start_date=start_date,
                end_date=end_date,
                description="Generated meal plan based on nutrition needs and preferences"
            )
            
            # Add meals to the plan
            for day, meals in meal_plan['weekly_plan'].items():
                day_of_week = int(day.split('_')[1]) - 1  # Convert to 0-6 for Monday-Sunday
                for meal_type, meal in meals.items():
                    db_meal = meal_service.add_meal_to_plan(
                        meal_plan_id=db_meal_plan.id,
                        day_of_week=day_of_week,
                        meal_type=meal_type,
                        name=meal['name'],
                        description="\n".join(meal['instructions']),
                        calories=meal['calories'],
                        protein=meal['macros']['protein']['grams'],
                        carbs=meal['macros']['carbs']['grams'],
                        fat=meal['macros']['fat']['grams']
                    )
                    
                    # Add ingredients to the meal
                    for ingredient in meal['ingredients']:
                        meal_service.add_ingredient_to_meal(
                            meal_id=db_meal.id,
                            name=ingredient['name'],
                            quantity=ingredient['amount'],
                            unit=ingredient['unit']
                        )
        except Exception as e:
            current_app.logger.error(f"Error saving meal plan to database: {str(e)}")
            # Continue with response even if database save fails
        
        return jsonify({
            'status': 'success',
            'data': {
                'meal_plan': meal_plan['weekly_plan'],
                'grocery_list': meal_plan['grocery_list'],
                'prep_schedule': meal_plan['prep_schedule'],
                'shopping_links': shopping_links
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating meal plan: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to generate meal plan'
        }), 500

@health_insights.route('/meal-plan')
@login_required
def meal_plan():
    """Show meal plan page."""
    return render_template('health_insights/meal_plan.html')

@health_insights.route('/recovery')
@login_required
def recovery():
    """Show recovery page."""
    return render_template('health_insights/recovery.html') 