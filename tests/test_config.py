"""
Tests for configuration system.

These tests ensure our config classes work correctly across different environments.
"""
import pytest
import os
from app.config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, get_config


class TestConfigSystem:
    """Test the configuration system."""
    
    def test_base_config_values(self):
        """Test base configuration has expected defaults."""
        config = Config()
        
        assert config.DEBUG is False
        assert config.TESTING is False
        assert config.UPLOAD_FOLDER.endswith("battlescribe")
        assert config.WAHAPEDIA_BASE_URL == "https://wahapedia.ru/wh40k10ed/"
        assert len(config.WAHAPEDIA_CSV_FILES) == 6
        assert ".ros" in config.SUPPORTED_EXTENSIONS
        assert ".rosz" in config.SUPPORTED_EXTENSIONS
        assert config.REQUEST_TIMEOUT == 30
        assert config.MAX_RETRIES == 5
        
    def test_development_config(self):
        """Test development configuration overrides."""
        config = DevelopmentConfig()
        
        assert config.DEBUG is True
        assert config.REQUEST_TIMEOUT == 60  # Longer timeout for debugging
        
    def test_production_config(self):
        """Test production configuration optimizations.""" 
        config = ProductionConfig()
        
        assert config.DEBUG is False
        assert config.REQUEST_TIMEOUT == 15  # Faster timeout
        assert config.MAX_RETRIES == 3  # Fewer retries
        
    def test_testing_config(self):
        """Test testing configuration."""
        config = TestingConfig()
        
        assert config.DEBUG is True
        assert config.TESTING is True
        assert config.UPLOAD_FOLDER.startswith("/tmp/")
        assert config.REQUEST_TIMEOUT == 5  # Fast timeouts for tests
        assert config.MAX_RETRIES == 1
        assert config.FILE_RETENTION_HOURS == 1


class TestConfigGetter:
    """Test the get_config() function."""
    
    def test_get_config_development(self):
        """Test getting development config."""
        config = get_config('development')
        assert isinstance(config, type(DevelopmentConfig))
        assert config.DEBUG is True
        
    def test_get_config_production(self):
        """Test getting production config."""
        config = get_config('production')
        assert isinstance(config, type(ProductionConfig))
        assert config.DEBUG is False
        
    def test_get_config_testing(self):
        """Test getting testing config."""
        config = get_config('testing')
        assert isinstance(config, type(TestingConfig))
        assert config.TESTING is True
        
    def test_get_config_default(self):
        """Test getting default config."""
        config = get_config('invalid_name')
        assert isinstance(config, type(DevelopmentConfig))
        
    def test_get_config_from_environment(self, monkeypatch):
        """Test getting config from FLASK_ENV environment variable."""
        # Mock environment variable
        monkeypatch.setenv("FLASK_ENV", "production")
        config = get_config()
        assert isinstance(config, type(ProductionConfig))


class TestGameConstants:
    """Test game constants are properly imported."""
    
    def test_game_constants_imported(self):
        """Test that game constants are available."""
        from app.config import (
            SUBFACTION_TYPES, GAME_PHASES, UNIT_RENAME_MAPPINGS, 
            VALID_STRATAGEM_TYPES, ARMY_OF_RENOWN_LIST
        )
        
        # Test basic structure
        assert isinstance(SUBFACTION_TYPES, list)
        assert len(SUBFACTION_TYPES) > 0
        assert "Chapter" in SUBFACTION_TYPES
        
        assert isinstance(GAME_PHASES, list)
        assert len(GAME_PHASES) > 0
        assert "Command phase" in GAME_PHASES
        
        assert isinstance(UNIT_RENAME_MAPPINGS, dict)
        assert len(UNIT_RENAME_MAPPINGS) > 0
        
        assert isinstance(VALID_STRATAGEM_TYPES, list)
        assert "Battle Tactic Stratagem" in VALID_STRATAGEM_TYPES
        
        assert isinstance(ARMY_OF_RENOWN_LIST, list)
        assert "Vanguard Spearhead" in ARMY_OF_RENOWN_LIST


if __name__ == "__main__":
    pytest.main([__file__, "-v"])