import os
from app import create_app, db
from flask_migrate import Migrate

# Get environment
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if env == 'production':
        # In production, use SSL certificate
        ssl_context = (
            os.environ.get('SSL_CERT_PATH', 'cert.pem'),
            os.environ.get('SSL_KEY_PATH', 'key.pem')
        )
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 443)),
            ssl_context=ssl_context
        )
    else:
        # In development, run without SSL
        app.run(
            host='0.0.0.0',
            port=int(os.environ.get('PORT', 5001)),
            debug=True
        ) 