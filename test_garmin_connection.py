from garminconnect import Garmin, GarminConnectConnectionError, GarminConnectAuthenticationError
import logging
from datetime import datetime, timedelta
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_garmin_connection():
    # Test credentials
    email = "a.tselekis@gmail.com"
    password = "Tseleki$1988"
    
    # Debug information
    logger.info("Using test credentials:")
    logger.info(f"GARMIN_EMAIL: {email}")
    logger.info(f"GARMIN_PASSWORD: {'*' * len(password) if password else 'None'}")
    
    try:
        # Initialize client
        client = Garmin(
            email=email,
            password=password,
            is_cn=False
        )
        
        # Try to login
        logger.info("\nAttempting to login...")
        client.login()
        logger.info("✓ Login successful!")
        
        # Get today's date
        today = datetime.now().date()
        
        # Test various data endpoints
        logger.info("\nTesting data access:")
        
        try:
            logger.info("\n1. User Profile:")
            user_profile = client.get_user_profile()
            logger.info("✓ Successfully retrieved user profile")
            logger.info(f"   - Display name: {user_profile.get('displayName', 'N/A')}")
            logger.info(f"   - Full name: {user_profile.get('fullName', 'N/A')}")
            logger.info(f"   - Email: {user_profile.get('emailAddress', 'N/A')}")
        except Exception as e:
            logger.error(f"✗ Could not access user profile: {str(e)}")
        
        try:
            logger.info("\n2. Daily Summary:")
            daily_summary = client.get_last_activity()
            logger.info("✓ Successfully retrieved daily summary")
            logger.info(f"   - Activity type: {daily_summary.get('activityType', 'N/A')}")
            logger.info(f"   - Duration: {daily_summary.get('duration', 'N/A')} seconds")
            logger.info(f"   - Distance: {daily_summary.get('distance', 'N/A')} meters")
        except Exception as e:
            logger.error(f"✗ Could not access daily summary: {str(e)}")
        
        try:
            logger.info("\n3. Heart Rate Data:")
            heart_rate = client.get_heart_rates(today)
            logger.info("✓ Successfully retrieved heart rate data")
            if heart_rate:
                logger.info(f"   - Data points available: {len(heart_rate)}")
                if len(heart_rate) > 0:
                    logger.info(f"   - Latest heart rate: {heart_rate[-1].get('value', 'N/A')} bpm")
        except Exception as e:
            logger.error(f"✗ Could not access heart rate data: {str(e)}")
        
        try:
            logger.info("\n4. Steps Data:")
            steps = client.get_steps_data(today)
            logger.info("✓ Successfully retrieved steps data")
            if steps:
                logger.info(f"   - Data points available: {len(steps)}")
                daily_total = sum(step.get('steps', 0) for step in steps)
                logger.info(f"   - Total steps today: {daily_total}")
        except Exception as e:
            logger.error(f"✗ Could not access steps data: {str(e)}")
        
        try:
            logger.info("\n5. Sleep Data:")
            sleep_data = client.get_sleep_data(today)
            logger.info("✓ Successfully retrieved sleep data")
            if sleep_data:
                logger.info(f"   - Sleep duration: {sleep_data.get('duration', 'N/A')} seconds")
                logger.info(f"   - Deep sleep: {sleep_data.get('deepSleepDuration', 'N/A')} seconds")
                logger.info(f"   - Light sleep: {sleep_data.get('lightSleepDuration', 'N/A')} seconds")
        except Exception as e:
            logger.error(f"✗ Could not access sleep data: {str(e)}")
        
        try:
            logger.info("\n6. Device Information:")
            devices = client.get_devices()
            logger.info("✓ Successfully retrieved device information")
            logger.info(f"   - Number of devices: {len(devices)}")
            for device in devices:
                logger.info(f"   - Device: {device.get('productDisplayName', 'Unknown')} ({device.get('deviceId', 'No ID')})")
        except Exception as e:
            logger.error(f"✗ Could not access device information: {str(e)}")
        
        logger.info("\nConnection test completed!")
        return True
        
    except GarminConnectAuthenticationError as e:
        logger.error(f"\nAuthentication error: {str(e)}")
        logger.error("Please verify:")
        logger.error("1. Your Garmin Connect credentials are correct")
        logger.error("2. Two-factor authentication is disabled on your Garmin account")
        logger.error("3. You can log in to Garmin Connect website manually")
        return False
    except GarminConnectConnectionError as e:
        logger.error(f"\nConnection error: {str(e)}")
        logger.error("Please check your internet connection")
        return False
    except Exception as e:
        logger.error(f"\nUnexpected error: {str(e)}")
        logger.error("Please try again or contact support")
        return False

if __name__ == "__main__":
    test_garmin_connection() 