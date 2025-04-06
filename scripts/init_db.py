import os
from app import create_app, db
from pymongo import MongoClient
from dotenv import load_dotenv
from app.models.time_series_metrics import TimeSeriesMetrics
from app.models.alerts import AlertStore, MealTracking

# Load environment variables
load_dotenv()

def init_postgres():
    """Initialize PostgreSQL database."""
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        print("PostgreSQL database initialized successfully!")

def init_mongo():
    """Initialize MongoDB database."""
    # Connect to MongoDB
    client = MongoClient(os.getenv('MONGO_URI'))
    db = client[os.getenv('MONGO_DB')]
    
    # Create collections
    collections = [
        'health_data',
        'predictions',
        'training_data',
        'device_data',
        'time_series_metrics',
        'alerts',           # New collection for alerts
        'meal_tracking'     # New collection for meal tracking
    ]
    
    for collection in collections:
        if collection not in db.list_collection_names():
            db.create_collection(collection)
            print(f"MongoDB collection '{collection}' created successfully!")
    
    # Create indexes
    db.health_data.create_index([('user_id', 1), ('timestamp', 1)])
    db.predictions.create_index([('user_id', 1), ('timestamp', 1)])
    db.training_data.create_index([('timestamp', 1)])
    db.device_data.create_index([('user_id', 1), ('timestamp', 1)])
    db.device_data.create_index([('device_type', 1), ('data_type', 1)])
    db.device_data.create_index([('processed', 1)])
    
    # Create indexes for time-series metrics
    time_series = TimeSeriesMetrics()
    time_series.create_indexes()
    
    # Create indexes for alerts
    alert_store = AlertStore()
    alert_store.create_indexes()
    
    # Create indexes for meal tracking
    meal_tracking = MealTracking()
    meal_tracking.create_indexes()
    
    print("MongoDB database initialized successfully!")

if __name__ == '__main__':
    print("Initializing databases...")
    init_postgres()
    init_mongo()
    print("All databases initialized successfully!") 