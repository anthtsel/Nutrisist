import os
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    FLASK_APP = os.environ.get('FLASK_APP', 'run.py')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
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