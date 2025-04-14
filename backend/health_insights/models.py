from .. import db
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, Any
from math import ceil
from flask import current_app

class DataType(Enum):
    HEART_RATE = "heart_rate"
    SLEEP = "sleep"
    STEPS = "steps"
    ACTIVITY = "activity"
    NUTRITION = "nutrition"
    RECOVERY = "recovery"
    STRESS = "stress"

class HealthPlatform(ABC):
    """Abstract base class for health data platforms."""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.last_sync = None
        self.sync_interval = 6  # hours
        self.auto_sync = True
    
    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Connect to the health platform."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the health platform."""
        pass
    
    @abstractmethod
    def fetch_data(self, data_type: DataType, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Fetch health data from the platform."""
        pass
    
    @abstractmethod
    def normalize_data(self, data: Dict[str, Any], data_type: DataType) -> Dict[str, Any]:
        """Normalize platform-specific data to unified format."""
        pass

class UserProfile(db.Model):
    """User health profile model."""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=False)  # in kg
    height = db.Column(db.Integer, nullable=False)  # in cm
    gender = db.Column(db.String(20), nullable=False)
    activity_level = db.Column(db.String(20), nullable=False)
    goal_type = db.Column(db.String(20), nullable=False)
    weekly_activity_target = db.Column(db.Float, nullable=False)  # in hours
    medical_conditions = db.Column(db.Text)
    medications = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserProfile {self.name}>'

class HealthInsightModel:
    """Model for generating health insights."""
    
    def analyze_heart_rate(self, heart_rate_data):
        """Analyze heart rate data and generate insights."""
        if not heart_rate_data:
            return {
                'status': 'NO_DATA',
                'confidence': 0,
                'recommendations': ['Start tracking your heart rate to get insights']
            }
            
        # Calculate average heart rate
        heart_rates = [hr['value'] for hr in heart_rate_data if isinstance(hr, dict) and 'value' in hr]
        if not heart_rates:
            return {
                'status': 'NO_DATA',
                'confidence': 0,
                'recommendations': ['No valid heart rate measurements found']
            }
            
        avg_hr = sum(heart_rates) / len(heart_rates)
        
        # Determine status based on average heart rate
        if avg_hr > 100:
            status = 'WARNING'
            recommendations = [
                'Consider consulting a healthcare provider',
                'Practice relaxation techniques',
                'Monitor your caffeine intake'
            ]
        elif avg_hr < 60:
            status = 'INFO'
            recommendations = [
                'This could be normal for athletes',
                'Monitor for symptoms like dizziness',
                'Ensure adequate hydration'
            ]
        else:
            status = 'SUCCESS'
            recommendations = [
                'Maintain your current lifestyle',
                'Continue regular exercise',
                'Keep tracking your heart rate'
            ]
            
        return {
            'status': status,
            'confidence': 0.8,
            'recommendations': recommendations
        }
        
    def analyze_sleep(self, sleep_data):
        """Analyze sleep quality and generate insights."""
        if not sleep_data:
            return {
                'quality_score': 0,
                'status': 'NO_DATA',
                'recommendations': ['Start tracking your sleep to get insights']
            }
            
        # Calculate average sleep duration
        sleep_durations = [sleep['duration'] for sleep in sleep_data if isinstance(sleep, dict) and 'duration' in sleep]
        if not sleep_durations:
            return {
                'quality_score': 0,
                'status': 'NO_DATA',
                'recommendations': ['No valid sleep measurements found']
            }
            
        avg_duration = sum(sleep_durations) / len(sleep_durations)
        
        # Calculate quality score (0-1)
        quality_score = min(avg_duration / (8 * 3600), 1)  # 8 hours as target
        
        # Generate recommendations
        if quality_score < 0.6:
            status = 'WARNING'
            recommendations = [
                'Aim for 7-9 hours of sleep',
                'Maintain a consistent sleep schedule',
                'Create a relaxing bedtime routine'
            ]
        elif quality_score < 0.8:
            status = 'INFO'
            recommendations = [
                'You\'re getting close to optimal sleep',
                'Try to get to bed 30 minutes earlier',
                'Limit screen time before bed'
            ]
        else:
            status = 'SUCCESS'
            recommendations = [
                'Maintain your current sleep schedule',
                'Keep your bedroom cool and dark',
                'Continue monitoring your sleep quality'
            ]
            
        return {
            'quality_score': quality_score,
            'status': status,
            'recommendations': recommendations
        }
        
    def analyze_recovery(self, profile):
        """Analyze recovery status based on user profile."""
        if not profile:
            return {
                'status': 'NO_DATA',
                'confidence': 0,
                'recommendations': ['Complete your profile to get recovery insights']
            }
            
        # Base recovery analysis on activity level and goals
        if profile.activity_level in ['high', 'athlete']:
            status = 'WARNING'
            recommendations = [
                'Ensure adequate rest between intense workouts',
                'Focus on proper nutrition and hydration',
                'Monitor for signs of overtraining'
            ]
        elif profile.activity_level == 'moderate':
            status = 'SUCCESS'
            recommendations = [
                'Your activity level is well-balanced',
                'Continue with your current routine',
                'Consider gradually increasing intensity'
            ]
        else:
            status = 'INFO'
            recommendations = [
                'Consider increasing your activity level',
                'Start with low-impact exercises',
                'Set realistic weekly goals'
            ]
            
        return {
            'status': status,
            'confidence': 0.7,
            'recommendations': recommendations
        }
        
    def analyze_nutrition(self, profile):
        """Calculate nutrition needs based on profile."""
        if not profile:
            return None
            
        # Calculate BMR using Harris-Benedict equation
        if profile.gender.lower() == 'male':
            bmr = 88.362 + (13.397 * profile.weight) + (4.799 * profile.height) - (5.677 * profile.age)
        else:
            bmr = 447.593 + (9.247 * profile.weight) + (3.098 * profile.height) - (4.330 * profile.age)
            
        # Activity multiplier
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'high': 1.725,
            'athlete': 1.9
        }
        
        multiplier = activity_multipliers.get(profile.activity_level.lower(), 1.2)
        daily_calories = bmr * multiplier
        
        # Adjust based on goal
        if profile.goal_type == 'weight_loss':
            daily_calories *= 0.85  # 15% deficit
            macros = {'protein': 40, 'carbs': 30, 'fat': 30}
        elif profile.goal_type == 'muscle_gain':
            daily_calories *= 1.1  # 10% surplus
            macros = {'protein': 30, 'carbs': 50, 'fat': 20}
        else:  # maintenance or fitness
            macros = {'protein': 30, 'carbs': 40, 'fat': 30}
            
        # Calculate water needs (ml) - basic calculation
        hydration = profile.weight * 35  # 35ml per kg of body weight
        
        return {
            'daily_calories': daily_calories,
            'macros': macros,
            'hydration': hydration
        }

class RecoveryAssistant:
    """Analyzes user's recovery status and provides personalized recommendations."""
    
    def __init__(self):
        self.sleep_threshold = 0.7  # 70% of normal sleep quality
        self.hrv_threshold = 0.8    # 80% of normal HRV
        
    def analyze_recovery_status(self, user_data):
        """Analyze recovery status based on sleep and HRV data."""
        sleep_score = user_data.get('sleep_score', 0)
        hrv_score = user_data.get('hrv_score', 0)
        user_averages = user_data.get('user_averages', {})
        
        sleep_ratio = sleep_score / user_averages.get('sleep_score', sleep_score) if user_averages.get('sleep_score') else 1
        hrv_ratio = hrv_score / user_averages.get('hrv_score', hrv_score) if user_averages.get('hrv_score') else 1
        
        recovery_status = self._calculate_recovery_status(sleep_ratio, hrv_ratio)
        recommendations = self._generate_recommendations(recovery_status, sleep_ratio, hrv_ratio)
        
        return {
            'status': recovery_status,
            'sleep_ratio': sleep_ratio,
            'hrv_ratio': hrv_ratio,
            'recommendations': recommendations
        }
    
    def _calculate_recovery_status(self, sleep_ratio, hrv_ratio):
        """Calculate recovery status based on sleep and HRV ratios."""
        if sleep_ratio < self.sleep_threshold and hrv_ratio < self.hrv_threshold:
            return 'NEEDS_RECOVERY'
        elif sleep_ratio < self.sleep_threshold or hrv_ratio < self.hrv_threshold:
            return 'MODERATE_RECOVERY'
        return 'RECOVERED'
    
    def _generate_recommendations(self, status, sleep_ratio, hrv_ratio):
        """Generate personalized recovery recommendations."""
        recommendations = []
        
        if status == 'NEEDS_RECOVERY':
            recommendations.extend([
                'Take a rest day from intense exercise',
                'Focus on gentle movement like walking or yoga',
                'Practice deep breathing or meditation',
                'Prioritize sleep and stress management'
            ])
        elif status == 'MODERATE_RECOVERY':
            if sleep_ratio < self.sleep_threshold:
                recommendations.extend([
                    'Consider a shorter, lower-intensity workout',
                    'Practice good sleep hygiene tonight',
                    'Avoid caffeine after 2 PM'
                ])
            if hrv_ratio < self.hrv_threshold:
                recommendations.extend([
                    'Include extra warm-up and cool-down time',
                    'Try light mobility work',
                    'Focus on stress management techniques'
                ])
        else:
            recommendations.extend([
                "You're recovered and ready for normal training",
                "Continue monitoring your recovery metrics",
                "Maintain your current sleep and recovery practices"
            ])
        
        return recommendations 

class NutritionAdvisor:
    """Provides personalized nutrition recommendations based on user data and goals."""
    
    def __init__(self):
        self.protein_per_kg = {
            'weight_loss': 2.2,      # g/kg for weight loss
            'muscle_gain': 2.4,      # g/kg for muscle gain
            'maintenance': 1.8,      # g/kg for maintenance
            'endurance': 1.6         # g/kg for endurance
        }
    
    def calculate_nutrition_needs(self, user_data):
        """Calculate detailed nutrition needs based on user data."""
        weight = user_data.get('weight', 70)  # kg
        height = user_data.get('height', 170)  # cm
        age = user_data.get('age', 30)
        gender = user_data.get('gender', 'male')
        activity_level = user_data.get('activity_level', 'moderate')
        goal = user_data.get('goal', 'maintenance')
        calories_burned = user_data.get('calories_burned', 0)
        
        # Calculate BMR using Mifflin-St Jeor equation
        if gender.lower() == 'male':
            bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
        else:
            bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
        
        # Activity multiplier
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'high': 1.725,
            'athlete': 1.9
        }
        
        # Calculate TDEE (Total Daily Energy Expenditure)
        tdee = bmr * activity_multipliers.get(activity_level, 1.2)
        tdee += calories_burned  # Add additional calories burned from activities
        
        # Adjust calories based on goal
        if goal == 'weight_loss':
            target_calories = tdee * 0.85  # 15% deficit
        elif goal == 'muscle_gain':
            target_calories = tdee * 1.1   # 10% surplus
        else:
            target_calories = tdee
        
        # Calculate macronutrient distribution
        protein_g = weight * self.protein_per_kg.get(goal, 1.8)
        protein_cals = protein_g * 4
        
        fat_cals = target_calories * 0.25  # 25% of calories from fat
        fat_g = fat_cals / 9
        
        carb_cals = target_calories - protein_cals - fat_cals
        carb_g = carb_cals / 4
        
        return {
            'target_calories': round(target_calories),
            'macros': {
                'protein': {
                    'grams': round(protein_g),
                    'calories': round(protein_cals),
                    'percentage': round((protein_cals / target_calories) * 100)
                },
                'carbs': {
                    'grams': round(carb_g),
                    'calories': round(carb_cals),
                    'percentage': round((carb_cals / target_calories) * 100)
                },
                'fat': {
                    'grams': round(fat_g),
                    'calories': round(fat_cals),
                    'percentage': round((fat_cals / target_calories) * 100)
                }
            },
            'meal_timing': self._get_meal_timing_recommendations(activity_level, goal),
            'hydration': round(weight * 35)  # 35ml per kg of body weight
        }
    
    def _get_meal_timing_recommendations(self, activity_level, goal):
        """Generate meal timing recommendations based on activity and goals."""
        if activity_level in ['high', 'athlete']:
            if goal == 'muscle_gain':
                return {
                    'meals_per_day': 6,
                    'pre_workout': 'Eat 2-3 hours before training',
                    'post_workout': 'Consume protein and carbs within 30 minutes',
                    'spacing': 'Eat every 2-3 hours'
                }
            else:
                return {
                    'meals_per_day': 5,
                    'pre_workout': 'Light meal 1-2 hours before training',
                    'post_workout': 'Protein and carbs within 1 hour',
                    'spacing': 'Eat every 3-4 hours'
                }
        else:
            return {
                'meals_per_day': 4,
                'pre_workout': 'Light snack 1 hour before activity',
                'post_workout': 'Balanced meal within 2 hours',
                'spacing': 'Eat every 4-5 hours'
            } 

class MealPlanner:
    """Generates personalized meal plans and grocery lists."""
    
    def __init__(self):
        self.meal_categories = {
            'breakfast': 'Breakfast',
            'lunch': 'Lunch',
            'dinner': 'Dinner',
            'snacks': 'Snacks'
        }
        self.food_categories = {
            'proteins': ['chicken', 'fish', 'beef', 'eggs', 'tofu', 'lentils', 'beans', 'pork', 'turkey', 'shrimp'],
            'carbs': ['rice', 'quinoa', 'pasta', 'bread', 'potatoes', 'oats', 'corn', 'sweet potatoes', 'barley', 'couscous'],
            'vegetables': ['broccoli', 'spinach', 'carrots', 'peppers', 'kale', 'zucchini', 'cauliflower', 'asparagus', 'brussels sprouts', 'green beans'],
            'fruits': ['apples', 'bananas', 'berries', 'oranges', 'grapes', 'melon', 'pears', 'peaches', 'pineapple', 'mango'],
            'healthy_fats': ['avocado', 'olive oil', 'nuts', 'seeds', 'coconut oil', 'almond butter', 'peanut butter', 'walnuts', 'chia seeds', 'flaxseeds'],
            'dairy': ['milk', 'yogurt', 'cheese', 'cottage cheese', 'greek yogurt', 'cream cheese', 'sour cream'],
            'condiments': ['salt', 'pepper', 'garlic', 'onion', 'herbs', 'spices', 'vinegar', 'soy sauce', 'hot sauce', 'mustard']
        }
        
        # Sample recipes for each meal type
        self.recipes = {
            'breakfast': [
                {
                    'name': 'Protein Oatmeal',
                    'ingredients': [
                        {'name': 'oats', 'amount': 50, 'unit': 'g'},
                        {'name': 'protein powder', 'amount': 30, 'unit': 'g'},
                        {'name': 'berries', 'amount': 100, 'unit': 'g'},
                        {'name': 'almonds', 'amount': 15, 'unit': 'g'},
                        {'name': 'cinnamon', 'amount': 2, 'unit': 'g'}
                    ],
                    'instructions': [
                        'Cook oats according to package instructions',
                        'Stir in protein powder',
                        'Top with berries and almonds',
                        'Sprinkle with cinnamon'
                    ]
                },
                {
                    'name': 'Vegetable Omelette',
                    'ingredients': [
                        {'name': 'eggs', 'amount': 3, 'unit': 'large'},
                        {'name': 'spinach', 'amount': 50, 'unit': 'g'},
                        {'name': 'bell peppers', 'amount': 50, 'unit': 'g'},
                        {'name': 'olive oil', 'amount': 5, 'unit': 'ml'},
                        {'name': 'salt', 'amount': 1, 'unit': 'g'},
                        {'name': 'pepper', 'amount': 1, 'unit': 'g'}
                    ],
                    'instructions': [
                        'Sauté vegetables in olive oil',
                        'Beat eggs with salt and pepper',
                        'Pour eggs over vegetables',
                        'Cook until set'
                    ]
                }
            ],
            'lunch': [
                {
                    'name': 'Grilled Chicken Salad',
                    'ingredients': [
                        {'name': 'chicken breast', 'amount': 150, 'unit': 'g'},
                        {'name': 'mixed greens', 'amount': 100, 'unit': 'g'},
                        {'name': 'cherry tomatoes', 'amount': 100, 'unit': 'g'},
                        {'name': 'olive oil', 'amount': 15, 'unit': 'ml'},
                        {'name': 'balsamic vinegar', 'amount': 10, 'unit': 'ml'},
                        {'name': 'salt', 'amount': 1, 'unit': 'g'},
                        {'name': 'pepper', 'amount': 1, 'unit': 'g'}
                    ],
                    'instructions': [
                        'Season and grill chicken breast',
                        'Toss greens and tomatoes with olive oil and vinegar',
                        'Top with sliced chicken',
                        'Season with salt and pepper'
                    ]
                }
            ],
            'dinner': [
                {
                    'name': 'Salmon with Quinoa',
                    'ingredients': [
                        {'name': 'salmon fillet', 'amount': 150, 'unit': 'g'},
                        {'name': 'quinoa', 'amount': 100, 'unit': 'g'},
                        {'name': 'broccoli', 'amount': 100, 'unit': 'g'},
                        {'name': 'olive oil', 'amount': 10, 'unit': 'ml'},
                        {'name': 'lemon', 'amount': 1, 'unit': 'whole'},
                        {'name': 'garlic', 'amount': 2, 'unit': 'cloves'},
                        {'name': 'salt', 'amount': 1, 'unit': 'g'},
                        {'name': 'pepper', 'amount': 1, 'unit': 'g'}
                    ],
                    'instructions': [
                        'Cook quinoa according to package instructions',
                        'Season salmon with salt, pepper, and garlic',
                        'Roast salmon and broccoli with olive oil',
                        'Serve with lemon wedges'
                    ]
                }
            ],
            'snacks': [
                {
                    'name': 'Protein Smoothie',
                    'ingredients': [
                        {'name': 'protein powder', 'amount': 30, 'unit': 'g'},
                        {'name': 'banana', 'amount': 1, 'unit': 'medium'},
                        {'name': 'almond milk', 'amount': 250, 'unit': 'ml'},
                        {'name': 'peanut butter', 'amount': 15, 'unit': 'g'},
                        {'name': 'ice', 'amount': 100, 'unit': 'g'}
                    ],
                    'instructions': [
                        'Add all ingredients to blender',
                        'Blend until smooth',
                        'Serve immediately'
                    ]
                }
            ]
        }
    
    def generate_meal_plan(self, nutrition_needs, preferences):
        """Generate a weekly meal plan based on nutrition needs and preferences."""
        try:
            daily_calories = nutrition_needs['target_calories']
            macros = nutrition_needs['macros']
            dietary_preferences = preferences.get('dietary_type', 'balanced')
            excluded_foods = preferences.get('excluded_foods', [])
            servings = preferences.get('servings', 1)
            
            # Generate meal distribution
            meal_calories = self._distribute_calories(daily_calories, preferences.get('meal_count', 4))
            
            # Generate weekly plan
            weekly_plan = {}
            grocery_list = {}
            
            for day in range(7):
                daily_meals = {}
                for meal, calories in meal_calories.items():
                    meal_macros = self._calculate_meal_macros(calories, macros)
                    meal_items = self._select_meal_items(
                        meal_macros,
                        dietary_preferences,
                        excluded_foods,
                        meal,
                        servings
                    )
                    if meal_items:
                        daily_meals[meal] = meal_items
                        
                        # Add items to grocery list
                        for item in meal_items['ingredients']:
                            category = self._get_food_category(item['name'])
                            if category not in grocery_list:
                                grocery_list[category] = {}
                            if item['name'] not in grocery_list[category]:
                                grocery_list[category][item['name']] = {
                                    'amount': 0,
                                    'unit': item['unit'],
                                    'recipes': []
                                }
                            grocery_list[category][item['name']]['amount'] += item['amount']
                            if meal_items['name'] not in grocery_list[category][item['name']]['recipes']:
                                grocery_list[category][item['name']]['recipes'].append(meal_items['name'])
                
                weekly_plan[f'day_{day + 1}'] = daily_meals
            
            # Generate prep schedule
            prep_schedule = self._generate_prep_schedule(weekly_plan)
            
            return {
                'weekly_plan': weekly_plan,
                'grocery_list': self._optimize_grocery_list(grocery_list),
                'prep_schedule': prep_schedule
            }
        except Exception as e:
            current_app.logger.error(f"Error generating meal plan: {str(e)}")
            return None
    
    def generate_shopping_links(self, grocery_list):
        """Generate shopping cart links for various platforms."""
        try:
            # Format grocery list for URL parameters
            formatted_items = []
            for category, items in grocery_list.items():
                for item in items:
                    formatted_items.append(f"{item['quantity']} {item['item']}".strip())
            
            # Generate platform-specific links
            shopping_links = {
                'instacart': {
                    'name': 'Instacart',
                    'url': f"https://www.instacart.com/store/partner_recipe?" + 
                          f"recipe_ingredients={','.join(formatted_items)}"
                },
                'amazon_fresh': {
                    'name': 'Amazon Fresh',
                    'url': f"https://www.amazon.com/alm/storefront?" + 
                          f"almBrandId=QW1hem9uIEZyZXNo&" + 
                          f"items={','.join(formatted_items)}"
                }
            }
            
            return shopping_links
        except Exception as e:
            current_app.logger.error(f"Error generating shopping links: {str(e)}")
            return {}

    def _optimize_grocery_list(self, grocery_list):
        """Optimize the grocery list by combining similar items and adding categories."""
        optimized_list = {}
        for category, items in grocery_list.items():
            optimized_list[category] = []
            for item_name, details in items.items():
                # Round up amounts to convenient shopping quantities
                amount = details['amount']
                if details['unit'] == 'g':
                    amount = ceil(amount / 100) * 100  # Round to nearest 100g
                elif details['unit'] == 'ml':
                    amount = ceil(amount / 250) * 250  # Round to nearest 250ml
                elif details['unit'] == 'whole':
                    amount = ceil(amount)  # Round up whole items
                
                optimized_list[category].append({
                    'item': item_name,
                    'quantity': f"{amount}{details['unit']}",
                    'recipes': details['recipes']
                })
        
        # Sort categories in a logical shopping order
        category_order = ['proteins', 'dairy', 'vegetables', 'fruits', 'carbs', 'healthy_fats', 'condiments']
        sorted_list = {}
        for category in category_order:
            if category in optimized_list:
                sorted_list[category] = optimized_list[category]
        
        # Add any remaining categories
        for category, items in optimized_list.items():
            if category not in sorted_list:
                sorted_list[category] = items
        
        return sorted_list

    def _generate_prep_schedule(self, weekly_plan):
        """Generate a meal prep schedule based on the weekly plan."""
        prep_schedule = {
            'sunday': [],
            'wednesday': []
        }
        
        # Group meals by type for batch cooking
        meal_types = {}
        for day, meals in weekly_plan.items():
            for meal_type, meal in meals.items():
                if meal_type not in meal_types:
                    meal_types[meal_type] = []
                meal_types[meal_type].append(meal)
        
        # Add batch cooking tasks to Sunday prep
        for meal_type, meals in meal_types.items():
            if meal_type in ['breakfast', 'lunch']:
                prep_schedule['sunday'].append({
                    'task': f'Prepare {meal_type} for the week',
                    'meals': [meal['name'] for meal in meals],
                    'estimated_time': '1-2 hours',
                    'ingredients': self._get_prep_ingredients(meals)
                })
        
        # Add Wednesday prep tasks
        prep_schedule['wednesday'].append({
            'task': 'Prepare fresh ingredients for remaining meals',
            'estimated_time': '30 minutes',
            'ingredients': self._get_fresh_ingredients(weekly_plan)
        })
        
        return prep_schedule

    def _get_prep_ingredients(self, meals):
        """Get ingredients needed for meal prep."""
        ingredients = {}
        for meal in meals:
            for ingredient in meal['ingredients']:
                if ingredient['name'] not in ingredients:
                    ingredients[ingredient['name']] = {
                        'amount': 0,
                        'unit': ingredient['unit']
                    }
                ingredients[ingredient['name']]['amount'] += ingredient['amount']
        return ingredients

    def _get_fresh_ingredients(self, weekly_plan):
        """Get fresh ingredients needed for the week."""
        fresh_ingredients = {}
        for day, meals in weekly_plan.items():
            for meal_type, meal in meals.items():
                if meal_type in ['dinner', 'snacks']:
                    for ingredient in meal['ingredients']:
                        if ingredient['name'] not in fresh_ingredients:
                            fresh_ingredients[ingredient['name']] = {
                                'amount': 0,
                                'unit': ingredient['unit']
                            }
                        fresh_ingredients[ingredient['name']]['amount'] += ingredient['amount']
        return fresh_ingredients
    
    def _distribute_calories(self, total_calories, meals_per_day):
        """Distribute daily calories across meals."""
        if meals_per_day == 6:
            return {
                'breakfast': total_calories * 0.2,
                'morning_snack': total_calories * 0.1,
                'lunch': total_calories * 0.25,
                'afternoon_snack': total_calories * 0.1,
                'dinner': total_calories * 0.25,
                'evening_snack': total_calories * 0.1
            }
        elif meals_per_day == 5:
            return {
                'breakfast': total_calories * 0.25,
                'morning_snack': total_calories * 0.1,
                'lunch': total_calories * 0.3,
                'afternoon_snack': total_calories * 0.1,
                'dinner': total_calories * 0.25
            }
        else:  # 4 meals
            return {
                'breakfast': total_calories * 0.3,
                'lunch': total_calories * 0.3,
                'snack': total_calories * 0.1,
                'dinner': total_calories * 0.3
            }
    
    def _calculate_meal_macros(self, meal_calories, daily_macros):
        """Calculate macros for a specific meal."""
        return {
            'protein': {
                'grams': round((meal_calories * (daily_macros['protein']['percentage'] / 100)) / 4)
            },
            'carbs': {
                'grams': round((meal_calories * (daily_macros['carbs']['percentage'] / 100)) / 4)
            },
            'fat': {
                'grams': round((meal_calories * (daily_macros['fat']['percentage'] / 100)) / 9)
            }
        }
    
    def _select_meal_items(self, meal_macros, dietary_preferences, excluded_foods, meal_type, servings=1):
        """Select appropriate food items for a meal based on macros and preferences."""
        try:
            # Filter recipes based on meal type and dietary preferences
            available_recipes = self.recipes.get(meal_type, [])
            
            if not available_recipes:
                # If no specific recipes, create a balanced meal
                return {
                    'name': f'Balanced {meal_type.replace("_", " ").title()}',
                    'calories': sum([
                        meal_macros['protein']['grams'] * 4,
                        meal_macros['carbs']['grams'] * 4,
                        meal_macros['fat']['grams'] * 9
                    ]),
                    'macros': meal_macros,
                    'ingredients': [
                        {'name': 'chicken breast', 'amount': 150 * servings, 'unit': 'g'},
                        {'name': 'brown rice', 'amount': 100 * servings, 'unit': 'g'},
                        {'name': 'broccoli', 'amount': 100 * servings, 'unit': 'g'},
                        {'name': 'olive oil', 'amount': 15 * servings, 'unit': 'ml'}
                    ],
                    'instructions': [
                        'Cook chicken breast',
                        'Prepare brown rice',
                        'Steam broccoli',
                        'Combine and serve'
                    ]
                }
            
            # Select a random recipe (in a real app, this would be more sophisticated)
            import random
            recipe = random.choice(available_recipes)
            
            # Adjust ingredients for servings
            adjusted_ingredients = []
            for ingredient in recipe['ingredients']:
                adjusted_ingredients.append({
                    'name': ingredient['name'],
                    'amount': ingredient['amount'] * servings,
                    'unit': ingredient['unit']
                })
            
            return {
                'name': recipe['name'],
                'calories': sum([
                    meal_macros['protein']['grams'] * 4,
                    meal_macros['carbs']['grams'] * 4,
                    meal_macros['fat']['grams'] * 9
                ]),
                'macros': meal_macros,
                'ingredients': adjusted_ingredients,
                'instructions': recipe['instructions']
            }
        except Exception as e:
            current_app.logger.error(f"Error selecting meal items: {str(e)}")
            return None
    
    def _get_food_category(self, food_name):
        """Determine the category of a food item."""
        for category, foods in self.food_categories.items():
            if any(food in food_name.lower() for food in foods):
                return category
        return 'other' 