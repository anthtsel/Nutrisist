from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.user import bp as user_bp
    app.register_blueprint(user_bp, url_prefix='/user')
    
    from app.garmin import bp as garmin_bp
    app.register_blueprint(garmin_bp, url_prefix='/garmin')
    
    from app.health_insights import bp as health_insights_bp
    app.register_blueprint(health_insights_bp, url_prefix='/health-insights')
    
    return app

from app import models 