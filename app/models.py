from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db

class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Health Information
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    activity_level = db.Column(db.String(20))
    health_goals = db.Column(db.String(200))
    
    # Health Metrics History
    health_metrics = db.relationship('HealthMetric', backref='user', lazy=True)
    
    def __init__(self, username, email):
        self.username = username
        self.email = email
    
    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)
    
    def calculate_bmi(self):
        """Calculate BMI based on height and weight"""
        if self.height and self.weight and self.height > 0:
            # Convert height from cm to meters
            height_m = self.height / 100
            return round(self.weight / (height_m * height_m), 1)
        return None
    
    def get_bmi_category(self):
        """Get BMI category based on calculated BMI"""
        bmi = self.calculate_bmi()
        if not bmi:
            return None
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 25:
            return "Normal weight"
        elif 25 <= bmi < 30:
            return "Overweight"
        else:
            return "Obese"
    
    def __repr__(self):
        return f'<User {self.username}>'

class HealthMetric(db.Model):
    """Health metrics history model."""
    __tablename__ = 'health_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    weight = db.Column(db.Float)  # in kg
    body_fat_percentage = db.Column(db.Float)
    muscle_mass_percentage = db.Column(db.Float)
    bmi = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<HealthMetric {self.date}>' 