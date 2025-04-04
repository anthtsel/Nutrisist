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

def get_env_bool(var_name, default=False):
    """Convert environment variable to boolean."""
    value = os.environ.get(var_name, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_list(var_name, default=None, separator=','):
    """Convert comma-separated environment variable to list."""
    value = os.environ.get(var_name)
    if value is None:
        return default or []
    return [x.strip() for x in value.split(separator)]

def get_env_int(var_name, default=None):
    """Convert environment variable to integer, stripping any comments."""
    value = os.environ.get(var_name)
    if value is None:
        return default
    # Strip any comments (everything after #)
    value = value.split('#')[0].strip()
    return int(value)

class Config:
    # Flask Configuration
    FLASK_APP = os.environ.get('FLASK_APP', 'run.py')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'generate-a-secure-key-in-production'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = get_env_bool('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)
    
    # Security Configuration
    SESSION_COOKIE_SECURE = get_env_bool('SESSION_COOKIE_SECURE', True)
    SESSION_COOKIE_HTTPONLY = get_env_bool('SESSION_COOKIE_HTTPONLY', True)
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Strict')
    PERMANENT_SESSION_LIFETIME = get_env_int('PERMANENT_SESSION_LIFETIME', 3600)
    
    # CORS Configuration
    CORS_ALLOWED_ORIGINS = get_env_list('CORS_ALLOWED_ORIGINS', ['http://localhost:3000'])
    CORS_ALLOWED_METHODS = get_env_list('CORS_ALLOWED_METHODS', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    CORS_ALLOWED_HEADERS = get_env_list('CORS_ALLOWED_HEADERS', ['Content-Type', 'Authorization'])
    CORS_EXPOSE_HEADERS = get_env_list('CORS_EXPOSE_HEADERS', ['Content-Range', 'X-Total-Count'])
    CORS_MAX_AGE = int(os.environ.get('CORS_MAX_AGE', 600))
    
    # Security Headers
    STRICT_TRANSPORT_SECURITY = get_env_bool('STRICT_TRANSPORT_SECURITY', True)
    STRICT_TRANSPORT_SECURITY_MAX_AGE = int(os.environ.get('STRICT_TRANSPORT_SECURITY_MAX_AGE', 31536000))
    STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS = get_env_bool('STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS', True)
    STRICT_TRANSPORT_SECURITY_PRELOAD = get_env_bool('STRICT_TRANSPORT_SECURITY_PRELOAD', True)
    
    # Content Security Policy
    CSP_DIRECTIVES = {
        'default-src': ["'self'"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net/"],
        'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net/"],
        'img-src': ["'self'", "data:", "https:"],
        'font-src': ["'self'", "https://cdn.jsdelivr.net/"],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
        'form-action': ["'self'"],
        'base-uri': ["'self'"],
        'frame-src': ["'none'"]
    }
    
    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100/hour')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    
    # API Keys
    GARMIN_CLIENT_ID = os.environ.get('GARMIN_CLIENT_ID')
    GARMIN_CLIENT_SECRET = os.environ.get('GARMIN_CLIENT_SECRET')
    GARMIN_REDIRECT_URI = os.environ.get('GARMIN_REDIRECT_URI', 'http://localhost:5001/garmin/callback')

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    # In development, you might want to disable secure cookies
    SESSION_COOKIE_SECURE = False
    # Allow more lenient CORS in development
    CORS_ALLOWED_ORIGINS = ['*']

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    # Ensure these are set in production
    @classmethod
    def init_app(cls, app):
        # Log a warning if SECRET_KEY is not set
        if not app.config['SECRET_KEY'] or app.config['SECRET_KEY'] == 'generate-a-secure-key-in-production':
            app.logger.warning('SECRET_KEY is not set! Please set it in production.')
        
        # Ensure database URL is set
        if not app.config['SQLALCHEMY_DATABASE_URI'] or app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite'):
            app.logger.warning('Using SQLite in production is not recommended.')
        
        # Ensure mail configuration is set
        if not all([app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD']]):
            app.logger.warning('Email configuration is not complete.')
        
        # Ensure CORS origins are properly set
        if '*' in app.config['CORS_ALLOWED_ORIGINS']:
            app.logger.warning('CORS is allowing all origins in production!')

# Dictionary mapping configuration names to configuration classes
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 