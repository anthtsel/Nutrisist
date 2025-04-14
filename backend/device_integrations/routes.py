from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from . import device_integrations
from .. import db
from ..models import User, DeviceConnection
import requests
from datetime import datetime, timedelta
import jwt
from functools import wraps

# Decorator to check if device connection exists
def device_connection_required(platform):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            connection = DeviceConnection.query.filter_by(
                user_id=current_user.id,
                platform=platform
            ).first()
            if not connection:
                flash(f'Please connect your {platform} account first.', 'warning')
                return redirect(url_for('device_integrations.connect', platform=platform))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@device_integrations.route('/devices')
@login_required
def devices():
    """Show connected devices and available integrations."""
    connections = DeviceConnection.query.filter_by(user_id=current_user.id).all()
    return render_template('device_integrations/devices.html', 
                         title='Device Connections',
                         connections=connections)

@device_integrations.route('/connect/<platform>')
@login_required
def connect(platform):
    """Initiate OAuth flow for device connection."""
    if platform not in current_app.config['SUPPORTED_PLATFORMS']:
        flash('Unsupported platform.', 'danger')
        return redirect(url_for('device_integrations.devices'))
    
    # Generate state token for OAuth security
    state = jwt.encode(
        {'user_id': current_user.id, 'platform': platform, 'exp': datetime.utcnow() + timedelta(minutes=5)},
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    # Redirect to platform's OAuth URL
    oauth_url = current_app.config['PLATFORM_CONFIGS'][platform]['auth_url']
    client_id = current_app.config['PLATFORM_CONFIGS'][platform]['client_id']
    redirect_uri = url_for('device_integrations.oauth_callback', platform=platform, _external=True)
    
    auth_url = f"{oauth_url}?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&state={state}"
    return redirect(auth_url)

@device_integrations.route('/callback/<platform>')
@login_required
def oauth_callback(platform):
    """Handle OAuth callback from device platform."""
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        flash('Authorization failed. Please try again.', 'danger')
        return redirect(url_for('device_integrations.devices'))
    
    try:
        # Verify state token
        state_data = jwt.decode(state, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if state_data['user_id'] != current_user.id or state_data['platform'] != platform:
            flash('Invalid authorization state.', 'danger')
            return redirect(url_for('device_integrations.devices'))
    except:
        flash('Invalid authorization state.', 'danger')
        return redirect(url_for('device_integrations.devices'))
    
    # Exchange code for access token
    config = current_app.config['PLATFORM_CONFIGS'][platform]
    token_url = config['token_url']
    client_id = config['client_id']
    client_secret = config['client_secret']
    redirect_uri = url_for('device_integrations.oauth_callback', platform=platform, _external=True)
    
    try:
        response = requests.post(token_url, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        })
        response.raise_for_status()
        token_data = response.json()
    except:
        flash('Failed to connect to platform. Please try again.', 'danger')
        return redirect(url_for('device_integrations.devices'))
    
    # Store connection
    connection = DeviceConnection(
        user_id=current_user.id,
        platform=platform,
        access_token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_expires_at=datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
    )
    
    try:
        db.session.add(connection)
        db.session.commit()
        flash(f'Successfully connected to {platform}!', 'success')
    except:
        db.session.rollback()
        flash('Failed to save connection. Please try again.', 'danger')
    
    return redirect(url_for('device_integrations.devices'))

@device_integrations.route('/disconnect/<platform>')
@login_required
@device_connection_required(platform)
def disconnect(platform):
    """Disconnect device platform."""
    connection = DeviceConnection.query.filter_by(
        user_id=current_user.id,
        platform=platform
    ).first()
    
    try:
        db.session.delete(connection)
        db.session.commit()
        flash(f'Successfully disconnected from {platform}.', 'success')
    except:
        db.session.rollback()
        flash('Failed to disconnect. Please try again.', 'danger')
    
    return redirect(url_for('device_integrations.devices'))

@device_integrations.route('/sync/<platform>')
@login_required
@device_connection_required(platform)
def sync(platform):
    """Trigger manual sync for a specific platform."""
    connection = DeviceConnection.query.filter_by(
        user_id=current_user.id,
        platform=platform
    ).first()
    
    try:
        # Refresh token if needed
        if connection.token_expires_at < datetime.utcnow():
            refresh_token(connection)
        
        # Sync data based on platform
        if platform == 'garmin':
            sync_garmin_data(connection)
        elif platform == 'apple':
            sync_apple_data(connection)
        elif platform == 'whoop':
            sync_whoop_data(connection)
        elif platform == 'oura':
            sync_oura_data(connection)
        elif platform == 'peloton':
            sync_peloton_data(connection)
        elif platform == 'samsung':
            sync_samsung_data(connection)
        elif platform == 'zwift':
            sync_zwift_data(connection)
        elif platform == 'fitbit':
            sync_fitbit_data(connection)
        
        flash(f'Successfully synced data from {platform}.', 'success')
    except Exception as e:
        current_app.logger.error(f"Sync error for {platform}: {str(e)}")
        flash(f'Failed to sync data from {platform}. Please try again.', 'danger')
    
    return redirect(url_for('device_integrations.devices'))

def refresh_token(connection):
    """Refresh OAuth token for a connection."""
    config = current_app.config['PLATFORM_CONFIGS'][connection.platform]
    token_url = config['token_url']
    client_id = config['client_id']
    client_secret = config['client_secret']
    
    try:
        response = requests.post(token_url, data={
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': connection.refresh_token,
            'grant_type': 'refresh_token'
        })
        response.raise_for_status()
        token_data = response.json()
        
        connection.access_token = token_data['access_token']
        connection.refresh_token = token_data.get('refresh_token', connection.refresh_token)
        connection.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))
        db.session.commit()
    except:
        db.session.rollback()
        raise

# Platform-specific sync functions
def sync_garmin_data(connection):
    """Sync data from Garmin Connect."""
    # Implement Garmin API sync
    pass

def sync_apple_data(connection):
    """Sync data from Apple Health."""
    # Implement Apple Health API sync
    pass

def sync_whoop_data(connection):
    """Sync data from Whoop."""
    # Implement Whoop API sync
    pass

def sync_oura_data(connection):
    """Sync data from Oura Ring."""
    # Implement Oura API sync
    pass

def sync_peloton_data(connection):
    """Sync data from Peloton."""
    # Implement Peloton API sync
    pass

def sync_samsung_data(connection):
    """Sync data from Samsung Health."""
    # Implement Samsung Health API sync
    pass

def sync_zwift_data(connection):
    """Sync data from Zwift."""
    # Implement Zwift API sync
    pass

def sync_fitbit_data(connection):
    """Sync data from Fitbit."""
    # Implement Fitbit API sync
    pass 