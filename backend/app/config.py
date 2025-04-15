import os
from dotenv import load_dotenv
from datetime import timedelta
from urllib.parse import quote_plus

load_dotenv()

class Config:
    # Common configurations
    SECRET_KEY = os.getenv('SECRET_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt_dev_key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # PostgreSQL configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('POSTGRES_USER')}:{quote_plus(os.getenv('POSTGRES_PASSWORD'))}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    
    # MongoDB configuration
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/nutrisist')
    
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI
    MONGO_URI = os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/nutrisist_test')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    MONGO_URI = os.getenv('MONGO_URI')
    
    # Additional production settings
    JWT_COOKIE_SECURE = True

config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}