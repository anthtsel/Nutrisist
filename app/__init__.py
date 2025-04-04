from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_cors import CORS
from config import config
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
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
    
    # Root route
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('health_insights.dashboard'))
        return redirect(url_for('auth.login'))
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        # HTTP Strict Transport Security
        if app.config['STRICT_TRANSPORT_SECURITY']:
            hsts_header = f'max-age={app.config["STRICT_TRANSPORT_SECURITY_MAX_AGE"]}'
            if app.config['STRICT_TRANSPORT_SECURITY_INCLUDE_SUBDOMAINS']:
                hsts_header += '; includeSubDomains'
            if app.config['STRICT_TRANSPORT_SECURITY_PRELOAD']:
                hsts_header += '; preload'
            response.headers['Strict-Transport-Security'] = hsts_header
        
        # Content Security Policy
        csp_header = '; '.join(
            f"{key} {' '.join(value)}"
            for key, value in app.config['CSP_DIRECTIVES'].items()
        )
        response.headers['Content-Security-Policy'] = csp_header
        
        # Other security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Ensure cookies are secure
        if app.config['SESSION_COOKIE_SECURE']:
            response.headers['Set-Cookie'] = response.headers.get('Set-Cookie', '') + '; Secure'
        
        return response
    
    # Force HTTPS in production
    @app.before_request
    def force_https():
        if not app.debug and not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)
    
    # Import and register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from .health_insights import health_insights as health_insights_blueprint
    app.register_blueprint(health_insights_blueprint, url_prefix='/health-insights')
    
    # Register error handlers
    from .errors import not_found_error, internal_error
    app.register_error_handler(404, not_found_error)
    app.register_error_handler(500, internal_error)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app

from app import models 