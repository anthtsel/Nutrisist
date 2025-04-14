from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from config import config
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
mail = Mail()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    Migrate(app, db)
    
    # Initialize CORS
    CORS(app, resources={
        r"/*": {
            "origins": app.config['CORS_ALLOWED_ORIGINS'],
            "methods": app.config['CORS_ALLOWED_METHODS'],
            "allow_headers": app.config['CORS_ALLOWED_HEADERS'],
            "expose_headers": app.config['CORS_EXPOSE_HEADERS'],
            "max_age": app.config['CORS_MAX_AGE'],
            "supports_credentials": True
        }
    })
    
    # Handle proxy headers for HTTPS
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)
    
    # Add context processor for template variables
    @app.context_processor
    def utility_processor():
        return {
            'now': datetime.utcnow()
        }
    
    # User loader for Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    from .health_insights import health_insights as health_insights_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(health_insights_blueprint, url_prefix='/health-insights')
    
    @app.after_request
    def add_security_headers(response):
        # HTTP Strict Transport Security
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net/; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net/; "
            "font-src 'self' https://cdn.jsdelivr.net/; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        
        # X-Content-Type-Options
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # X-Frame-Options
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # X-XSS-Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    @app.before_request
    def force_https():
        if not request.is_secure and app.config['ENV'] == 'production':
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    
    return app

from app import models 