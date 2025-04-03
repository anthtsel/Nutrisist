from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    # Health Information
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    activity_level = db.Column(db.String(20))
    health_goals = db.Column(db.String(200))
    
    # Health Metrics History
    health_metrics = db.relationship('HealthMetric', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
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
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    weight = db.Column(db.Float)  # in kg
    body_fat_percentage = db.Column(db.Float)
    muscle_mass_percentage = db.Column(db.Float)
    bmi = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<HealthMetric {self.date}>' 