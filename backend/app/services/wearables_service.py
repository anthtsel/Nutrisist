from datetime import datetime, timedelta
from flask import current_app
from app import mongo, db
from app.models.models import User, UserProfile

class WearableService:
    """Service for interacting with wearable data in MongoDB and handling device connections"""
    
    @staticmethod
    def connect_device(user_id, device_type, auth_data):
        """
        Connect a wearable device for a user
        
        Args:
            user_id: The PostgreSQL user ID
            device_type: Type of wearable (fitbit, apple_watch, etc.)
            auth_data: Authentication data from OAuth or direct connection
            
        Returns:
            bool: Success status
        """
        try:
            # Update user profile in PostgreSQL
            user_profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not user_profile:
                return False
                
            user_profile.wearable_connected = True
            user_profile.wearable_type = device_type
            user_profile.wearable_id = auth_data.get('device_id')
            user_profile.last_sync = datetime.utcnow()
            
            db.session.commit()
            
            # Store wearable connection in MongoDB
            wearable_data = {
                "user_id": str(user_id),
                "device_type": device_type,
                "device_id": auth_data.get('device_id'),
                "last_sync": datetime.utcnow(),
                "auth_token": auth_data.get('access_token'),
                "auth_expires": datetime.utcnow() + timedelta(days=30),  # Assuming 30-day token
            }
            
            # Upsert the wearable connection data
            mongo.db.wearable_connections.update_one(
                {"user_id": str(user_id)},
                {"$set": wearable_data},
                upsert=True
            )
            
            # Start data sync process (this would typically be an async task)
            WearableService.sync_wearable_data(user_id)
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error connecting device: {str(e)}")
            return False
    
    @staticmethod
    def sync_wearable_data(user_id):
        """
        Sync wearable data from the connected device API
        
        Args:
            user_id: The PostgreSQL user ID
            
        Returns:
            bool: Success status
        """
        try:
            # Get wearable connection info
            connection = mongo.db.wearable_connections.find_one({"user_id": str(user_id)})
            if not connection:
                return False
                
            # In a real application, we would make API calls to the wearable platform
            # using the stored auth_token and device_id
            # For this example, we'll simulate some data
            
            # Get the last 7 days of data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            # Simulate fetching and storing activity data
            for i in range(7):
                current_date = start_date + timedelta(days=i)
                
                # Simulate daily activity data
                activity_data = {
                    "user_id": str(user_id),
                    "date": current_date,
                    "device_id": connection["device_id"],
                    "steps": 8000 + (i * 500),  # Simulated steps
                    "distance": 5.2 + (i * 0.3),  # Simulated distance in km
                    "floors_climbed": 10 + i,
                    "calories_burned": 2000 + (i * 100),
                    "active_minutes": {
                        "sedentary": 960 - (i * 30),
                        "lightly_active": 240 + (i * 10),
                        "fairly_active": 30 + (i * 5),
                        "very_active": 20 + (i * 5)
                    },
                    "heart_rate": {
                        "resting": 65 - i,
                        "min": 55,
                        "max": 140 + (i * 5),
                        "avg": 72 - (i * 2),
                        "zones": {
                            "out_of_range": 1200 - (i * 30),
                            "fat_burn": 180 + (i * 10),
                            "cardio": 45 + (i * 5),
                            "peak": 15 + (i * 3)
                        }
                    },
                    "source": connection["device_type"],
                    "is_complete": True
                }
                
                # Upsert activity data
                mongo.db.daily_activities.update_one(
                    {"user_id": str(user_id), "date": current_date},
                    {"$set": activity_data},
                    upsert=True
                )
                
                # Simulate sleep data
                sleep_data = {
                    "user_id": str(user_id),
                    "date": current_date,
                    "device_id": connection["device_id"],
                    "sleep_duration": 7.5 + (i * 0.1),
                    "time_in_bed": 8.0 + (i * 0.1),
                    "efficiency": 93 + i,
                    "sleep_stages": {
                        "deep": 1.5 + (i * 0.05),
                        "light": 4.0 + (i * 0.1),
                        "rem": 1.8 - (i * 0.05),
                        "awake": 0.3 - (i * 0.02)
                    },
                    "source": connection["device_type"],
                    "is_complete": True
                }
                
                # Upsert sleep data
                mongo.db.sleep_data.update_one(
                    {"user_id": str(user_id), "date": current_date},
                    {"$set": sleep_data},
                    upsert=True
                )
            
            # Generate aggregated data
            WearableService.generate_aggregated_data(user_id, start_date, end_date)
            
            # Update last sync time
            mongo.db.wearable_connections.update_one(
                {"user_id": str(user_id)},
                {"$set": {"last_sync": datetime.utcnow()}}
            )
            
            # Update PostgreSQL user profile
            user_profile = UserProfile.query.filter_by(user_id=user_id).first()
            if user_profile:
                user_profile.last_sync = datetime.utcnow()
                db.session.commit()
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error syncing wearable data: {str(e)}")
            return False
    
    @staticmethod
    def generate_aggregated_data(user_id, start_date, end_date):
        """
        Generate aggregated wearable data for meal planning
        
        Args:
            user_id: The PostgreSQL user ID
            start_date: Start date for aggregation
            end_date: End date for aggregation
            
        Returns:
            dict: Aggregated data
        """
        try:
            # Fetch activity data
            activity_data = list(mongo.db.daily_activities.find({
                "user_id": str(user_id),
                "date": {"$gte": start_date, "$lte": end_date}
            }))
            
            # Fetch sleep data
            sleep_data = list(mongo.db.sleep_data.find({
                "user_id": str(user_id),
                "date": {"$gte": start_date, "$lte": end_date}
            }))
            
            # Skip if no data
            if not activity_data or not sleep_data:
                return None
                
            # Calculate averages
            total_days = len(activity_data)
            
            # Activity averages
            avg_steps = sum(day["steps"] for day in activity_data) / total_days
            avg_calories_burned = sum(day["calories_burned"] for day in activity_data) / total_days
            avg_active_minutes = sum(
                day["active_minutes"]["fairly_active"] + day["active_minutes"]["very_active"] 
                for day in activity_data
            ) / total_days
            avg_resting_hr = sum(day["heart_rate"]["resting"] for day in activity_data) / total_days
            
            # Sleep averages
            avg_sleep_duration = sum(day["sleep_duration"] for day in sleep_data) / len(sleep_data)
            avg_deep_sleep = sum(day["sleep_stages"]["deep"] for day in sleep_data) / len(sleep_data)
            avg_sleep_efficiency = sum(day["efficiency"] for day in sleep_data) / len(sleep_data)
            
            # Determine activity level
            activity_level = "sedentary"
            if avg_steps >= 10000:
                activity_level = "very_active"
            elif avg_steps >= 7500:
                activity_level = "moderately_active"
            elif avg_steps >= 5000:
                activity_level = "lightly_active"
                
            # Determine sleep quality
            # Determine sleep quality
            sleep_quality = "poor"
            if avg_sleep_duration >= 8 and avg_deep_sleep >= 1.5 and avg_sleep_efficiency >= 90:
                sleep_quality = "excellent"
            elif avg_sleep_duration >= 7 and avg_deep_sleep >= 1.2 and avg_sleep_efficiency >= 85:
                sleep_quality = "good"
            elif avg_sleep_duration >= 6 and avg_deep_sleep >= 1.0 and avg_sleep_efficiency >= 80:
                sleep_quality = "fair"
            
            # Get user profile for BMR calculation
            user_profile = UserProfile.query.filter_by(user_id=user_id).first()
            
            # Calculate BMR using Harris-Benedict Equation
            # This is a simplification - in a real app you'd have more complex calculations
            bmr = 0
            if user_profile:
                if user_profile.gender == 'male':
                    bmr = 88.362 + (13.397 * user_profile.weight) + (4.799 * user_profile.height) - (5.677 * user_profile.age)
                else:
                    bmr = 447.593 + (9.247 * user_profile.weight) + (3.098 * user_profile.height) - (4.330 * user_profile.age)
            
            # Adjust BMR based on activity level
            activity_multipliers = {
                "sedentary": 1.2,
                "lightly_active": 1.375,
                "moderately_active": 1.55,
                "very_active": 1.725
            }
            
            estimated_bmr = int(bmr)
            recommended_calories = int(bmr * activity_multipliers.get(activity_level, 1.2))
            
            # Calculate recommended macros
            # Typical distribution: 30% protein, 40% carbs, 30% fat
            recommended_protein = int((recommended_calories * 0.3) / 4)  # 4 calories per gram of protein
            recommended_carbs = int((recommended_calories * 0.4) / 4)    # 4 calories per gram of carbs
            recommended_fat = int((recommended_calories * 0.3) / 9)      # 9 calories per gram of fat
            
            # Create aggregated data document
            aggregated_data = {
                "user_id": str(user_id),
                "date_range": {
                    "start": start_date,
                    "end": end_date,
                },
                "avg_daily_steps": int(avg_steps),
                "avg_daily_calories_burned": int(avg_calories_burned),
                "avg_active_minutes": int(avg_active_minutes),
                "avg_resting_heart_rate": int(avg_resting_hr),
                "avg_sleep_duration": float(avg_sleep_duration),
                "avg_deep_sleep": float(avg_deep_sleep),
                "avg_sleep_efficiency": int(avg_sleep_efficiency),
                "activity_level": activity_level,
                "sleep_quality": sleep_quality,
                "estimated_bmr": estimated_bmr,
                "recommended_calories": recommended_calories,
                "recommended_macros": {
                    "protein": recommended_protein,
                    "carbs": recommended_carbs,
                    "fat": recommended_fat,
                },
                "generated_at": datetime.utcnow(),
                "is_complete": True
            }
            
            # Upsert aggregated data
            mongo.db.aggregated_wearable_data.update_one(
                {
                    "user_id": str(user_id),
                    "date_range.start": start_date,
                    "date_range.end": end_date
                },
                {"$set": aggregated_data},
                upsert=True
            )
            
            return aggregated_data
            
        except Exception as e:
            current_app.logger.error(f"Error generating aggregated data: {str(e)}")
            return None
    
    @staticmethod
    def get_latest_aggregated_data(user_id):
        """
        Get the latest aggregated wearable data for a user
        
        Args:
            user_id: The PostgreSQL user ID
            
        Returns:
            dict: Latest aggregated data
        """
        try:
            # Find the latest aggregated data
            return mongo.db.aggregated_wearable_data.find_one(
                {"user_id": str(user_id)},
                sort=[("generated_at", -1)]
            )
        except Exception as e:
            current_app.logger.error(f"Error getting aggregated data: {str(e)}")
            return None
    
    @staticmethod
    def disconnect_device(user_id):
        """
        Disconnect a wearable device for a user
        
        Args:
            user_id: The PostgreSQL user ID
            
        Returns:
            bool: Success status
        """
        try:
            # Update user profile in PostgreSQL
            user_profile = UserProfile.query.filter_by(user_id=user_id).first()
            if user_profile:
                user_profile.wearable_connected = False
                user_profile.wearable_type = None
                user_profile.wearable_id = None
                user_profile.last_sync = None
                
                db.session.commit()
            
            # Remove wearable connection from MongoDB
            mongo.db.wearable_connections.delete_one({"user_id": str(user_id)})
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error disconnecting device: {str(e)}")
            return False