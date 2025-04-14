from flask import render_template
from app import db

def not_found_error(error):
    """Handle 404 Not Found errors."""
    return render_template('errors/404.html'), 404

def internal_error(error):
    """Handle 500 Internal Server Error."""
    db.session.rollback()  # Roll back any failed database sessions
    return render_template('errors/500.html'), 500 