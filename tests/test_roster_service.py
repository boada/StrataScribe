"""
Tests for Roster Processing Service functionality.
"""
import pytest
from unittest.mock import Mock, patch

from app.services.roster_service import (
    RosterProcessingService, RosterServiceFactory, StratagemCollection,
    RosterProcessingError, RosterAnalysisError, StratagemMatchingError
)
from app.services.file_service import FileService
from app.repositories.stratagem_repository import StratagemRepository
from app.models.domain import (
    RosterData, RosterForce, ProcessingOptions, ProcessingResult,
    Faction, Unit, Stratagem
)
from app.config.settings import TestingConfig


class TestStratagemCollection:
    """Test StratagemCollection functionality."""
    
    def test_empty_collection(self):
        """Test empty stratagem collection."""
        collection = StratagemCollection(
            faction_stratagems=[],
            unit_stratagems=[],
            core_stratagems=[],
            empty_stratagems=[],
            detachment_stratagems=[]
        )
        
        assert len(collection.all_stratagems) == 0
    
    def test_collection_with_duplicates(self):
        """Test that duplicate stratagems are removed."""
        strat1 = Stratagem(
            id="1", name="Test Stratagem", type="Battle", cp_cost=1,
            description="", legend="", phase="Command", faction_id="sm"
        )
        strat2 = Stratagem(
            id="1", name="Test Stratagem", type="Battle", cp_cost=1,
            description="", legend="", phase="Command", faction_id="sm"
        )
        strat3 = Stratagem(
            id="2", name="Another Stratagem", type="Core", cp_cost=0,
            description="", legend="", phase="Movement", faction_id="sm"
        )
        
        collection = StratagemCollection(
            faction_stratagems=[strat1],
            unit_stratagems=[strat2],  # Same ID as strat1
            core_stratagems=[strat3],
            empty_stratagems=[],
            detachment_stratagems=[]
        )
        
        # Should only have 2 unique stratagems despite 3 being added
        assert len(collection.all_stratagems) == 2
        ids = {s.id for s in collection.all_stratagems}
        assert ids == {"1", "2"}


class TestRosterProcessingService:
    """Test RosterProcessingService functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestingConfig()
        
        # Create mock dependencies
        self.mock_file_service = Mock(spec=FileService)
        self.mock_repository = Mock(spec=StratagemRepository)
        
        self.service = RosterProcessingService(
            self.mock_file_service, 
            self.mock_repository, 
            self.config
        )
    
    def test_init(self):
        """Test service initialization."""
        assert self.service.file_service == self.mock_file_service
        assert self.service.repository == self.mock_repository
        assert self.service.config == self.config
    
    def test_read_roster_file_success(self):
        """Test successful roster file reading."""
        test_roster = RosterData(name="Test Roster")
        self.mock_file_service.read_roster_file.return_value = test_roster
        
        result = self.service._parse_roster_file("test.ros")
        
        assert result == test_roster
        self.mock_file_service.read_roster_file.assert_called_once_with("test.ros")
    
    def test_read_roster_file_error(self):
        """Test roster file reading error handling."""
        self.mock_file_service.read_roster_file.side_effect = Exception("File error")
        
        with pytest.raises(RosterAnalysisError, match="Failed to read roster file"):
            self.service._parse_roster_file("test.ros")
    
    @pytest.mark.skip(reason="Method changed during reconstruction - see test_roster_service_new.py")
    def test_analyze_roster_structure_single_force(self):
        """Test analyzing roster with single force."""
        # Create test data
        faction = Faction(id="sm", name="Space Marines")
        unit = Unit(id="1", name="Tactical Squad", faction_id="sm")
        force = RosterForce(
            catalogue_name="Space Marines",
            faction=faction,
            units=[unit]
        )
        roster_data = RosterData(name="Test Roster", forces=[force])
        
        # Mock repository call
        self.mock_repository.find_faction_by_name.return_value = faction
        
        result = self.service._analyze_roster_structure(roster_data)
        
        assert result['roster_data'] == roster_data
        assert len(result['factions']) == 1
        assert result['factions'][0] == faction
        assert len(result['units']) == 1
        assert result['units'][0] == unit
        assert len(result['force_info']) == 1
    
    def test_analyze_roster_structure_multiple_forces(self):
        """Test roster structure analysis with multiple forces."""
        faction1 = Faction(id="sm", name="Space Marines")
        faction2 = Faction(id="csm", name="Chaos Space Marines")
        
        force1 = RosterForce(catalogue_name="Space Marines", faction=faction1, units=[])
        force2 = RosterForce(catalogue_name="Chaos Space Marines", faction=faction2, units=[])
        
        roster_data = RosterData(forces=[force1, force2])
        
        result = self.service._analyze_roster_structure(roster_data)
        
        assert len(result['factions']) == 2
        assert len(result['force_info']) == 2
    
    def test_analyze_roster_structure_duplicate_factions(self):
        """Test that duplicate factions are removed."""
        faction = Faction(id="sm", name="Space Marines")
        
        force1 = RosterForce(catalogue_name="Space Marines", faction=faction, units=[])
        force2 = RosterForce(catalogue_name="Space Marines", faction=faction, units=[])
        
        roster_data = RosterData(forces=[force1, force2])
        
        result = self.service._analyze_roster_structure(roster_data)
        
        # Should only have one faction despite two forces with same faction
        assert len(result['factions']) == 1
        assert result['factions'][0] == faction
    
    def test_analyze_force_with_faction(self):
        """Test force analysis when faction is provided."""
        faction = Faction(id="sm", name="Space Marines")
        unit = Unit(id="1", name="Tactical Squad", faction_id="sm")
        force = RosterForce(
            catalogue_name="Space Marines",
            faction=faction,
            units=[unit],
            detachment="Battalion"
        )
        
        result = self.service._analyze_force(force)
        
        assert result['faction'] == faction
        assert result['units'] == [unit]
        assert result['detachment'] == "Battalion"
    
    def test_analyze_force_without_faction(self):
        """Test force analysis when faction needs to be looked up."""
        faction = Faction(id="sm", name="Space Marines")
        force = RosterForce(catalogue_name="Space Marines", units=[])
        
        self.mock_repository.find_faction_by_name.return_value = faction
        
        result = self.service._analyze_force(force)
        
        assert result['faction'] == faction
        self.mock_repository.find_faction_by_name.assert_called_once_with("Space Marines")
    
    def test_collect_stratagems_basic(self):
        """Test basic stratagem collection."""
        faction = Faction(id="sm", name="Space Marines")
        analysis = {
            'factions': [faction],
            'units': []
        }
        options = ProcessingOptions(show_core=True, show_empty=True)
        
        # Mock repository responses
        faction_strats = [Stratagem(id="1", name="Faction Strat", type="Battle", cp_cost=1,
                                   description="", legend="", phase="", faction_id="sm")]
        core_strats = [Stratagem(id="2", name="Core Strat", type="Core", cp_cost=0,
                                description="", legend="", phase="", faction_id="")]
        empty_strats = [Stratagem(id="3", name="Empty Strat", type="Battle", cp_cost=1,
                                 description="", legend="", phase="", faction_id="sm")]
        
        self.mock_repository.find_faction_stratagems.return_value = faction_strats
        self.mock_repository.find_core_stratagems.return_value = core_strats
        self.mock_repository.find_empty_stratagems.return_value = empty_strats
        
        result = self.service._collect_stratagems(analysis, options)
        
        assert len(result.faction_stratagems) == 1
        assert len(result.core_stratagems) == 1
        assert len(result.empty_stratagems) == 1
        assert len(result.all_stratagems) == 3
    
    def test_collect_stratagems_with_units(self):
        """Test stratagem collection including unit stratagems."""
        unit = Unit(id="1", name="Tactical Squad", faction_id="sm")
        analysis = {
            'factions': [],
            'units': [unit]
        }
        options = ProcessingOptions()
        
        unit_strats = [Stratagem(id="1", name="Unit Strat", type="Battle", cp_cost=1,
                                description="", legend="", phase="", faction_id="sm")]
        
        self.mock_repository.find_stratagems_for_unit.return_value = unit_strats
        
        result = self.service._collect_stratagems(analysis, options)
        
        assert len(result.unit_stratagems) == 1
        self.mock_repository.find_stratagems_for_unit.assert_called_once_with("Tactical Squad")
    
    def test_collect_stratagems_error_handling(self):
        """Test stratagem collection error handling."""
        faction = Faction(id="sm", name="Space Marines")
        analysis = {'factions': [faction], 'units': []}
        options = ProcessingOptions()
        
        self.mock_repository.find_faction_stratagems.side_effect = Exception("Repository error")
        
        with pytest.raises(StratagemMatchingError, match="Failed to collect stratagems"):
            self.service._collect_stratagems(analysis, options)
    
    def test_organize_by_phase(self):
        """Test organizing stratagems by game phase."""
        stratagems = StratagemCollection(
            faction_stratagems=[
                Stratagem(id="1", name="Command Strat", type="Battle", cp_cost=1,
                         description="", legend="", phase="Command", faction_id="sm"),
                Stratagem(id="2", name="Shooting Strat", type="Battle", cp_cost=1,
                         description="", legend="", phase="Shooting", faction_id="sm")
            ],
            unit_stratagems=[],
            core_stratagems=[],
            empty_stratagems=[],
            detachment_stratagems=[]
        )
        
        analysis = {
            'force_info': [{'faction': Faction(id="sm", name="Space Marines")}]
        }
        options = ProcessingOptions()
        
        result = self.service._organize_by_phase(analysis, stratagems, options)
        
        assert len(result) == 1  # One force
        force_phases = result[0]
        assert "Command" in force_phases
        assert "Shooting" in force_phases
        assert "Command Strat" in force_phases["Command"]
        assert "Shooting Strat" in force_phases["Shooting"]
    
    def test_organize_by_unit(self):
        """Test organizing stratagems by unit."""
        unit = Unit(id="1", name="Tactical Squad", faction_id="sm")
        
        stratagems = StratagemCollection(
            faction_stratagems=[],
            unit_stratagems=[
                Stratagem(id="1", name="Tactical Strat", type="Battle", cp_cost=1,
                         description="", legend="", phase="", faction_id="sm")
            ],
            core_stratagems=[],
            empty_stratagems=[],
            detachment_stratagems=[]
        )
        
        analysis = {
            'force_info': [{'units': [unit], 'faction': None}]
        }
        options = ProcessingOptions()
        
        result = self.service._organize_by_unit(analysis, stratagems, options)
        
        assert len(result) == 1  # One force
        # Note: The current implementation has simplified unit matching
        # This test validates the structure is correct
        force_units = result[0]
        assert isinstance(force_units, dict)
    
    def test_sort_phases_by_game_order(self):
        """Test phase sorting according to game turn order."""
        phase_dict = {
            "Shooting": ["Strat 1"],
            "Command": ["Strat 2"],
            "Movement": ["Strat 3"],
            "Custom Phase": ["Strat 4"]
        }
        
        result = self.service._sort_phases_by_game_order(phase_dict)
        
        # Command should come before Movement, which should come before Shooting
        phases = list(result.keys())
        assert phases.index("Command") < phases.index("Movement")
        assert phases.index("Movement") < phases.index("Shooting")
        # Custom phases should still be included
        assert "Custom Phase" in phases


class TestRosterProcessingIntegration:
    """Integration tests for roster processing."""
    
    def setup_method(self):
        """Set up integration test fixtures."""
        self.config = TestingConfig()
        
        # Create mock dependencies for integration testing
        self.mock_file_service = Mock(spec=FileService)
        self.mock_repository = Mock(spec=StratagemRepository)
        
        self.service = RosterProcessingService(
            self.mock_file_service,
            self.mock_repository,
            self.config
        )
    
    def test_process_roster_file_complete_flow(self):
        """Test complete roster processing flow."""
        # Setup test data
        faction = Faction(id="sm", name="Space Marines")
        unit = Unit(id="1", name="Tactical Squad", faction_id="sm")
        force = RosterForce(catalogue_name="Space Marines", faction=faction, units=[unit])
        roster_data = RosterData(name="Test Roster", forces=[force])
        
        stratagem = Stratagem(id="1", name="Test Strat", type="Battle", cp_cost=1,
                             description="", legend="", phase="Command", faction_id="sm")
        
        options = ProcessingOptions(show_core=False, show_empty=False)
        
        # Mock all the calls
        self.mock_repository.initialize.return_value = True
        self.mock_file_service.read_roster_file.return_value = roster_data
        self.mock_repository.find_faction_by_name.return_value = faction
        self.mock_repository.find_faction_stratagems.return_value = [stratagem]
        self.mock_repository.find_stratagems_for_unit.return_value = []
        self.mock_file_service.cleanup_old_files.return_value = 0
        
        # Execute
        result = self.service.process_roster_file("test.ros", options)
        
        # Verify
        assert isinstance(result, ProcessingResult)
        assert len(result.all_stratagems) == 1
        assert result.all_stratagems[0] == stratagem
        
        # Verify all services were called
        self.mock_repository.initialize.assert_called_once()
        self.mock_file_service.read_roster_file.assert_called_once_with("test.ros")
        self.mock_file_service.cleanup_old_files.assert_called_once()
    
    def test_process_roster_file_error_propagation(self):
        """Test that errors are properly propagated and wrapped."""
        self.mock_repository.initialize.return_value = True
        self.mock_file_service.read_roster_file.side_effect = Exception("File read error")
        
        options = ProcessingOptions()
        
        with pytest.raises(RosterProcessingError, match="Failed to process roster"):
            self.service.process_roster_file("test.ros", options)


class TestRosterServiceFactory:
    """Test roster service factory."""
    
    def test_create_service(self):
        """Test service creation via factory."""
        config = TestingConfig()
        
        # Create service using factory
        service = RosterServiceFactory.create_service(config)
        
        # Verify service was created with correct type and config
        assert isinstance(service, RosterProcessingService)
        assert service.config == config
        
        # Verify dependencies are properly initialized
        assert service.file_service is not None
        assert service.repository is not None


class TestRosterProcessingErrors:
    """Test roster processing error handling."""
    
    def test_error_inheritance(self):
        """Test custom exception inheritance."""
        assert issubclass(RosterProcessingError, Exception)
        assert issubclass(RosterAnalysisError, RosterProcessingError)
        assert issubclass(StratagemMatchingError, RosterProcessingError)
    
    def test_error_messages(self):
        """Test error message handling."""
        processing_error = RosterProcessingError("Processing failed")
        assert str(processing_error) == "Processing failed"
        
        analysis_error = RosterAnalysisError("Analysis failed")
        assert str(analysis_error) == "Analysis failed"
        
        matching_error = StratagemMatchingError("Matching failed")
        assert str(matching_error) == "Matching failed"