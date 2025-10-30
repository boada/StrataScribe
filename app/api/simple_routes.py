"""
Simple routes for testing the application factory pattern.

This version avoids legacy imports to test the factory works.
"""
from flask import Blueprint, render_template

# Create blueprint
bp = Blueprint('main', __name__)


@bp.route("/")
def home():
    """Simple home route for testing."""
    return "<h1>StrataScribe</h1><p>Application factory working! ✅</p>"


@bp.route("/about")
def about():
    """Simple about route.""" 
    return "<h1>About</h1><p>Modern Flask application with clean architecture.</p>"


@bp.route("/health")
def health_check():
    """Health check endpoint."""
    from app.config import get_config
    config = get_config()
    return {
        "status": "healthy",
        "debug": config.DEBUG,
        "supported_extensions": list(config.SUPPORTED_EXTENSIONS)
    }