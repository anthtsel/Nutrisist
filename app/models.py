from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from . import db
from flask_bcrypt import generate_password_hash, check_password_hash
from enum import Enum

class UserRole(Enum):
    USER = 'user'
    ADMIN = 'admin'

class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default=UserRole.USER.value)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Health Information
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    activity_level = db.Column(db.String(20))
    health_goals = db.Column(db.String(200))
    
    # Relationships
    health_metrics = db.relationship('HealthMetric', backref='user', lazy=True)
    profile = db.relationship('UserProfile', backref='user', uselist=False, lazy=True)
    
    def __init__(self, username, email, password=None, role=UserRole.USER.value):
        self.username = username
        self.email = email
        self.role = role
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Hash password using bcrypt."""
        self.password_hash = generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)
    
    def has_role(self, role):
        """Check if user has the specified role."""
        return self.role == role.value if isinstance(role, UserRole) else self.role == role
    
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN.value
    
    def record_login_attempt(self, success):
        """Record login attempt and handle account locking."""
        if success:
            self.failed_login_attempts = 0
            self.locked_until = None
            self.last_login = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
                self.locked_until = datetime.utcnow() + timedelta(minutes=15)
    
    def is_locked(self):
        """Check if account is locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
    
    def calculate_bmi(self):
        """Calculate BMI based on height and weight."""
        if self.height and self.weight and self.height > 0:
            height_m = self.height / 100
            return round(self.weight / (height_m * height_m), 1)
        return None
    
    def get_bmi_category(self):
        """Get BMI category based on calculated BMI."""
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