from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func
from app import db, mongo
from app.models.models import User, UserProfile, MealPlan, Meal, Ingredient, DietaryRestriction
from app.services.wearable_service import WearableService

class MealService:
    """Service for generating and managing meal plans based on wearable data"""
    
    @staticmethod
    def generate_meal_plan(user_id, days=7, name=None):
        """
        Generate a personalized meal plan based on wearable data
        
        Args:
            user_id: The user ID
            days: Number of days for the meal plan (default: 7)
            name: Optional name for the meal plan
            
        Returns:
            MealPlan: The generated meal plan or None if failed
        """
        try:
            # Get user profile
            user_profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not user_profile:
                return None
                
            # Check if wearable is connected
            if not user_profile.wearable_connected:
                return None
                
            # Get latest aggregated wearable data
            wearable_data = WearableService.get_latest_aggregated_data(user_id)
            if not wearable_data:
                # If no wearable data, try to sync and get data
                success = WearableService.sync_wearable_data(user_id)
                if success:
                    wearable_data = WearableService.get_latest_aggregated_data(user_id)
                
                if not wearable_data:
                    return None
            
            # Get dietary restrictions
            restrictions = [r.id for r in user_profile.dietary_restrictions]
            
            # Calculate meal plan parameters
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=days-1)
            
            # Use recommendations from wearable data or fall back to profile goals
            daily_calories = wearable_data.get("recommended_calories", user_profile.calorie_goal)
            protein_target = wearable_data.get("recommended_macros", {}).get("protein", user_profile.protein_goal)
            carbs_target = wearable_data.get("recommended_macros", {}).get("carbs", user_profile.carb_goal)
            fat_target = wearable_data.get("recommended_macros", {}).get("fat", user_profile.fat_goal)
            
            # Create meal plan
            plan_name = name or f"Meal Plan {start_date.strftime('%Y-%m-%d')}"
            new_plan = MealPlan(
                user_id=user_id,
                name=plan_name,
                start_date=start_date,
                end_date=end_date,
                total_calories=daily_calories * days,
                total_protein=protein_target * days,
                total_carbs=carbs_target * days,
                total_fat=fat_target * days,
                avg_daily_calories_burned=wearable_data.get("avg_daily_calories_burned"),
                avg_daily_steps=wearable_data.get("avg_daily_steps"),
                avg_sleep_duration=wearable_data.get("avg_sleep_duration")
            )
            
            db.session.add(new_plan)
            db.session.flush()  # Get the ID without committing
            
            # Get meals per day from user profile
            meals_per_day = user_profile.meals_per_day or 3
            
            # Determine meal distribution
            meal_distribution = MealService._get_meal_distribution(meals_per_day, daily_calories)
            
            # Get preferred cuisines
            preferred_cuisines = []
            if user_profile.preferred_cuisines:
                preferred_cuisines = user_profile.preferred_cuisines.split(',')
            
            # Generate meals for each day
            for day in range(days):
                day_of_week = (start_date + timedelta(days=day)).weekday()  # 0-6 (Monday-Sunday)
                
                # Generate meals for each meal time
                for meal_time, meal_info in meal_distribution.items():
                    # Calculate target calories for this meal
                    target_calories = int(daily_calories * meal_info["calorie_percent"])
                    
                    # Find suitable meals
                    meals_query = db.session.query(Meal).filter(
                        Meal.calories.between(target_calories * 0.9, target_calories * 1.1),
                        Meal.meal_type == meal_time
                    )
                    
                    # Apply cuisine preferences if available
                    if preferred_cuisines:
                        meals_query = meals_query.filter(Meal.cuisine.in_(preferred_cuisines))
                    
                    # Apply dietary restrictions
                    if restrictions:
                        # This is a simplified approach - in reality, you'd need a more complex query
                        # to filter out meals that contain ingredients with restricted properties
                        pass
                    
                    # Get top matching meals ordered by highest rating
                    top_meals = meals_query.order_by(Meal.avg_rating.desc()).limit(10).all()
                    
                    # If no meals found, relax calorie constraints
                    if not top_meals:
                        top_meals = db.session.query(Meal).filter(
                            Meal.calories.between(target_calories * 0.8, target_calories * 1.2),
                            Meal.meal_type == meal_time
                        ).order_by(Meal.avg_rating.desc()).limit(5).all()
                    
                    # Select a meal (in a real app, you'd implement a more sophisticated algorithm)
                    selected_meal = None
                    if top_meals:
                        selected_meal = top_meals[day % len(top_meals)]  # Simple rotation for variety
                    
                    # If no suitable meal found, skip
                    if not selected_meal:
                        continue
                    
                    # Add meal to plan
                    stmt = meal_plan_meals.insert().values(
                        meal_plan_id=new_plan.id,
                        meal_id=selected_meal.id,
                        meal_time=meal_time,
                        day_of_week=day_of_week
                    )
                    db.session.execute(stmt)
            
            # Commit the transaction
            db.session.commit()
            
            return new_plan
            
        except Exception as e:
            current_app.logger.error(f"Error generating meal plan: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def _get_meal_distribution(meals_per_day, total_calories):
        """
        Get the distribution of calories across different meals
        
        Args:
            meals_per_day: Number of meals per day
            total_calories: Total daily calories
            
        Returns:
            dict: Meal distribution with calorie percentages
        """
        if meals_per_day == 3:
            return {
                "breakfast": {"calorie_percent": 0.25},
                "lunch": {"calorie_percent": 0.35},
                "dinner": {"calorie_percent": 0.4}
            }
        elif meals_per_day == 4:
            return {
                "breakfast": {"calorie_percent": 0.25},
                "lunch": {"calorie_percent": 0.3},
                "snack": {"calorie_percent": 0.15},
                "dinner": {"calorie_percent": 0.3}
            }
        elif meals_per_day == 5:
            return {
                "breakfast": {"calorie_percent": 0.2},
                "morning_snack": {"calorie_percent": 0.1},
                "lunch": {"calorie_percent": 0.3},
                "afternoon_snack": {"calorie_percent": 0.1},
                "dinner": {"calorie_percent": 0.3}
            }
        else:
            # Default to 3 meals
            return {
                "breakfast": {"calorie_percent": 0.25},
                "lunch": {"calorie_percent": 0.35},
                "dinner": {"calorie_percent": 0.4}
            }
    
    @staticmethod
    def get_meal_plan(meal_plan_id, user_id=None):
        """
        Get a meal plan with its associated meals
        
        Args:
            meal_plan_id: The meal plan ID
            user_id: Optional user ID for validation
            
        Returns:
            dict: Meal plan with structured meal data
        """
        try:
            # Get meal plan
            query = db.session.query(MealPlan)
            if user_id:
                query = query.filter_by(id=meal_plan_id, user_id=user_id)
            else:
                query = query.filter_by(id=meal_plan_id)
                
            meal_plan = query.first()
            if not meal_plan:
                return None
            
            # Query all meals for this plan with their meal time and day
            meal_data = db.session.query(
                Meal, 
                meal_plan_meals.c.meal_time,
                meal_plan_meals.c.day_of_week
            ).join(
                meal_plan_meals, 
                meal_plan_meals.c.meal_id == Meal.id
            ).filter(
                meal_plan_meals.c.meal_plan_id == meal_plan_id
            ).all()
            
            # Structure by day and meal time
            days = {}
            for meal, meal_time, day_of_week in meal_data:
                if day_of_week not in days:
                    days[day_of_week] = {}
                
                days[day_of_week][meal_time] = {
                    "id": meal.id,
                    "name": meal.name,
                    "description": meal.description,
                    "calories": meal.calories,
                    "protein": meal.protein,
                    "carbs": meal.carbs,
                    "fat": meal.fat,
                    "meal_type": meal.meal_type,
                    "cuisine": meal.cuisine
                }
            
            # Convert meal plan to dict for JSON serialization
            result = {
                "id": meal_plan.id,
                "user_id": meal_plan.user_id,
                "name": meal_plan.name,
                "start_date": meal_plan.start_date.isoformat(),
                "end_date": meal_plan.end_date.isoformat(),
                "total_calories": meal_plan.total_calories,
                "total_protein": meal_plan.total_protein,
                "total_carbs": meal_plan.total_carbs,
                "total_fat": meal_plan.total_fat,
                "avg_daily_calories_burned": meal_plan.avg_daily_calories_burned,
                "avg_daily_steps": meal_plan.avg_daily_steps,
                "avg_sleep_duration": meal_plan.avg_sleep_duration,
                "days": days
            }
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error getting meal plan: {str(e)}")
            return None
    
    @staticmethod
    def get_user_meal_plans(user_id, limit=10):
        """
        Get all meal plans for a user
        
        Args:
            user_id: The user ID
            limit: Maximum number of plans to return
            
        Returns:
            list: List of meal plans
        """
        try:
            # Query meal plans for user, ordered by creation date
            meal_plans = db.session.query(MealPlan).filter_by(
                user_id=user_id
            ).order_by(
                MealPlan.created_at.desc()
            ).limit(limit).all()
            
            # Convert to list of dicts
            result = []
            for plan in meal_plans:
                result.append({
                    "id": plan.id,
                    "name": plan.name,
                    "start_date": plan.start_date.isoformat(),
                    "end_date": plan.end_date.isoformat(),
                    "created_at": plan.created_at.isoformat(),
                    "total_calories": plan.total_calories
                })
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error getting user meal plans: {str(e)}")
            return []