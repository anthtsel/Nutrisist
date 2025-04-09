import os
from flask import Flask
from flask_migrate import Migrate
from app import create_app, db
from config import config

def update_database(database_url):
    """Update a specific database with migrations."""
    print(f"\nUpdating database: {database_url}")
    
    # Create app with specific database URL
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Run migrations
    with app.app_context():
        print("Running migrations...")
        os.system('flask db upgrade')
        print("Migrations completed successfully!")

def main():
    # List of databases to update
    databases = [
        'postgresql://postgres:Tseleki$1988@localhost:5432/health_diet_plan',
        'postgresql://postgres:Tseleki$1988@localhost:5432/prod_health_diet_plan',
        # Add any other databases here
    ]
    
    # Update each database
    for db_url in databases:
        try:
            update_database(db_url)
        except Exception as e:
            print(f"Error updating database {db_url}: {str(e)}")

if __name__ == '__main__':
    main() 