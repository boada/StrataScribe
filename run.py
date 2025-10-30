"""
New application entry point using the application factory pattern.

This replaces the old main.py approach and allows for better testing and configuration.
"""
import os
from app import create_app

# Get environment from environment variable or default to development
config_name = os.environ.get('FLASK_ENV', 'development')

# Create application instance
app = create_app(config_name)

if __name__ == "__main__":
    # Development server
    debug_mode = config_name == 'development'
    app.run(host="0.0.0.0", debug=debug_mode)