#!/usr/bin/env python3
"""
Start the new Flask webapp using our clean architecture
"""
import os
from app import create_app

if __name__ == "__main__":
    # Create the Flask app using our factory
    app = create_app('development')
    
    # Run in development mode
    app.run(
        host='0.0.0.0',
        port=5001,  # Use a different port than legacy app
        debug=True
    )