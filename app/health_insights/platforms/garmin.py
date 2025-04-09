"""
Garmin platform integration for health data.
"""
import os
import requests
from datetime import datetime, timedelta
from flask import current_app, session
from app.models import User
from app import db

class GarminPlatform:
    def __init__(self, user_id):
        self.user_id = user_id
        self.user = User.query.get(user_id)
        self.access_token = self.user.garmin_access_token
        self.refresh_token = self.user.garmin_refresh_token
        self.token_expires_at = self.user.garmin_token_expires_at
        self.base_url = "https://api.garmin.com/wellness-api/rest"
        self.oauth_url = "https://connect.garmin.com/oauthConfirm"
        self.token_url = "https://connect.garmin.com/oauth-service/oauth/access_token"
        self.request_token_url = "https://connect.garmin.com/oauth-service/oauth/request_token"
        self.authorize_url = "https://connect.garmin.com/oauthConfirm"

    def get_headers(self):
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json"
        }

    def refresh_access_token(self):
        """Refresh the access token if expired."""
        if datetime.utcnow() >= self.token_expires_at:
            data = {
                "client_id": current_app.config['GARMIN_CLIENT_ID'],
                "client_secret": current_app.config['GARMIN_CLIENT_SECRET'],
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token"
            }
            
            response = requests.post(self.token_url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.refresh_token = token_data['refresh_token']
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
                
                # Update user tokens
                self.user.garmin_access_token = self.access_token
                self.user.garmin_refresh_token = self.refresh_token
                self.user.garmin_token_expires_at = self.token_expires_at
                db.session.commit()
                return True
            return False
        return True

    def fetch_activity_data(self, start_date, end_date):
        """Fetch activity data from Garmin."""
        if not self.refresh_access_token():
            return None

        url = f"{self.base_url}/activities"
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return None

    def fetch_sleep_data(self, start_date, end_date):
        """Fetch sleep data from Garmin."""
        if not self.refresh_access_token():
            return None

        url = f"{self.base_url}/sleep"
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return None

    def fetch_heart_rate_data(self, start_date, end_date):
        """Fetch heart rate data from Garmin."""
        if not self.refresh_access_token():
            return None

        url = f"{self.base_url}/heartRate"
        params = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d")
        }
        
        response = requests.get(url, headers=self.get_headers(), params=params)
        if response.status_code == 200:
            return response.json()
        return None

    def normalize_activity_data(self, data):
        """Normalize Garmin activity data to our format."""
        normalized_data = []
        for activity in data:
            normalized_activity = {
                'date': datetime.strptime(activity['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ').date(),
                'steps': activity.get('steps', 0),
                'distance': activity.get('distance', 0),
                'calories': activity.get('calories', 0),
                'active_minutes': activity.get('activeMinutes', 0),
                'platform': 'garmin'
            }
            normalized_data.append(normalized_activity)
        return normalized_data

    def normalize_sleep_data(self, data):
        """Normalize Garmin sleep data to our format."""
        normalized_data = []
        for sleep in data:
            normalized_sleep = {
                'date': datetime.strptime(sleep['startTime'], '%Y-%m-%dT%H:%M:%S.%fZ').date(),
                'total_sleep': sleep.get('totalSleep', 0),
                'deep_sleep': sleep.get('deepSleep', 0),
                'light_sleep': sleep.get('lightSleep', 0),
                'rem_sleep': sleep.get('remSleep', 0),
                'awake_time': sleep.get('awakeTime', 0),
                'platform': 'garmin'
            }
            normalized_data.append(normalized_sleep)
        return normalized_data

    def normalize_heart_rate_data(self, data):
        """Normalize Garmin heart rate data to our format."""
        normalized_data = []
        for hr in data:
            normalized_hr = {
                'date': datetime.strptime(hr['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ').date(),
                'resting_heart_rate': hr.get('restingHeartRate', 0),
                'max_heart_rate': hr.get('maxHeartRate', 0),
                'min_heart_rate': hr.get('minHeartRate', 0),
                'avg_heart_rate': hr.get('avgHeartRate', 0),
                'platform': 'garmin'
            }
            normalized_data.append(normalized_hr)
        return normalized_data

    def fetch_and_normalize_data(self, start_date, end_date):
        """Fetch and normalize all Garmin data."""
        activity_data = self.fetch_activity_data(start_date, end_date)
        sleep_data = self.fetch_sleep_data(start_date, end_date)
        heart_rate_data = self.fetch_heart_rate_data(start_date, end_date)

        normalized_data = {
            'activity': self.normalize_activity_data(activity_data) if activity_data else [],
            'sleep': self.normalize_sleep_data(sleep_data) if sleep_data else [],
            'heart_rate': self.normalize_heart_rate_data(heart_rate_data) if heart_rate_data else []
        }

        return normalized_data 