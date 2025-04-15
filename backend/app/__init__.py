from flask import Flask, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from .config import Config
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure secret key is set
    if not app.config['SECRET_KEY']:
        app.config['SECRET_KEY'] = os.urandom(24)
    
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes import auth, dashboard, meal_plan
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(meal_plan.bp)

    # Root route redirects to dashboard
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    return app 