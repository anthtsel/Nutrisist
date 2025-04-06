from datetime import datetime, date
from app import db

class MealPlan(db.Model):
    """Stores user meal plans in PostgreSQL."""
    __tablename__ = 'meal_plans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    meals = db.relationship('Meal', backref='meal_plan', lazy=True, cascade='all, delete-orphan')
    user = db.relationship('User', backref='meal_plans')

    __table_args__ = (
        db.Index('idx_meal_plan_user_dates', 'user_id', 'start_date', 'end_date'),
    )

    def __repr__(self):
        return f'<MealPlan {self.name} for user {self.user_id}>'

class Meal(db.Model):
    """Stores individual meals within a meal plan."""
    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True)
    meal_plan_id = db.Column(db.Integer, db.ForeignKey('meal_plans.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 for Monday-Sunday
    meal_type = db.Column(db.String(50), nullable=False)  # breakfast, lunch, dinner, snack
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)  # in grams
    carbs = db.Column(db.Float)    # in grams
    fat = db.Column(db.Float)      # in grams
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    ingredients = db.relationship('MealIngredient', backref='meal', lazy=True, cascade='all, delete-orphan')

    __table_args__ = (
        db.Index('idx_meal_plan_day_type', 'meal_plan_id', 'day_of_week', 'meal_type'),
    )

    def __repr__(self):
        return f'<Meal {self.name} ({self.meal_type})>'

class MealIngredient(db.Model):
    """Stores ingredients for each meal."""
    __tablename__ = 'meal_ingredients'

    id = db.Column(db.Integer, primary_key=True)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # g, ml, cups, etc.
    calories = db.Column(db.Integer)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MealIngredient {self.name} ({self.quantity}{self.unit})>' 