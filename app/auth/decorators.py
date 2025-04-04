from functools import wraps
from flask import abort, current_app
from flask_login import current_user
from ..models import UserRole

def role_required(role):
    """Decorator to require specific role for access."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if not current_user.has_role(role):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role."""
    return role_required(UserRole.ADMIN)(f)

def verified_required(f):
    """Decorator to require email verification."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.email_verified:
            abort(403, description="Please verify your email address to access this feature.")
        return f(*args, **kwargs)
    return decorated_function

def check_locked(f):
    """Decorator to check if account is locked."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.is_locked():
            abort(403, description="Account is temporarily locked due to too many failed login attempts.")
        return f(*args, **kwargs)
    return decorated_function 