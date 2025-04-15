# MongoDB schemas for wearable data
# We use Python dictionaries to represent MongoDB schemas

# User Wearable Data Schema
wearable_data_schema = {
    "user_id": str,  # Link to PostgreSQL user ID
    "device_type": str,  # fitbit, apple_watch, garmin, etc.
    "device_id": str,  # Unique identifier for the device
    "last_sync": dict,  # Timestamp of last synchronization
    "auth_token": str,  # OAuth token or API key (encrypted)
    "auth_expires": dict,  # Token expiration date
}

# Daily Activity Schema
daily_activity_schema = {
    "user_id": str,  # Link to PostgreSQL user ID
    "date": dict,  # Date of activity data
    "device_id": str,  # Reference to the wearable device
    
    # Activity metrics
    "steps": int,  # Total steps
    "distance": float,  # Distance in kilometers
    "floors_climbed": int,  # Number of floors climbed
    "calories_burned": int,  # Total calories burned
    "active_minutes": {
        "sedentary": int,  # Minutes of sedentary activity
        "lightly_active": int,  # Minutes of light activity
        "fairly_active": int,  # Minutes of moderate activity
        "very_active": int,  # Minutes of intense activity
    },
    
    # Heart rate data
    "heart_rate": {
        "resting": int,  # Resting heart rate
        "min": int,  # Minimum heart rate
        "max": int,  # Maximum heart rate
        "avg": int,  # Average heart rate
        "zones": {
            "out_of_range": int,  # Minutes in out-of-range zone
            "fat_burn": int,  # Minutes in fat burn zone
            "cardio": int,  # Minutes in cardio zone
            "peak": int,  # Minutes in peak zone
        }
    },
    
    # Raw activity time series (hourly)
    "hourly_steps": [
        {
            "time": dict,  # Hour timestamp
            "value": int,  # Steps during this hour
        }
    ],
    
    # Raw heart rate time series
    "heart_rate_intraday": [
        {
            "time": dict,  # Timestamp
            "value": int,  # Heart rate at this time
        }
    ],
    
    # Metadata
    "source": str,  # Data source (e.g., "fitbit_api", "apple_healthkit")
    "is_complete": bool,  # Whether this is a complete day of data
}

# Sleep Data Schema
sleep_schema = {
    "user_id": str,  # Link to PostgreSQL user ID
    "date": dict,  # Date of sleep (starting night)
    "device_id": str,  # Reference to the wearable device
    
    # Sleep metrics
    "sleep_duration": float,  # Total sleep time in hours
    "time_in_bed": float,  # Total time in bed in hours
    "efficiency": int,  # Sleep efficiency percentage
    
    # Sleep stages
    "sleep_stages": {
        "deep": float,  # Time in deep sleep (hours)
        "light": float,  # Time in light sleep (hours)
        "rem": float,  # Time in REM sleep (hours)
        "awake": float,  # Time awake during sleep (hours)
    },
    
    # Sleep records
    "sleep_records": [
        {
            "start_time": dict,  # When sleep started
            "end_time": dict,  # When sleep ended
            "duration": float,  # Duration in hours
            "is_main_sleep": bool,  # Whether this is the main sleep (vs. nap)
        }
    ],
    
    # Sleep stage timeline (for visualization)
    "sleep_stages_timeline": [
        {
            "time": dict,  # Timestamp
            "stage": str,  # Sleep stage (deep, light, rem, awake)
        }
    ],
    
    # Metadata
    "source": str,  # Data source
    "is_complete": bool,  # Whether this is a complete night of data
}

# Aggregated Wearable Data Schema (for meal plan generation)
wearable_aggregated_schema = {
    "user_id": str,  # Link to PostgreSQL user ID
    "date_range": {
        "start": dict,  # Start date of aggregation
        "end": dict,  # End date of aggregation
    },
    
    # Activity aggregates
    "avg_daily_steps": int,  # Average steps per day
    "avg_daily_calories_burned": int,  # Average calories burned per day
    "avg_active_minutes": int,  # Average active minutes per day
    "avg_resting_heart_rate": int,  # Average resting heart rate
    
    # Sleep aggregates
    "avg_sleep_duration": float,  # Average sleep duration in hours
    "avg_deep_sleep": float,  # Average deep sleep in hours
    "avg_sleep_efficiency": int,  # Average sleep efficiency percentage
    
    # Activity classification
    "activity_level": str,  # sedentary, lightly_active, moderately_active, very_active
    "sleep_quality": str,  # poor, fair, good, excellent
    
    # Calculated fields for meal planning
    "estimated_bmr": int,  # Basal Metabolic Rate based on user profile and wearable data
    "recommended_calories": int,  # Recommended daily calorie intake
    "recommended_macros": {
        "protein": int,  # Recommended protein in grams
        "carbs": int,  # Recommended carbs in grams
        "fat": int,  # Recommended fat in grams
    },
    
    # Metadata
    "generated_at": dict,  # When this aggregation was created
    "is_complete": bool,  # Whether data covers the entire period
}

# Define a Python class to interact with MongoDB collections
class MongoModels:
    WEARABLE_DATA_COLLECTION = "wearable_connections"
    DAILY_ACTIVITY_COLLECTION = "daily_activities"
    SLEEP_DATA_COLLECTION = "sleep_data"
    AGGREGATED_DATA_COLLECTION = "aggregated_wearable_data"
    
    @staticmethod
    def get_collection_schemas():
        return {
            MongoModels.WEARABLE_DATA_COLLECTION: wearable_data_schema,
            MongoModels.DAILY_ACTIVITY_COLLECTION: daily_activity_schema,
            MongoModels.SLEEP_DATA_COLLECTION: sleep_schema,
            MongoModels.AGGREGATED_DATA_COLLECTION: wearable_aggregated_schema
        }