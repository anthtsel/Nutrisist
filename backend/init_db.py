from app import create_app, db
from app.models import User

def init_db():
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_db() 