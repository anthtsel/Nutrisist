from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_pymongo import PyMongo
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()  # PostgreSQL connection
mongo = PyMongo()  # MongoDB connection
jwt = JWTManager()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__, 
                static_folder='../../frontend/public',
                template_folder='../../frontend/templates')
    
    # Load configuration
    from .config import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # MongoDB configuration
    app.config["MONGO_URI"] = os.getenv('MONGODB_URI') + '/' + os.getenv('MONGODB_DB')
    
    # Initialize extensions with app
    db.init_app(app)
    mongo.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    CORS(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # User loader for Flask-Login
    from .models.user import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.meal_plan import meal_plan_bp
    from .routes.wearable import wearable_bp
    from .routes.user import user_bp
    from .routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(meal_plan_bp, url_prefix='/api/meal-plans')
    app.register_blueprint(wearable_bp, url_prefix='/api/wearables')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app