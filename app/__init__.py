"""
StrataScribe Application Package

A modular Flask application for parsing BattleScribe rosters 
and generating stratagem reports using Wahapedia data.
"""
from typing import Optional
from flask import Flask

from app.config import get_config


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Application factory pattern for creating Flask app instances.
    
    Args:
        config_name: Configuration environment ('development', 'production', 'testing')
        
    Returns:
        Configured Flask application instance
    """
    # Use standard Flask app structure - templates/ folder will be found automatically
    app = Flask(__name__)
    
    # Load configuration
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize configuration
    config.init_app(app)
    
    # Register blueprints (import inside function to avoid circular imports)
    from app.api.routes import bp as routes_bp
    app.register_blueprint(routes_bp)
    
    return app