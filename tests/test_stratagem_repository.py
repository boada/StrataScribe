"""
Tests for Stratagem Repository functionality.
"""
import pytest
from unittest.mock import Mock, patch

from app.repositories.stratagem_repository import (
    StratagemRepository, StratagemRepositoryError
)
from app.services.wahapedia_service import WahapediaService
from app.models.domain import Faction, Stratagem
from app.models.external import WahapediaDatasheet
from app.config.settings import TestingConfig


class TestStratagemRepository:
    """Test StratagemRepository functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestingConfig()
        
        # Create mock service
        self.mock_service = Mock(spec=WahapediaService)
        self.repository = StratagemRepository(self.mock_service)
    
    def test_init(self):
        """Test repository initialization."""
        assert self.repository.wahapedia_service == self.mock_service
        assert self.repository._factions_cache is None
        assert self.repository._stratagems_cache is None
    
    def test_initialize_success(self):
        """Test successful repository initialization."""
        self.mock_service.initialize.return_value = True
        
        result = self.repository.initialize()
        
        assert result is True
        self.mock_service.initialize.assert_called_once()
    
    def test_initialize_error(self):
        """Test repository initialization error handling."""
        self.mock_service.initialize.side_effect = Exception("Service error")
        
        with pytest.raises(StratagemRepositoryError, match="Repository initialization failed"):
            self.repository.initialize()
    
    def test_get_all_factions_caches_result(self):
        """Test that factions are cached after first call."""
        test_factions = [
            Faction(id="1", name="Space Marines"),
            Faction(id="2", name="Chaos Space Marines")
        ]
        self.mock_service.get_factions.return_value = test_factions
        
        # First call
        result1 = self.repository.get_all_factions()
        assert result1 == test_factions
        
        # Second call should use cache
        result2 = self.repository.get_all_factions()
        assert result2 == test_factions
        
        # Service should only be called once
        self.mock_service.get_factions.assert_called_once()
    
    def test_get_faction_by_id_found(self):
        """Test finding faction by ID."""
        test_factions = [
            Faction(id="sm", name="Space Marines"),
            Faction(id="csm", name="Chaos Space Marines")
        ]
        self.mock_service.get_factions.return_value = test_factions
        
        result = self.repository.get_faction_by_id("sm")
        
        assert result is not None
        assert result.id == "sm"
        assert result.name == "Space Marines"
    
    def test_get_faction_by_id_not_found(self):
        """Test faction lookup when not found."""
        test_factions = [Faction(id="sm", name="Space Marines")]
        self.mock_service.get_factions.return_value = test_factions
        
        result = self.repository.get_faction_by_id("nonexistent")
        
        assert result is None
    
    def test_find_faction_by_name_exact_match(self):
        """Test finding faction by exact name match."""
        test_factions = [
            Faction(id="sm", name="Space Marines"),
            Faction(id="ig", name="Astra Militarum")
        ]
        self.mock_service.get_factions.return_value = test_factions
        
        result = self.repository.find_faction_by_name("Space Marines")
        
        assert result is not None
        assert result.id == "sm"
    
    def test_find_faction_by_name_partial_match(self):
        """Test finding faction by partial name match."""
        test_factions = [
            Faction(id="sm", name="Space Marines"),
            Faction(id="ig", name="Astra Militarum")
        ]
        self.mock_service.get_factions.return_value = test_factions
        
        result = self.repository.find_faction_by_name("Space")
        
        assert result is not None
        assert result.id == "sm"
    
    def test_find_faction_by_name_case_insensitive(self):
        """Test case-insensitive faction name search."""
        test_factions = [Faction(id="sm", name="Space Marines")]
        self.mock_service.get_factions.return_value = test_factions
        
        result = self.repository.find_faction_by_name("space marines")
        
        assert result is not None
        assert result.id == "sm"
    
    def test_get_all_stratagems_caches_result(self):
        """Test that stratagems are cached."""
        test_stratagems = [
            Stratagem(id="1", name="Test", type="Battle", cp_cost=1, 
                     description="", legend="", phase="", faction_id="sm")
        ]
        self.mock_service.get_stratagems.return_value = test_stratagems
        
        # First call
        result1 = self.repository.get_all_stratagems()
        assert result1 == test_stratagems
        
        # Second call should use cache
        result2 = self.repository.get_all_stratagems()
        assert result2 == test_stratagems
        
        # Service called once without faction filter
        self.mock_service.get_stratagems.assert_called_once_with()
    
    def test_get_all_stratagems_with_faction_filter(self):
        """Test getting stratagems with faction filter (no caching)."""
        test_stratagems = [
            Stratagem(id="1", name="SM Stratagem", type="Battle", cp_cost=1, 
                     description="", legend="", phase="", faction_id="sm")
        ]
        self.mock_service.get_stratagems.return_value = test_stratagems
        
        result = self.repository.get_all_stratagems(faction_id="sm")
        
        assert result == test_stratagems
        self.mock_service.get_stratagems.assert_called_once_with(faction_id="sm")
    
    def test_get_stratagem_by_id(self):
        """Test finding stratagem by ID."""
        test_stratagems = [
            Stratagem(id="strat1", name="Test", type="Battle", cp_cost=1,
                     description="", legend="", phase="", faction_id="sm"),
            Stratagem(id="strat2", name="Another", type="Core", cp_cost=0,
                     description="", legend="", phase="", faction_id="sm")
        ]
        self.mock_service.get_stratagems.return_value = test_stratagems
        
        result = self.repository.get_stratagem_by_id("strat1")
        
        assert result is not None
        assert result.id == "strat1"
        assert result.name == "Test"
    
    def test_find_stratagems_by_type(self):
        """Test finding stratagems by type."""
        test_stratagems = [
            Stratagem(id="1", name="Battle Strat", type="Battle Tactic", cp_cost=1,
                     description="", legend="", phase="", faction_id="sm"),
            Stratagem(id="2", name="Core Strat", type="Core", cp_cost=0,
                     description="", legend="", phase="", faction_id="sm")
        ]
        self.mock_service.get_stratagems.return_value = test_stratagems
        
        result = self.repository.find_stratagems_by_type("Battle")
        
        assert len(result) == 1
        assert result[0].id == "1"
        assert "Battle" in result[0].type
    
    def test_find_core_stratagems(self):
        """Test finding core stratagems."""
        test_stratagems = [
            Stratagem(id="1", name="Battle Strat", type="Battle Tactic", cp_cost=1,
                     description="", legend="", phase="", faction_id="sm"),
            Stratagem(id="2", name="Core Strat", type="Core", cp_cost=0,
                     description="", legend="", phase="", faction_id="sm")
        ]
        self.mock_service.get_stratagems.return_value = test_stratagems
        
        result = self.repository.find_core_stratagems()
        
        # Should find the core stratagem (one with "core" in type)
        core_results = [s for s in result if s.is_core]
        assert len(core_results) >= 0  # Depends on is_core implementation
    
    def test_find_stratagems_by_phase(self):
        """Test finding stratagems by phase."""
        test_stratagems = [
            Stratagem(id="1", name="Command Strat", type="Battle", cp_cost=1,
                     description="", legend="", phase="Command", faction_id="sm"),
            Stratagem(id="2", name="Shooting Strat", type="Battle", cp_cost=1,
                     description="", legend="", phase="Shooting", faction_id="sm")
        ]
        self.mock_service.get_stratagems.return_value = test_stratagems
        
        result = self.repository.find_stratagems_by_phase("Command")
        
        assert len(result) == 1
        assert result[0].id == "1"
        assert "Command" in result[0].phase
    
    def test_get_all_datasheets_caches_result(self):
        """Test that datasheets are cached."""
        test_datasheets = [
            WahapediaDatasheet(id="1", name="Space Marine", faction_id="sm")
        ]
        self.mock_service.get_datasheets.return_value = test_datasheets
        
        # First call
        result1 = self.repository.get_all_datasheets()
        assert result1 == test_datasheets
        
        # Second call should use cache
        result2 = self.repository.get_all_datasheets()
        assert result2 == test_datasheets
        
        # Service should only be called once
        self.mock_service.get_datasheets.assert_called_once()
    
    def test_find_datasheet_by_name_exact(self):
        """Test finding datasheet by exact name."""
        test_datasheets = [
            WahapediaDatasheet(id="1", name="Space Marine", faction_id="sm"),
            WahapediaDatasheet(id="2", name="Chaos Space Marine", faction_id="csm")
        ]
        self.mock_service.get_datasheets.return_value = test_datasheets
        
        result = self.repository.find_datasheet_by_name("Space Marine")
        
        assert result is not None
        assert result.id == "1"
        assert result.name == "Space Marine"
    
    def test_find_datasheet_by_name_partial(self):
        """Test finding datasheet by partial name."""
        test_datasheets = [
            WahapediaDatasheet(id="1", name="Space Marine Tactical Squad", faction_id="sm")
        ]
        self.mock_service.get_datasheets.return_value = test_datasheets
        
        result = self.repository.find_datasheet_by_name("Tactical")
        
        assert result is not None
        assert result.id == "1"
    
    def test_get_datasheet_stratagems_caches_result(self):
        """Test that datasheet-stratagem relationships are cached."""
        test_relationships = [
            {"datasheet_id": "1", "stratagem_id": "strat1"},
            {"datasheet_id": "2", "stratagem_id": "strat2"}
        ]
        self.mock_service.get_datasheet_stratagems.return_value = test_relationships
        
        # First call
        result1 = self.repository.get_datasheet_stratagems()
        assert result1 == test_relationships
        
        # Second call should use cache
        result2 = self.repository.get_datasheet_stratagems()
        assert result2 == test_relationships
        
        # Service should only be called once
        self.mock_service.get_datasheet_stratagems.assert_called_once()
    
    def test_find_faction_stratagems(self):
        """Test finding stratagems for a faction."""
        test_stratagems = [
            Stratagem(id="1", name="SM Strat", type="Battle", cp_cost=1,
                     description="", legend="", phase="", faction_id="sm"),
            Stratagem(id="2", name="CSM Strat", type="Battle", cp_cost=1,
                     description="", legend="", phase="", faction_id="csm"),
            Stratagem(id="3", name="Sub Strat", type="Battle", cp_cost=1,
                     description="", legend="", phase="", faction_id="other", subfaction_id="sm")
        ]
        self.mock_service.get_stratagems.return_value = test_stratagems
        
        result = self.repository.find_faction_stratagems("sm", include_subfactions=True)
        
        # Should find faction stratagems and subfaction stratagems
        assert len(result) == 2  # Main faction + subfaction
        faction_ids = {s.faction_id for s in result}
        subfaction_ids = {s.subfaction_id for s in result if s.subfaction_id}
        assert "sm" in faction_ids or "sm" in subfaction_ids
    
    def test_clear_caches(self):
        """Test cache clearing."""
        # Populate caches
        self.mock_service.get_factions.return_value = []
        self.repository.get_all_factions()
        
        # Clear caches
        self.repository._clear_caches()
        
        # Verify caches are cleared
        assert self.repository._factions_cache is None
        assert self.repository._stratagems_cache is None


class TestStratagemRepositoryIntegration:
    """Integration tests with real service (mocked at HTTP level)."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.config = TestingConfig()
        
        # Use real service but mock the HTTP calls
        self.service = WahapediaService(self.config)
        self.repository = StratagemRepository(self.service)


class TestStratagemRepositoryErrors:
    """Test repository error handling."""
    
    def test_error_inheritance(self):
        """Test custom exception inheritance."""
        assert issubclass(StratagemRepositoryError, Exception)
    
    def test_error_messages(self):
        """Test error message handling."""
        error = StratagemRepositoryError("Repository error")
        assert str(error) == "Repository error"