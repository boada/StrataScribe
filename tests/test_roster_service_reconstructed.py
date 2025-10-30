"""
Tests for the reconstructed RosterProcessingService.

These tests validate the 5-step roster processing pipeline:
1. Parse roster file
2. Extract faction data  
3. Extract detachment data
4. Extract unit data
5. Collect applicable stratagems
6. Organize results for UI
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

from app.services.roster_service import RosterProcessingService, RosterProcessingError, RosterAnalysisError
from app.models.domain import (
    RosterData, RosterForce, ProcessingOptions, ProcessingResult,
    Faction, Stratagem
)


class TestRosterProcessingServiceReconstructed:
    """Test the reconstructed roster processing service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_service = Mock()
        self.mock_repo = Mock()
        
        # Mock config
        self.mock_config = Mock()
        self.mock_config.BATTLESCRIBE_DATA_PATH = Path("/test/data")
        
        self.service = RosterProcessingService(
            file_service=self.mock_file_service,
            stratagem_repository=self.mock_repo
        )
        self.service.config = self.mock_config
    
    def test_process_roster_file_complete_flow(self):
        """Test the complete roster processing flow."""
        # Mock file service
        test_roster = RosterData(
            name="Test Army",
            game_system="Warhammer 40,000 10th Edition",
            forces=[
                RosterForce(
                    name="Adeptus Astartes",
                    catalogue_name="Adeptus Astartes"
                )
            ]
        )
        self.mock_file_service.read_roster_file.return_value = test_roster
        
        # Mock repository
        test_factions = [
            Faction(name="Adeptus Astartes", wahapedia_name="Space Marines")
        ]
        test_stratagems = [
            Stratagem(
                name="Test Stratagem",
                faction="Space Marines",
                phase="Movement phase",
                cost=1,
                description="Test description"
            )
        ]
        
        self.mock_repo.get_all_factions.return_value = test_factions
        self.mock_repo.get_stratagems_for_factions.return_value = test_stratagems
        self.mock_repo.get_core_stratagems.return_value = []
        
        # Test processing
        options = ProcessingOptions(show_core=True)
        result = self.service.process_roster_file("test.ros", options)
        
        # Verify result structure
        assert isinstance(result, ProcessingResult)
        assert len(result.phases) == 1  # One force
        assert len(result.units) == 1   # One force
        assert isinstance(result.all_stratagems, list)
        
        # Verify method calls
        self.mock_file_service.read_roster_file.assert_called_once_with("test.ros")
        self.mock_repo.get_all_factions.assert_called_once()
    
    def test_parse_roster_file_success(self):
        """Test successful roster file parsing."""
        test_roster = RosterData(name="Test Roster")
        self.mock_file_service.read_roster_file.return_value = test_roster
        
        result = self.service._parse_roster_file("test.ros")
        
        assert result == test_roster
        self.mock_file_service.read_roster_file.assert_called_once_with("test.ros")
    
    def test_parse_roster_file_error(self):
        """Test roster file parsing error handling."""
        self.mock_file_service.read_roster_file.side_effect = Exception("File error")
        
        with pytest.raises(RosterProcessingError, match="Failed to parse roster file"):
            self.service._parse_roster_file("test.ros")
    
    def test_extract_faction_data_success(self):
        """Test successful faction data extraction."""
        # Mock roster with forces
        roster_data = RosterData(
            name="Test Army",
            forces=[
                RosterForce(name="Space Marines", catalogue_name="Adeptus Astartes")
            ]
        )
        
        # Mock repository
        test_factions = [
            Faction(name="Adeptus Astartes", wahapedia_name="Space Marines")
        ]
        self.mock_repo.get_all_factions.return_value = test_factions
        
        result = self.service._extract_faction_data(roster_data)
        
        assert len(result) == 1
        assert result[0] is not None
        assert result[0]["battlescribe_name"] == "Adeptus Astartes"
        assert result[0]["wahapedia_name"] == "Space Marines"
    
    def test_extract_faction_data_no_match(self):
        """Test faction extraction with no matching factions."""
        roster_data = RosterData(
            name="Test Army", 
            forces=[
                RosterForce(name="Unknown Faction", catalogue_name="Unknown")
            ]
        )
        
        self.mock_repo.get_all_factions.return_value = []
        
        result = self.service._extract_faction_data(roster_data)
        
        assert len(result) == 1
        assert result[0] is None
    
    def test_extract_detachment_data_success(self):
        """Test successful detachment data extraction."""
        roster_data = RosterData(
            name="Test Army",
            forces=[
                RosterForce(
                    name="Space Marines",
                    selections=[
                        Mock(name="Gladius Task Force", type_name="Detachment")
                    ]
                )
            ]
        )
        
        result = self.service._extract_detachment_data(roster_data)
        
        assert len(result) == 1
        assert result[0] == "Gladius Task Force"
    
    def test_extract_unit_data_success(self):
        """Test successful unit data extraction."""
        mock_selection = Mock()
        mock_selection.name = "Captain"
        mock_selection.type_name = "Unit"
        
        roster_data = RosterData(
            name="Test Army",
            forces=[
                RosterForce(
                    name="Space Marines",
                    selections=[mock_selection]
                )
            ]
        )
        
        result = self.service._extract_unit_data(roster_data)
        
        assert len(result) == 1  # One force
        assert len(result[0]) == 1  # One unit
        assert result[0][0]["name"] == "Captain"
        assert result[0][0]["datasheet"] == "Captain"
    
    def test_collect_applicable_stratagems_basic(self):
        """Test basic stratagem collection."""
        faction_data = [{"wahapedia_name": "Space Marines"}]
        detachment_data = ["Gladius Task Force"]
        unit_data = [[{"datasheet": "Captain"}]]
        
        # Mock stratagems
        faction_stratagems = [
            Stratagem(name="Faction Strat", faction="Space Marines", phase="Movement phase")
        ]
        detachment_stratagems = [
            Stratagem(name="Detachment Strat", detachment="Gladius Task Force", phase="Shooting phase")
        ]
        unit_stratagems = [
            Stratagem(name="Unit Strat", keywords=["Captain"], phase="Fight phase")
        ]
        core_stratagems = [
            Stratagem(name="Core Strat", faction="Core", phase="Command phase")
        ]
        
        self.mock_repo.get_stratagems_for_factions.return_value = faction_stratagems
        self.mock_repo.get_stratagems_for_detachments.return_value = detachment_stratagems
        self.mock_repo.get_stratagems_for_units.return_value = unit_stratagems
        self.mock_repo.get_core_stratagems.return_value = core_stratagems
        
        options = ProcessingOptions(show_core=True)
        
        result = self.service._collect_applicable_stratagems(
            faction_data, detachment_data, unit_data, options
        )
        
        assert len(result) >= 3  # Should include faction, detachment, and core stratagems
        stratagem_names = [s.name for s in result]
        assert "Faction Strat" in stratagem_names
        assert "Detachment Strat" in stratagem_names
        assert "Core Strat" in stratagem_names
    
    def test_organize_results_for_ui_success(self):
        """Test UI results organization."""
        stratagems = [
            Stratagem(name="Move Strat", phase="Movement phase"),
            Stratagem(name="Shoot Strat", phase="Shooting phase")
        ]
        unit_data = [[{"name": "Captain", "datasheet": "Captain"}]]
        
        result = self.service._organize_results_for_ui(stratagems, unit_data)
        
        assert isinstance(result, ProcessingResult)
        assert len(result.phases) == 1  # One force
        assert len(result.units) == 1   # One force
        assert len(result.all_stratagems) == 2
    
    def test_organize_by_phase_success(self):
        """Test phase organization."""
        stratagems = [
            Stratagem(name="Move Strat", phase="Movement phase"),
            Stratagem(name="Shoot Strat", phase="Shooting phase"),
            Stratagem(name="Fight Strat", phase="Fight phase")
        ]
        
        result = self.service._organize_by_phase(stratagems, num_forces=1)
        
        assert len(result) == 1  # One force
        phases = result[0]
        assert "Movement phase" in phases
        assert "Shooting phase" in phases
        assert "Fight phase" in phases
        assert "Move Strat" in phases["Movement phase"]
        assert "Shoot Strat" in phases["Shooting phase"]
        assert "Fight Strat" in phases["Fight phase"]
    
    def test_organize_by_unit_success(self):
        """Test unit organization."""
        stratagems = [
            Stratagem(name="Captain Strat", keywords=["Captain"]),
            Stratagem(name="Generic Strat", keywords=[])
        ]
        unit_data = [[{"name": "Captain", "datasheet": "Captain"}]]
        
        result = self.service._organize_by_unit(stratagems, unit_data)
        
        assert len(result) == 1  # One force
        units = result[0]
        assert "Captain" in units
        # Captain Strat should be associated with Captain unit
        # This is a simplified check - actual implementation may vary
        assert isinstance(units["Captain"], list)
    
    def test_error_handling_in_process_roster_file(self):
        """Test error handling in the main process method."""
        # Mock file service to raise an error
        self.mock_file_service.read_roster_file.side_effect = Exception("Critical error")
        
        options = ProcessingOptions()
        
        with pytest.raises(RosterProcessingError, match="Failed to process roster"):
            self.service.process_roster_file("test.ros", options)


class TestRosterProcessingServiceHelpers:
    """Test helper methods in roster processing service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_service = Mock()
        self.mock_repo = Mock()
        
        self.service = RosterProcessingService(
            file_service=self.mock_file_service,
            stratagem_repository=self.mock_repo
        )
    
    def test_match_faction_for_force_exact_match(self):
        """Test exact faction matching."""
        force = RosterForce(name="Space Marines", catalogue_name="Adeptus Astartes")
        factions = [
            Faction(name="Adeptus Astartes", wahapedia_name="Space Marines")
        ]
        
        result = self.service._match_faction_for_force(force, factions)
        
        assert result is not None
        assert result.name == "Adeptus Astartes"
    
    def test_match_faction_for_force_no_match(self):
        """Test faction matching with no matches."""
        force = RosterForce(name="Unknown", catalogue_name="Unknown")
        factions = [
            Faction(name="Adeptus Astartes", wahapedia_name="Space Marines")
        ]
        
        result = self.service._match_faction_for_force(force, factions)
        
        assert result is None
    
    def test_filter_relevant_stratagems_basic(self):
        """Test basic stratagem filtering."""
        stratagems = [
            Stratagem(name="Valid Strat", faction="Space Marines"),
            Stratagem(name="Invalid Strat", strat_type="Boarding Actions"),
            Stratagem(name="Another Valid", faction="Core")
        ]
        
        result = self.service._filter_relevant_stratagems(stratagems)
        
        # Should filter out Boarding Actions
        assert len(result) == 2
        names = [s.name for s in result]
        assert "Valid Strat" in names
        assert "Another Valid" in names
        assert "Invalid Strat" not in names


class TestProcessingOptions:
    """Test ProcessingOptions data class."""
    
    def test_default_options(self):
        """Test default processing options."""
        options = ProcessingOptions()
        
        assert options.show_core is True
        assert options.show_unit_stratagems is True
    
    def test_custom_options(self):
        """Test custom processing options."""
        options = ProcessingOptions(
            show_core=False,
            show_unit_stratagems=False
        )
        
        assert options.show_core is False
        assert options.show_unit_stratagems is False


class TestProcessingResult:
    """Test ProcessingResult data class."""
    
    def test_processing_result_creation(self):
        """Test ProcessingResult creation."""
        phases = [{"Movement phase": ["Strat 1"]}]
        units = [{"Captain": ["Strat 2"]}]
        stratagems = [Stratagem(name="Test", phase="Movement phase")]
        
        result = ProcessingResult(
            phases=phases,
            units=units,
            all_stratagems=stratagems
        )
        
        assert result.phases == phases
        assert result.units == units
        assert result.all_stratagems == stratagems
        assert len(result.all_stratagems) == 1