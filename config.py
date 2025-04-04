import os
from dotenv import load_dotenv
import logging
from datetime import timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    FLASK_APP = os.environ.get('FLASK_APP', 'run.py')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Upload folder configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Garmin OAuth Configuration
    GARMIN_CLIENT_ID = os.environ.get('GARMIN_CLIENT_ID')
    GARMIN_CLIENT_SECRET = os.environ.get('GARMIN_CLIENT_SECRET')
    GARMIN_REDIRECT_URI = os.environ.get('GARMIN_REDIRECT_URI', 'http://localhost:5001/garmin/callback')
    
    # Debug logging for Garmin credentials
    logger.info("Loading Garmin credentials from environment...")
    logger.info(f"GARMIN_CLIENT_ID configured: {'Yes' if GARMIN_CLIENT_ID else 'No'}")
    logger.info(f"GARMIN_CLIENT_SECRET configured: {'Yes' if GARMIN_CLIENT_SECRET else 'No'}")
    logger.info(f"GARMIN_REDIRECT_URI configured: {'Yes' if GARMIN_REDIRECT_URI else 'No'}")
    
    # HTTPS settings
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    REMEMBER_COOKIE_SECURE = True  # Only send "remember me" cookie over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    REMEMBER_COOKIE_HTTPONLY = True  # Prevent JavaScript access to remember cookie
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)  # Session timeout
    
    # Security headers
    STRICT_TRANSPORT_SECURITY = True  # Enable HSTS
    STRICT_TRANSPORT_SECURITY_PRELOAD = True
    STRICT_TRANSPORT_SECURITY_MAX_AGE = 31536000  # 1 year in seconds
    STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS = True

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # In development, you might want to disable secure cookies for testing
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # Ensure these are set in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # Use strong secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in environment

# Dictionary mapping configuration names to configuration classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 