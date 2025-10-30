"""
Integration tests for the reconstructed RosterProcessingService.

These tests validate the 5-step reconstruction working with real data.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.roster_service import RosterProcessingService, RosterProcessingError
from app.models.domain import RosterData, RosterForce, ProcessingOptions, Faction, Stratagem


class TestRosterServiceReconstruction:
    """Test the reconstructed methods in isolation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_service = Mock()
        self.mock_repo = Mock()
        
        self.service = RosterProcessingService(
            file_service=self.mock_file_service,
            repository=self.mock_repo
        )
    
    def test_parse_roster_file_delegates_correctly(self):
        """Test that _parse_roster_file delegates to file service."""
        mock_roster = Mock(spec=RosterData)
        self.mock_file_service.read_roster_file.return_value = mock_roster
        
        result = self.service._parse_roster_file("test.ros")
        
        assert result == mock_roster
        self.mock_file_service.read_roster_file.assert_called_once_with("test.ros")
    
    def test_extract_faction_data_handles_forces(self):
        """Test that faction extraction processes all forces."""
        # Create a roster with one force
        force = Mock(spec=RosterForce)
        force.catalogue_name = "Space Marines"
        
        roster_data = Mock(spec=RosterData)
        roster_data.forces = [force]
        
        # Mock repository
        faction = Mock(spec=Faction)
        faction.name = "Space Marines"
        faction.id = "space-marines"
        self.mock_repo.get_all_factions.return_value = [faction]
        
        result = self.service._extract_faction_data(roster_data)
        
        # Should return one result per force
        assert len(result) == 1
        self.mock_repo.get_all_factions.assert_called_once()
    
    def test_extract_detachment_data_finds_detachments(self):
        """Test detachment extraction from selections."""
        # Mock selection with detachment
        selection = Mock()
        selection.name = "Gladius Task Force"
        selection.type_name = "Detachment"
        
        force = Mock(spec=RosterForce)
        force.selections = [selection]
        
        roster_data = Mock(spec=RosterData)
        roster_data.forces = [force]
        
        result = self.service._extract_detachment_data(roster_data)
        
        assert len(result) == 1
        assert result[0] == "Gladius Task Force"
    
    def test_extract_unit_data_processes_units(self):
        """Test unit extraction from selections."""
        # Mock unit selection
        unit_selection = Mock()
        unit_selection.name = "Captain"
        unit_selection.type_name = "Unit"
        
        force = Mock(spec=RosterForce)
        force.selections = [unit_selection]
        
        roster_data = Mock(spec=RosterData)
        roster_data.forces = [force]
        
        result = self.service._extract_unit_data(roster_data)
        
        # Should return nested structure: [force][units]
        assert len(result) == 1  # One force
        assert len(result[0]) == 1  # One unit
        assert result[0][0]["name"] == "Captain"
    
    def test_collect_applicable_stratagems_calls_repository(self):
        """Test that stratagem collection uses repository correctly."""
        faction_data = [{"wahapedia_name": "Space Marines"}]
        detachment_data = ["Gladius Task Force"]
        unit_data = [[]]
        options = ProcessingOptions()
        
        # Mock repository returns
        self.mock_repo.get_stratagems_for_factions.return_value = []
        self.mock_repo.get_stratagems_for_detachments.return_value = []
        self.mock_repo.get_stratagems_for_units.return_value = []
        self.mock_repo.get_core_stratagems.return_value = []
        
        result = self.service._collect_applicable_stratagems(
            faction_data, detachment_data, unit_data, options
        )
        
        # Should call all repository methods
        self.mock_repo.get_stratagems_for_factions.assert_called_once()
        self.mock_repo.get_stratagems_for_detachments.assert_called_once()
        self.mock_repo.get_stratagems_for_units.assert_called_once()
        assert isinstance(result, list)
    
    def test_organize_results_for_ui_creates_processing_result(self):
        """Test UI organization creates correct result structure."""
        stratagems = []
        unit_data = [[]]
        
        result = self.service._organize_results_for_ui(stratagems, unit_data)
        
        # Should return ProcessingResult with correct structure
        assert hasattr(result, 'phases')
        assert hasattr(result, 'units') 
        assert hasattr(result, 'all_stratagems')
        assert isinstance(result.phases, list)
        assert isinstance(result.units, list)
        assert isinstance(result.all_stratagems, list)
    
    def test_organize_by_phase_groups_by_phase(self):
        """Test phase organization groups stratagems correctly."""
        # Mock stratagems with different phases
        strat1 = Mock(spec=Stratagem)
        strat1.name = "Move Fast"
        strat1.phase = "Movement phase"
        
        strat2 = Mock(spec=Stratagem)
        strat2.name = "Shoot Good"
        strat2.phase = "Shooting phase"
        
        stratagems = [strat1, strat2]
        
        result = self.service._organize_by_phase(stratagems, num_forces=1)
        
        assert len(result) == 1  # One force
        phases = result[0]
        assert "Movement phase" in phases
        assert "Shooting phase" in phases
        assert "Move Fast" in phases["Movement phase"]
        assert "Shoot Good" in phases["Shooting phase"]
    
    def test_organize_by_unit_groups_by_unit(self):
        """Test unit organization groups stratagems correctly."""
        # Mock stratagem with keywords
        strat = Mock(spec=Stratagem)
        strat.name = "Captain Strat"
        strat.keywords = ["Captain"]
        
        stratagems = [strat]
        unit_data = [[{"name": "Captain", "datasheet": "Captain"}]]
        
        result = self.service._organize_by_unit(stratagems, unit_data)
        
        assert len(result) == 1  # One force
        units = result[0]
        assert isinstance(units, dict)
    
    def test_filter_relevant_stratagems_removes_invalid_types(self):
        """Test filtering removes stratagems with invalid types."""
        valid_strat = Mock(spec=Stratagem)
        valid_strat.name = "Valid"
        valid_strat.strat_type = "Battle Tactic Stratagem"
        
        invalid_strat = Mock(spec=Stratagem)
        invalid_strat.name = "Invalid"
        invalid_strat.strat_type = "Boarding Actions"
        
        stratagems = [valid_strat, invalid_strat]
        
        result = self.service._filter_relevant_stratagems(stratagems)
        
        # Should only return valid stratagem
        assert len(result) == 1
        assert result[0].name == "Valid"


class TestRosterServiceIntegration:
    """Integration test for the complete flow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_service = Mock()
        self.mock_repo = Mock()
        
        self.service = RosterProcessingService(
            file_service=self.mock_file_service,
            repository=self.mock_repo
        )
    
    def test_full_processing_pipeline(self):
        """Test the complete processing pipeline works."""
        # Mock file service
        roster_data = Mock(spec=RosterData)
        roster_data.forces = []
        self.mock_file_service.read_roster_file.return_value = roster_data
        
        # Mock repository
        self.mock_repo.get_all_factions.return_value = []
        self.mock_repo.get_stratagems_for_factions.return_value = []
        self.mock_repo.get_stratagems_for_detachments.return_value = []
        self.mock_repo.get_stratagems_for_units.return_value = []
        self.mock_repo.get_core_stratagems.return_value = []
        
        options = ProcessingOptions()
        
        result = self.service.process_roster_file("test.ros", options)
        
        # Should complete without errors and return ProcessingResult
        assert hasattr(result, 'phases')
        assert hasattr(result, 'units')
        assert hasattr(result, 'all_stratagems')
        
        # Should have called file service
        self.mock_file_service.read_roster_file.assert_called_once_with("test.ros")
    
    def test_error_handling_in_pipeline(self):
        """Test error handling throughout the pipeline."""
        # Mock file service to raise an error
        self.mock_file_service.read_roster_file.side_effect = Exception("File not found")
        
        options = ProcessingOptions()
        
        with pytest.raises(RosterProcessingError):
            self.service.process_roster_file("bad.ros", options)