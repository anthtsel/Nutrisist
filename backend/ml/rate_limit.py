import time
from typing import Dict, Any
from datetime import datetime, timedelta
from app.ml.config import MLConfig
from app.ml.logger import logger
from app.ml.exceptions import RateLimitError

class RateLimiter:
    """Rate limiter for ML API endpoints."""
    
    def __init__(self):
        self.requests = {}
        self.windows = {}
    
    def _get_window_key(self, user_id: int, endpoint: str) -> str:
        """Get window key for rate limiting."""
        return f"{user_id}:{endpoint}"
    
    def _cleanup_old_windows(self):
        """Clean up old rate limit windows."""
        current_time = time.time()
        for key in list(self.windows.keys()):
            window = self.windows[key]
            if current_time - window['start_time'] > MLConfig.API_RATE_LIMIT_WINDOW:
                del self.windows[key]
                del self.requests[key]
    
    def check_rate_limit(
        self,
        user_id: int,
        endpoint: str,
        request_count: int = 1
    ) -> Dict[str, Any]:
        """Check if request is within rate limit."""
        try:
            # Clean up old windows
            self._cleanup_old_windows()
            
            # Get window key
            window_key = self._get_window_key(user_id, endpoint)
            
            # Get or create window
            if window_key not in self.windows:
                self.windows[window_key] = {
                    'start_time': time.time(),
                    'count': 0
                }
                self.requests[window_key] = []
            
            window = self.windows[window_key]
            requests = self.requests[window_key]
            
            # Check if window has expired
            current_time = time.time()
            if current_time - window['start_time'] > MLConfig.API_RATE_LIMIT_WINDOW:
                window['start_time'] = current_time
                window['count'] = 0
                requests.clear()
            
            # Check rate limit
            if window['count'] + request_count > MLConfig.API_RATE_LIMIT:
                # Calculate time until next window
                time_until_reset = MLConfig.API_RATE_LIMIT_WINDOW - (
                    current_time - window['start_time']
                )
                
                raise RateLimitError(
                    f"Rate limit exceeded. Try again in {time_until_reset:.0f} seconds."
                )
            
            # Update window
            window['count'] += request_count
            requests.append({
                'timestamp': current_time,
                'count': request_count
            })
            
            # Calculate remaining requests and reset time
            remaining_requests = MLConfig.API_RATE_LIMIT - window['count']
            time_until_reset = MLConfig.API_RATE_LIMIT_WINDOW - (
                current_time - window['start_time']
            )
            
            return {
                'remaining': remaining_requests,
                'reset_in': time_until_reset,
                'limit': MLConfig.API_RATE_LIMIT
            }
            
        except RateLimitError:
            raise
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            raise RateLimitError("Failed to check rate limit")
    
    def get_rate_limit_status(
        self,
        user_id: int,
        endpoint: str
    ) -> Dict[str, Any]:
        """Get current rate limit status."""
        try:
            # Clean up old windows
            self._cleanup_old_windows()
            
            # Get window key
            window_key = self._get_window_key(user_id, endpoint)
            
            # Get window
            if window_key not in self.windows:
                return {
                    'remaining': MLConfig.API_RATE_LIMIT,
                    'reset_in': MLConfig.API_RATE_LIMIT_WINDOW,
                    'limit': MLConfig.API_RATE_LIMIT,
                    'used': 0
                }
            
            window = self.windows[window_key]
            current_time = time.time()
            
            # Check if window has expired
            if current_time - window['start_time'] > MLConfig.API_RATE_LIMIT_WINDOW:
                return {
                    'remaining': MLConfig.API_RATE_LIMIT,
                    'reset_in': MLConfig.API_RATE_LIMIT_WINDOW,
                    'limit': MLConfig.API_RATE_LIMIT,
                    'used': 0
                }
            
            # Calculate remaining requests and reset time
            remaining_requests = MLConfig.API_RATE_LIMIT - window['count']
            time_until_reset = MLConfig.API_RATE_LIMIT_WINDOW - (
                current_time - window['start_time']
            )
            
            return {
                'remaining': remaining_requests,
                'reset_in': time_until_reset,
                'limit': MLConfig.API_RATE_LIMIT,
                'used': window['count']
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {str(e)}")
            raise RateLimitError("Failed to get rate limit status")
    
    def reset_rate_limit(
        self,
        user_id: int,
        endpoint: str
    ) -> None:
        """Reset rate limit for user and endpoint."""
        try:
            # Get window key
            window_key = self._get_window_key(user_id, endpoint)
            
            # Reset window
            if window_key in self.windows:
                del self.windows[window_key]
                del self.requests[window_key]
            
            logger.info(
                f"Reset rate limit - User: {user_id}, "
                f"Endpoint: {endpoint}"
            )
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {str(e)}")
            raise RateLimitError("Failed to reset rate limit")
    
    def get_all_rate_limits(self) -> Dict[str, Any]:
        """Get all current rate limits."""
        try:
            # Clean up old windows
            self._cleanup_old_windows()
            
            # Get current time
            current_time = time.time()
            
            # Format rate limits
            rate_limits = {}
            for key, window in self.windows.items():
                user_id, endpoint = key.split(':')
                time_until_reset = MLConfig.API_RATE_LIMIT_WINDOW - (
                    current_time - window['start_time']
                )
                
                if time_until_reset > 0:
                    rate_limits[key] = {
                        'user_id': int(user_id),
                        'endpoint': endpoint,
                        'used': window['count'],
                        'remaining': MLConfig.API_RATE_LIMIT - window['count'],
                        'reset_in': time_until_reset,
                        'limit': MLConfig.API_RATE_LIMIT
                    }
            
            return rate_limits
            
        except Exception as e:
            logger.error(f"Error getting all rate limits: {str(e)}")
            raise RateLimitError("Failed to get all rate limits") 