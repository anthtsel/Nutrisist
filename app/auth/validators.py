from wtforms.validators import ValidationError
import re
from bleach import clean

def sanitize_string(value):
    """Sanitize a string input by removing any HTML tags and unwanted characters."""
    # Remove any HTML tags and escape special characters
    cleaned = clean(value, strip=True)
    # Remove any non-printable characters
    cleaned = ''.join(char for char in cleaned if char.isprintable())
    return cleaned

def validate_username(form, field):
    """
    Validate username format and sanitize input.
    - Only allows alphanumeric characters, underscores, and hyphens
    - Length between 3 and 64 characters
    - No spaces allowed
    """
    # Sanitize the input first
    username = sanitize_string(field.data)
    
    # Check length after sanitization
    if len(username) < 3 or len(username) > 64:
        raise ValidationError('Username must be between 3 and 64 characters long.')
    
    # Check for valid characters
    if not re.match(r'^[A-Za-z0-9_-]*$', username):
        raise ValidationError('Username can only contain letters, numbers, underscores, and hyphens.')
    
    # No spaces allowed
    if ' ' in username:
        raise ValidationError('Username cannot contain spaces.')
    
    # Update the field data with sanitized value
    field.data = username

def validate_email(form, field):
    """
    Validate email format and sanitize input.
    - Must be a valid email format
    - Length must not exceed 120 characters
    - Converts to lowercase
    """
    # Sanitize the input first
    email = sanitize_string(field.data.lower())
    
    # Check length after sanitization
    if len(email) > 120:
        raise ValidationError('Email must not exceed 120 characters.')
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError('Invalid email address.')
    
    # Update the field data with sanitized value
    field.data = email

def validate_password(form, field):
    """
    Validate password strength and sanitize input.
    - Minimum length of 8 characters
    - Maximum length of 128 characters
    - Must contain at least one uppercase letter
    - Must contain at least one lowercase letter
    - Must contain at least one number
    - Must contain at least one special character
    - No spaces allowed at the beginning or end
    """
    password = field.data.strip()
    
    # Check length
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if len(password) > 128:
        raise ValidationError('Password must not exceed 128 characters.')
    
    # Check for required character types
    if not any(char.isupper() for char in password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not any(char.islower() for char in password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not any(char.isdigit() for char in password):
        raise ValidationError('Password must contain at least one number.')
    if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?' for char in password):
        raise ValidationError('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?)')
    
    # Check for common password patterns
    common_patterns = [
        r'password',
        r'12345',
        r'qwerty',
        r'admin',
        r'letmein',
        r'welcome'
    ]
    lower_password = password.lower()
    for pattern in common_patterns:
        if pattern in lower_password:
            raise ValidationError('Password contains a common pattern that is too easy to guess.')

def validate_text_field(form, field):
    """
    Validate and sanitize general text input.
    - Remove any HTML tags
    - Remove any script tags
    - Remove any unwanted characters
    - Limit length to 1000 characters
    """
    # Sanitize the input
    text = sanitize_string(field.data)
    
    # Check length
    if len(text) > 1000:
        raise ValidationError('Text is too long (maximum is 1000 characters).')
    
    # Update the field data with sanitized value
    field.data = text

def validate_search_query(form, field):
    """
    Validate and sanitize search queries.
    - Remove any HTML tags
    - Remove any script tags
    - Remove any SQL injection attempts
    - Limit length to 100 characters
    """
    # Sanitize the input
    query = sanitize_string(field.data)
    
    # Check length
    if len(query) > 100:
        raise ValidationError('Search query is too long (maximum is 100 characters).')
    
    # Check for SQL injection patterns
    sql_patterns = [
        r'--',
        r';',
        r'DROP',
        r'DELETE',
        r'UPDATE',
        r'INSERT',
        r'SELECT',
        r'UNION',
        r'WHERE'
    ]
    for pattern in sql_patterns:
        if pattern.lower() in query.lower():
            raise ValidationError('Invalid search query.')
    
    # Update the field data with sanitized value
    field.data = query 