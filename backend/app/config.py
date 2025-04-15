import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/nutrisist')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/nutrisist') 