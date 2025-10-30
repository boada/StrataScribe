"""
Tests for the RosterProcessingService.

Focuses on testing the public interface and integration points of the 
reconstructed roster processing service.
"""

import pytest
from unittest.mock import Mock

from app.services.roster_service import RosterProcessingService, StratagemCollection, RosterProcessingError
from app.services.file_service import FileService
from app.repositories.stratagem_repository import StratagemRepository
from app.models.domain import RosterData, ProcessingOptions, ProcessingResult, Stratagem
from app.config import get_config


class TestStratagemCollection:
    """Test the StratagemCollection utility class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.collection = StratagemCollection()
    
    def test_empty_collection(self):
        """Test empty collection initialization."""
        assert len(self.collection.faction_stratagems) == 0
        assert len(self.collection.unit_stratagems) == 0
        assert len(self.collection.core_stratagems) == 0
        assert len(self.collection.empty_stratagems) == 0
        assert len(self.collection.detachment_stratagems) == 0
        assert len(self.collection.all_stratagems) == 0
    
    def test_add_stratagem_to_collection(self):
        """Test adding stratagems to different categories."""
        faction_strat = Mock(spec=Stratagem)
        faction_strat.id = "faction_1"
        
        unit_strat = Mock(spec=Stratagem)
        unit_strat.id = "unit_1"
        
        self.collection.add_stratagem(faction_strat, 'faction')
        self.collection.add_stratagem(unit_strat, 'unit')
        
        assert len(self.collection.faction_stratagems) == 1
        assert len(self.collection.unit_stratagems) == 1
        assert len(self.collection.all_stratagems) == 2


class TestRosterProcessingService:
    """Test the main roster processing service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_service = Mock(spec=FileService)
        self.mock_repository = Mock(spec=StratagemRepository)
        self.config = get_config('testing')
        
        self.service = RosterProcessingService(
            self.mock_file_service, 
            self.mock_repository, 
            self.config
        )
    
    def test_initialization(self):
        """Test service initialization."""
        assert self.service.file_service == self.mock_file_service
        assert self.service.repository == self.mock_repository
        assert self.service.config == self.config
    
    def test_process_roster_file_success(self):
        """Test successful roster processing end-to-end."""
        # Mock successful file reading
        mock_roster = Mock(spec=RosterData)
        mock_roster.forces = []
        self.mock_file_service.read_roster_file.return_value = mock_roster
        
        # Mock repository responses
        self.mock_repository.get_all_factions.return_value = []
        self.mock_repository.get_all_stratagems.return_value = []
        
        # Mock wahapedia service through repository
        mock_wahapedia = Mock()
        mock_wahapedia.get_detachment_abilities.return_value = []
        mock_wahapedia.get_datasheets.return_value = []
        mock_wahapedia.get_datasheet_stratagems.return_value = []
        self.mock_repository.wahapedia_service = mock_wahapedia
        
        options = ProcessingOptions()
        result = self.service.process_roster_file("test.ros", options)
        
        # Should return ProcessingResult
        assert isinstance(result, ProcessingResult)
        assert hasattr(result, 'phases')
        assert hasattr(result, 'units')
        assert hasattr(result, 'all_stratagems')
        
        # Should have called file service
        self.mock_file_service.read_roster_file.assert_called_once_with("test.ros")
    
    def test_process_roster_file_error_handling(self):
        """Test error handling in roster processing."""
        # Mock file service error
        self.mock_file_service.read_roster_file.side_effect = Exception("File not found")
        
        options = ProcessingOptions()
        
        with pytest.raises(RosterProcessingError):
            self.service.process_roster_file("bad.ros", options)


class TestRosterServiceFactory:
    """Test the factory pattern for creating roster services."""
    
    def test_create_service(self):
        """Test service factory creates valid service."""
        from app.services import RosterServiceFactory
        
        config = get_config('testing')
        service = RosterServiceFactory.create_service(config)
        
        assert isinstance(service, RosterProcessingService)
        assert service.file_service is not None
        assert service.repository is not None
        assert service.config == config


class TestRosterServiceErrors:
    """Test custom error classes."""
    
    def test_error_inheritance(self):
        """Test that our custom errors inherit from Exception."""
        error = RosterProcessingError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_error_messages(self):
        """Test error message handling."""
        message = "Custom error message"
        error = RosterProcessingError(message)
        assert str(error) == message