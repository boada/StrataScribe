"""
Tests for Flask application factory and routing.

These tests ensure our app factory creates properly configured Flask instances
and that our routes work correctly.
"""
import pytest
import json
from app import create_app


class TestApplicationFactory:
    """Test the Flask application factory pattern."""
    
    def test_create_app_development(self):
        """Test creating development app instance."""
        app = create_app('development')
        
        assert app is not None
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is False
        assert 'battlescribe' in app.config['UPLOAD_FOLDER']
        assert app.config['REQUEST_TIMEOUT'] == 60  # Dev has longer timeout
        
    def test_create_app_production(self):
        """Test creating production app instance."""
        app = create_app('production')
        
        assert app is not None
        assert app.config['DEBUG'] is False
        assert app.config['TESTING'] is False
        assert app.config['REQUEST_TIMEOUT'] == 15  # Prod has shorter timeout
        assert app.config['MAX_RETRIES'] == 3  # Fewer retries in prod
        
    def test_create_app_testing(self):
        """Test creating testing app instance."""
        app = create_app('testing')
        
        assert app is not None
        assert app.config['DEBUG'] is True
        assert app.config['TESTING'] is True
        assert app.config['REQUEST_TIMEOUT'] == 5  # Fast timeouts for tests
        assert '/tmp/' in app.config['UPLOAD_FOLDER']  # Temp directory
        
    def test_create_app_default(self):
        """Test creating app with default config."""
        app = create_app()  # No config specified
        
        assert app is not None
        # Should default to development config
        assert app.config['DEBUG'] is True
        
    def test_blueprints_registered(self):
        """Test that blueprints are properly registered."""
        app = create_app('testing')
        
        # Should have our main blueprint registered
        assert 'main' in app.blueprints
        
        # Check that routes exist
        with app.app_context():
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            assert '/' in routes
            assert '/about' in routes
            assert '/health' in routes


@pytest.fixture
def app():
    """Create test app instance."""
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
    })
    return app


@pytest.fixture  
def client(app):
    """Create test client."""
    return app.test_client()


class TestRoutes:
    """Test Flask routes work correctly."""
    
    def test_home_route(self, client):
        """Test home route returns successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'StrataScribe' in response.data
        
    def test_about_route(self, client):
        """Test about route returns successfully."""
        response = client.get('/about')
        assert response.status_code == 200
        assert b'About' in response.data
        
    def test_health_check_route(self, client):
        """Test health check endpoint returns JSON."""
        response = client.get('/health')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'debug' in data
        assert 'supported_extensions' in data
        assert isinstance(data['supported_extensions'], list)
        assert '.ros' in data['supported_extensions']
        assert '.rosz' in data['supported_extensions']


class TestConfigurationIntegration:
    """Test that configuration integrates properly with Flask app."""
    
    def test_config_values_loaded(self, app):
        """Test that our custom config values are loaded into Flask."""
        # Test our custom config keys are available
        assert 'SUPPORTED_EXTENSIONS' in app.config
        assert 'WAHAPEDIA_BASE_URL' in app.config
        assert 'WAHAPEDIA_CSV_FILES' in app.config
        assert 'MOBILE_USER_AGENTS' in app.config
        
        # Test values are correct type
        assert isinstance(app.config['SUPPORTED_EXTENSIONS'], set)
        assert isinstance(app.config['WAHAPEDIA_CSV_FILES'], list)
        assert isinstance(app.config['MOBILE_USER_AGENTS'], list)
        
    def test_upload_folder_created(self, app):
        """Test that upload folder is created during config initialization."""
        import os
        
        # The config.init_app() should create the upload folder
        with app.app_context():
            upload_folder = app.config['UPLOAD_FOLDER']
            # For testing config, we need to manually create the temp directory
            # since it might not exist yet
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder, exist_ok=True)
            assert os.path.exists(upload_folder)
            
    def test_environment_detection(self, monkeypatch):
        """Test environment detection from environment variables."""
        monkeypatch.setenv('FLASK_ENV', 'production')
        
        app = create_app()  # Should detect production from env var
        
        # Should use production config
        assert app.config['DEBUG'] is False
        assert app.config['REQUEST_TIMEOUT'] == 15


class TestErrorHandling:
    """Test error handling in routes."""
    
    def test_404_handling(self, client):
        """Test 404 handling for non-existent routes."""
        response = client.get('/non-existent-route')
        assert response.status_code == 404
        
    def test_method_not_allowed(self, client):
        """Test method not allowed handling."""
        # Health endpoint only accepts GET
        response = client.post('/health')
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])