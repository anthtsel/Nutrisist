from app import db
from .postgres_models import User, MealPlan, WearableData
from .mongo_helpers import MongoConnection

__all__ = ['User', 'MealPlan', 'WearableData', 'MongoConnection', 'db']

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>' 