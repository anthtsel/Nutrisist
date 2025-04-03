from flask import render_template, jsonify, current_app, redirect, url_for, session, request
from flask_login import login_required, current_user
from app.garmin import bp
from garminconnect import Garmin, GarminConnectConnectionError, GarminConnectAuthenticationError
from datetime import datetime
import logging
import urllib3
import traceback
import requests
from urllib.parse import urlencode

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth2 configuration
GARMIN_OAUTH_URL = "https://connect.garmin.com/oauthConfirm"
GARMIN_TOKEN_URL = "https://connectapi.garmin.com/oauth-service/oauth/access_token"
GARMIN_SCOPE = "activity.read heart_rate.read sleep.read steps.read"

@bp.route('/dashboard')
@login_required
def garmin_dashboard():
    return render_template('garmin/dashboard.html')

@bp.route('/connect')
@login_required
def connect_garmin():
    try:
        # Get OAuth credentials from config
        client_id = current_app.config.get('GARMIN_CLIENT_ID')
        client_secret = current_app.config.get('GARMIN_CLIENT_SECRET')
        redirect_uri = current_app.config.get('GARMIN_REDIRECT_URI', 'http://localhost:5001/garmin/callback')
        
        if not client_id or not client_secret:
            logger.error("Missing Garmin OAuth credentials in config")
            return jsonify({
                'status': 'error',
                'message': 'Garmin OAuth credentials not configured. Please check your .env file.'
            }), 400

        # Generate OAuth authorization URL
        auth_params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': GARMIN_SCOPE,
            'state': 'garmin_oauth_state'  # You might want to generate a random state
        }
        
        auth_url = f"{GARMIN_OAUTH_URL}?{urlencode(auth_params)}"
        
        return jsonify({
            'status': 'redirect',
            'message': 'Redirecting to Garmin OAuth...',
            'auth_url': auth_url
        })
        
    except Exception as e:
        logger.error(f"Error initiating OAuth flow: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Error initiating OAuth flow: {str(e)}'
        }), 400

@bp.route('/callback')
@login_required
def garmin_callback():
    try:
        # Get OAuth credentials from config
        client_id = current_app.config.get('GARMIN_CLIENT_ID')
        client_secret = current_app.config.get('GARMIN_CLIENT_SECRET')
        redirect_uri = current_app.config.get('GARMIN_REDIRECT_URI', 'http://localhost:5001/garmin/callback')
        
        # Get authorization code from callback
        code = request.args.get('code')
        if not code:
            return jsonify({
                'status': 'error',
                'message': 'No authorization code received from Garmin'
            }), 400

        # Exchange code for access token
        token_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri
        }
        
        response = requests.post(GARMIN_TOKEN_URL, data=token_data)
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to exchange authorization code for access token'
            }), 400
            
        token_info = response.json()
        access_token = token_info.get('access_token')
        refresh_token = token_info.get('refresh_token')
        
        # Store tokens in session
        session['garmin_access_token'] = access_token
        session['garmin_refresh_token'] = refresh_token
        
        # Initialize Garmin client with access token
        client = Garmin(access_token=access_token)
        
        # Get today's date
        today = datetime.now().date()
        logger.info(f"Fetching data for date: {today}")
        
        # Collect data from working endpoints
        data = {}
        
        try:
            logger.info("Fetching heart rate data...")
            data['heart_rate'] = client.get_heart_rates(today)
            logger.info("Successfully fetched heart rate data")
        except Exception as e:
            logger.error(f"Error fetching heart rate data: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            data['heart_rate'] = []
            
        try:
            logger.info("Fetching steps data...")
            data['steps'] = client.get_steps_data(today)
            logger.info("Successfully fetched steps data")
        except Exception as e:
            logger.error(f"Error fetching steps data: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            data['steps'] = []
            
        try:
            logger.info("Fetching sleep data...")
            data['sleep'] = client.get_sleep_data(today)
            logger.info("Successfully fetched sleep data")
        except Exception as e:
            logger.error(f"Error fetching sleep data: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            data['sleep'] = None
            
        try:
            logger.info("Fetching device information...")
            data['devices'] = client.get_devices()
            logger.info("Successfully fetched device information")
        except Exception as e:
            logger.error(f"Error fetching device information: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            data['devices'] = []
        
        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to Garmin',
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({
            'status': 'error',
            'message': f'Error in OAuth callback: {str(e)}'
        }), 400

@bp.route('/data')
@login_required
def get_garmin_data():
    try:
        # Get credentials from config
        email = current_app.config.get('GARMIN_EMAIL')
        password = current_app.config.get('GARMIN_PASSWORD')
        
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Garmin credentials not configured.'
            }), 400

        # Initialize client
        client = Garmin(
            email=email,
            password=password,
            is_cn=False
        )
        
        # Login
        client.login()
        
        # Get today's date
        today = datetime.now().date()
        
        # Get data from working endpoints
        data = {
            'heart_rate': client.get_heart_rates(today),
            'steps': client.get_steps_data(today),
            'sleep': client.get_sleep_data(today),
            'devices': client.get_devices()
        }
        
        return jsonify({
            'status': 'success',
            'data': data
        })
        
    except Exception as e:
        logger.error(f"Error fetching Garmin data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error fetching Garmin data: {str(e)}'
        }), 400 