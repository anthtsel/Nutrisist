from flask import render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from .. import db
import os
import json
from datetime import datetime, timedelta
import logging
from werkzeug.utils import secure_filename
from .models import HealthInsightModel, DataType, UserProfile, RecoveryAssistant, NutritionAdvisor, MealPlanner
from .data_processor import GarminDataProcessor
from .platforms.apple_health import AppleHealthPlatform
from . import health_insights

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
    
    return render_template('health_insights/connect.html',
                         apple_connected=bool(apple_platform),
                         garmin_connected=bool(garmin_platform),
                         apple_last_sync=getattr(apple_platform, 'last_sync', None),
                         garmin_last_sync=getattr(garmin_platform, 'last_sync', None))

@health_insights.route('/connect-apple')
@login_required
def connect_apple():
    """Connect to Apple Health."""
    try:
        # For now, redirect to manual upload
        return redirect(url_for('health_insights.upload'))
    except Exception as e:
        logger.error(f"Error connecting to Apple Health: {str(e)}")
        return jsonify({'error': str(e)}), 500

@health_insights.route('/upload-apple-data', methods=['POST'])
@login_required
def upload_apple_data():
    """Handle Apple Health data file upload."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            logger.info(f"Saved file: {upload_path}")
            
            # Initialize platform with the uploaded file
            platform = AppleHealthPlatform(current_user.id, current_app.config['UPLOAD_FOLDER'])
            if platform.connect(filename):
                platforms[f'apple_{current_user.id}'] = platform
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to process Apple Health data'}), 400
            
    except Exception as e:
        logger.error(f"Error processing Apple Health data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@health_insights.route('/connect-garmin')
@login_required
def connect_garmin():
    """Connect to Garmin Connect."""
    try:
        # For now, redirect to manual upload
        return redirect(url_for('health_insights.upload'))
            
    except Exception as e:
        logger.error(f"Error connecting to Garmin Connect: {str(e)}")
        return jsonify({'error': str(e)}), 500

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
    """Manually trigger data sync for all connected platforms."""
    try:
        results = {'apple': False, 'garmin': False}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Sync Apple Health data
        apple_key = f'apple_{current_user.id}'
        if apple_key in platforms:
            apple_platform = platforms[apple_key]
            heart_rate_data = apple_platform.fetch_data(DataType.HEART_RATE, start_date, end_date)
            sleep_data = apple_platform.fetch_data(DataType.SLEEP, start_date, end_date)
            
            if heart_rate_data or sleep_data:
                # Save normalized data
                normalized_data = {
                    'heart_rate': apple_platform.normalize_data(heart_rate_data, DataType.HEART_RATE).get('heart_rate', []),
                    'sleep': apple_platform.normalize_data(sleep_data, DataType.SLEEP).get('sleep', [])
                }
                
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'apple_data.json')
                with open(save_path, 'w') as f:
                    json.dump(normalized_data, f)
                    
                results['apple'] = True
        
        # Sync Garmin data (manual upload only for now)
        garmin_key = f'garmin_{current_user.id}'
        if garmin_key in platforms:
            results['garmin'] = True
        
        return jsonify({
            'success': any(results.values()),
            'results': results
        })
            
    except Exception as e:
        logger.error(f"Error syncing data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@health_insights.route('/upload')
@login_required
def upload():
    """Show manual data upload form."""
    return render_template('health_insights/upload.html')

@health_insights.route('/upload-garmin-data', methods=['POST'])
@login_required
def upload_garmin_data():
    """Handle Garmin data file upload."""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)
            logger.info(f"Saved file: {upload_path}")
            
            # Process uploaded file
            processor = GarminDataProcessor(current_app.config['UPLOAD_FOLDER'])
            processor.process_directory()
            
            # Save processed data
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'garmin_data.json')
            with open(save_path, 'w') as f:
                json.dump(processor.processed_data, f)
                
            logger.info(f"Processed data saved to {save_path}")
            return jsonify({'success': True})
            
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        return jsonify({'error': str(e)}), 500

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