import jwt
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app
from app.ml.config import MLConfig
from app.ml.logger import logger
from app.ml.exceptions import AuthenticationError

class APIAuth:
    """API authentication for ML endpoints."""
    
    def __init__(self):
        self.secret_key = MLConfig.API_SECRET_KEY
        self.token_expiry = MLConfig.API_TOKEN_EXPIRY
        self.algorithm = MLConfig.API_TOKEN_ALGORITHM
    
    def generate_token(
        self,
        user_id: int,
        permissions: list = None,
        expiry: int = None
    ) -> str:
        """Generate JWT token for API authentication."""
        try:
            # Set token payload
            payload = {
                'user_id': user_id,
                'permissions': permissions or [],
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(
                    seconds=expiry or self.token_expiry
                )
            }
            
            # Generate token
            token = jwt.encode(
                payload,
                self.secret_key,
                algorithm=self.algorithm
            )
            
            logger.info(f"Generated API token for user {user_id}")
            
            return token
            
        except Exception as e:
            logger.error(f"Error generating API token: {str(e)}")
            raise AuthenticationError("Failed to generate API token")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check token expiry
            if datetime.utcfromtimestamp(payload['exp']) < datetime.utcnow():
                raise AuthenticationError("Token has expired")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Error validating API token: {str(e)}")
            raise AuthenticationError("Failed to validate API token")
    
    def get_token_from_request(self) -> Optional[str]:
        """Get JWT token from request headers."""
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None
        
        # Check Authorization header format
        if not auth_header.startswith('Bearer '):
            raise AuthenticationError("Invalid Authorization header format")
        
        return auth_header.split(' ')[1]
    
    def require_auth(self, f):
        """Decorator to require API authentication."""
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                # Get token from request
                token = self.get_token_from_request()
                
                if not token:
                    raise AuthenticationError("Missing API token")
                
                # Validate token
                payload = self.validate_token(token)
                
                # Add user info to request context
                request.user_id = payload['user_id']
                request.permissions = payload['permissions']
                
                return f(*args, **kwargs)
                
            except AuthenticationError:
                raise
            except Exception as e:
                logger.error(f"Error in authentication decorator: {str(e)}")
                raise AuthenticationError("Authentication failed")
        
        return decorated
    
    def require_permission(self, permission: str):
        """Decorator to require specific permission."""
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                try:
                    # Get token from request
                    token = self.get_token_from_request()
                    
                    if not token:
                        raise AuthenticationError("Missing API token")
                    
                    # Validate token
                    payload = self.validate_token(token)
                    
                    # Check permission
                    if permission not in payload['permissions']:
                        raise AuthenticationError(
                            f"Permission '{permission}' required"
                        )
                    
                    # Add user info to request context
                    request.user_id = payload['user_id']
                    request.permissions = payload['permissions']
                    
                    return f(*args, **kwargs)
                    
                except AuthenticationError:
                    raise
                except Exception as e:
                    logger.error(f"Error in permission decorator: {str(e)}")
                    raise AuthenticationError("Permission check failed")
            
            return decorated
        return decorator
    
    def refresh_token(self, token: str) -> str:
        """Refresh expired token."""
        try:
            # Validate token (ignore expiry)
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={'verify_exp': False}
            )
            
            # Generate new token
            new_token = self.generate_token(
                user_id=payload['user_id'],
                permissions=payload['permissions']
            )
            
            logger.info(f"Refreshed API token for user {payload['user_id']}")
            
            return new_token
            
        except Exception as e:
            logger.error(f"Error refreshing API token: {str(e)}")
            raise AuthenticationError("Failed to refresh API token")
    
    def revoke_token(self, token: str) -> None:
        """Revoke token (add to blacklist)."""
        try:
            # Validate token
            payload = self.validate_token(token)
            
            # Add token to blacklist
            expiry = datetime.utcfromtimestamp(payload['exp'])
            current_app.redis.setex(
                f"token_blacklist:{token}",
                (expiry - datetime.utcnow()).seconds,
                "revoked"
            )
            
            logger.info(f"Revoked API token for user {payload['user_id']}")
            
        except Exception as e:
            logger.error(f"Error revoking API token: {str(e)}")
            raise AuthenticationError("Failed to revoke API token")
    
    def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked."""
        try:
            # Check if token is in blacklist
            return bool(current_app.redis.get(f"token_blacklist:{token}"))
            
        except Exception as e:
            logger.error(f"Error checking token revocation: {str(e)}")
            raise AuthenticationError("Failed to check token revocation") 