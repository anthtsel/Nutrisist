from datetime import datetime, timedelta
from typing import Dict, Any, List
from app.models.meal_plans import MealPlan, Meal, MealIngredient
from app.models.alerts import AlertStore, MealTracking
from app import db

class MealService:
    """Service for handling meal plans and alerts."""
    
    def __init__(self):
        self.alert_store = AlertStore()
        self.meal_tracking = MealTracking()
    
    def create_meal_plan(self, user_id: int, name: str,
                        start_date: datetime, end_date: datetime,
                        description: str = None) -> MealPlan:
        """Create a new meal plan."""
        meal_plan = MealPlan(
            user_id=user_id,
            name=name,
            start_date=start_date.date(),
            end_date=end_date.date(),
            description=description
        )
        db.session.add(meal_plan)
        db.session.commit()
        return meal_plan
    
    def add_meal_to_plan(self, meal_plan_id: int, day_of_week: int,
                        meal_type: str, name: str,
                        description: str = None,
                        calories: int = None,
                        protein: float = None,
                        carbs: float = None,
                        fat: float = None) -> Meal:
        """Add a meal to a meal plan."""
        meal = Meal(
            meal_plan_id=meal_plan_id,
            day_of_week=day_of_week,
            meal_type=meal_type,
            name=name,
            description=description,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat
        )
        db.session.add(meal)
        db.session.commit()
        return meal
    
    def add_ingredient_to_meal(self, meal_id: int, name: str,
                             quantity: float, unit: str,
                             calories: int = None,
                             protein: float = None,
                             carbs: float = None,
                             fat: float = None) -> MealIngredient:
        """Add an ingredient to a meal."""
        ingredient = MealIngredient(
            meal_id=meal_id,
            name=name,
            quantity=quantity,
            unit=unit,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat
        )
        db.session.add(ingredient)
        db.session.commit()
        return ingredient
    
    def get_user_meal_plan(self, user_id: int, date: datetime = None) -> MealPlan:
        """Get the active meal plan for a user on a specific date."""
        if date is None:
            date = datetime.utcnow()
        
        return MealPlan.query.filter(
            MealPlan.user_id == user_id,
            MealPlan.is_active == True,
            MealPlan.start_date <= date.date(),
            MealPlan.end_date >= date.date()
        ).first()
    
    def get_todays_meals(self, user_id: int) -> List[Meal]:
        """Get today's meals from the active meal plan."""
        today = datetime.utcnow()
        meal_plan = self.get_user_meal_plan(user_id, today)
        
        if not meal_plan:
            return []
        
        day_of_week = today.weekday()  # 0-6 for Monday-Sunday
        return Meal.query.filter(
            Meal.meal_plan_id == meal_plan.id,
            Meal.day_of_week == day_of_week
        ).all()
    
    def log_meal_consumption(self, user_id: int, meal_id: int,
                           consumed: bool = True,
                           notes: str = None,
                           rating: int = None) -> str:
        """Log a meal consumption and create alerts if necessary."""
        # Log the meal
        log_id = self.meal_tracking.log_meal(
            user_id=user_id,
            meal_id=meal_id,
            date=datetime.utcnow(),
            consumed=consumed,
            notes=notes,
            rating=rating
        )
        
        # Create alert if meal was skipped
        if not consumed:
            meal = Meal.query.get(meal_id)
            self.alert_store.create_alert(
                user_id=user_id,
                alert_type='meal_skipped',
                message=f'Meal "{meal.name}" was skipped',
                priority='medium',
                metadata={'meal_id': meal_id}
            )
        
        return log_id
    
    def check_meal_plan_compliance(self, user_id: int):
        """Check meal plan compliance and create alerts."""
        today = datetime.utcnow()
        meal_plan = self.get_user_meal_plan(user_id, today)
        
        if not meal_plan:
            return
        
        # Get today's meals
        meals = self.get_todays_meals(user_id)
        
        # Check each meal
        for meal in meals:
            # Get meal logs for today
            logs = self.meal_tracking.get_meal_history(
                user_id=user_id,
                start_date=today.replace(hour=0, minute=0, second=0),
                end_date=today.replace(hour=23, minute=59, second=59)
            )
            
            # Check if meal was logged
            meal_logged = any(log['meal_id'] == meal.id for log in logs)
            
            if not meal_logged:
                # Create alert for missed meal
                self.alert_store.create_alert(
                    user_id=user_id,
                    alert_type='meal_missed',
                    message=f'You missed your {meal.meal_type}: {meal.name}',
                    priority='high',
                    metadata={'meal_id': meal.id}
                )
    
    def get_meal_plan_stats(self, user_id: int,
                          start_date: datetime,
                          end_date: datetime) -> Dict[str, Any]:
        """Get statistics for a meal plan period."""
        # Get meal logs for the period
        logs = self.meal_tracking.get_meal_history(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate statistics
        total_meals = len(logs)
        consumed_meals = sum(1 for log in logs if log['consumed'])
        skipped_meals = total_meals - consumed_meals
        
        # Get average rating
        ratings = [log['rating'] for log in logs if log.get('rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            'total_meals': total_meals,
            'consumed_meals': consumed_meals,
            'skipped_meals': skipped_meals,
            'compliance_rate': (consumed_meals / total_meals * 100) if total_meals > 0 else 0,
            'average_rating': avg_rating
        } 