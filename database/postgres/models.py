from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Association tables
meal_plan_meals = db.Table('meal_plan_meals',
    db.Column('meal_plan_id', db.Integer, db.ForeignKey('meal_plans.id'), primary_key=True),
    db.Column('meal_id', db.Integer, db.ForeignKey('meals.id'), primary_key=True),
    db.Column('meal_time', db.String(20), nullable=False),  # breakfast, lunch, dinner, snack
    db.Column('day_of_week', db.Integer, nullable=False)    # 0-6 (Monday-Sunday)
)

meal_ingredients = db.Table('meal_ingredients',
    db.Column('meal_id', db.Integer, db.ForeignKey('meals.id'), primary_key=True),
    db.Column('ingredient_id', db.Integer, db.ForeignKey('ingredients.id'), primary_key=True),
    db.Column('quantity', db.Float, nullable=False),
    db.Column('unit', db.String(20), nullable=False)
)

user_dietary_restrictions = db.Table('user_dietary_restrictions',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('dietary_restriction_id', db.Integer, db.ForeignKey('dietary_restrictions.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # One-to-one relationship with profile
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    
    # One-to-many relationships
    meal_plans = db.relationship('MealPlan', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Basic info
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    weight = db.Column(db.Float)  # in kg
    height = db.Column(db.Float)  # in cm
    activity_level = db.Column(db.String(20))  # sedentary, light, moderate, active, very active
    
    # Dietary goals
    calorie_goal = db.Column(db.Integer)
    protein_goal = db.Column(db.Integer)  # in grams
    carb_goal = db.Column(db.Integer)     # in grams
    fat_goal = db.Column(db.Integer)      # in grams
    
    # Meal preferences
    meals_per_day = db.Column(db.Integer, default=3)
    preferred_cuisines = db.Column(db.String(255))  # Comma-separated list
    
    # Wearable connection
    wearable_connected = db.Column(db.Boolean, default=False)
    wearable_type = db.Column(db.String(50))  # fitbit, apple_watch, etc.
    wearable_id = db.Column(db.String(100))   # ID or token for the connected device
    last_sync = db.Column(db.DateTime)
    
    # Many-to-many relationship with dietary restrictions
    dietary_restrictions = db.relationship('DietaryRestriction', 
                                          secondary=user_dietary_restrictions,
                                          lazy='subquery',
                                          backref=db.backref('users', lazy=True))
    
    def __repr__(self):
        return f'<UserProfile {self.user_id}>'

class MealPlan(db.Model):
    __tablename__ = 'meal_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    total_calories = db.Column(db.Integer)
    total_protein = db.Column(db.Float)
    total_carbs = db.Column(db.Float)
    total_fat = db.Column(db.Float)
    
    # Activity data snapshot from MongoDB at time of generation
    avg_daily_calories_burned = db.Column(db.Integer)
    avg_daily_steps = db.Column(db.Integer)
    avg_sleep_duration = db.Column(db.Float)  # in hours
    
    # Many-to-many relationship with meals
    meals = db.relationship('Meal', 
                           secondary=meal_plan_meals,
                           lazy='subquery',
                           backref=db.backref('meal_plans', lazy=True))
    
    def __repr__(self):
        return f'<MealPlan {self.name}>'

class Meal(db.Model):
    __tablename__ = 'meals'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Nutritional information
    calories = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Float, nullable=False)  # in grams
    carbs = db.Column(db.Float, nullable=False)    # in grams
    fat = db.Column(db.Float, nullable=False)      # in grams
    fiber = db.Column(db.Float)                    # in grams
    
    prep_time = db.Column(db.Integer)  # in minutes
    cooking_time = db.Column(db.Integer)  # in minutes
    
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    cuisine = db.Column(db.String(50))
    
    # Recipe instructions
    instructions = db.Column(db.Text)
    
    # Many-to-many relationship with ingredients
    ingredients = db.relationship('Ingredient', 
                                 secondary=meal_ingredients,
                                 lazy='subquery',
                                 backref=db.backref('meals', lazy=True))
    
    # User ratings
    avg_rating = db.Column(db.Float, default=0)
    
    def __repr__(self):
        return f'<Meal {self.name}>'

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    
    # Nutritional information per 100g
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)  # in grams
    carbs = db.Column(db.Float)    # in grams
    fat = db.Column(db.Float)      # in grams
    fiber = db.Column(db.Float)    # in grams
    
    food_group = db.Column(db.String(50))  # vegetables, fruits, grains, etc.
    
    def __repr__(self):
        return f'<Ingredient {self.name}>'

class DietaryRestriction(db.Model):
    __tablename__ = 'dietary_restrictions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<DietaryRestriction {self.name}>'