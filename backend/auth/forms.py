from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from .validators import validate_username, validate_email, validate_password
from ..models import User
import re

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        validate_username
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=128),
        validate_password
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64),
        validate_username
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Length(max=120),
        validate_email
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, max=128),
        validate_password
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        Length(min=8, max=128),
        validate_password
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Validate username."""
        # Check if username contains only allowed characters
        if not re.match("^[A-Za-z0-9_-]*$", username.data):
            raise ValidationError('Username can only contain letters, numbers, dashes and underscores')
        
        # Check if username already exists
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please use a different username.')

    def validate_email(self, email):
        """Validate email."""
        user = User.query.filter_by(email=email.data.lower()).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')

    def validate_password(self, password):
        """Validate password strength."""
        if not any(char.isupper() for char in password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in password.data):
            raise ValidationError('Password must contain at least one number')
        if not any(char in '!@#$%^&*()' for char in password.data):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*())')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Length(max=120),
        validate_email
    ])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, max=128),
        validate_password
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        Length(min=8, max=128),
        validate_password
    ])
    submit = SubmitField('Reset Password')

    def validate_password(self, password):
        """Validate password strength."""
        if not any(char.isupper() for char in password.data):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in password.data):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(char.isdigit() for char in password.data):
            raise ValidationError('Password must contain at least one number')
        if not any(char in '!@#$%^&*()' for char in password.data):
            raise ValidationError('Password must contain at least one special character (!@#$%^&*())') 