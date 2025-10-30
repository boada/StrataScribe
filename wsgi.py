"""
WSGI entry point for production deployment.
This file is used by WSGI servers like Gunicorn.
"""
import os
from app import create_app

# Create application instance using production config
config_name = os.environ.get('FLASK_ENV', 'production')
app = create_app(config_name)

if __name__ == "__main__":
    app.run()