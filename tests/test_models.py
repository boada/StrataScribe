"""
Tests for domain models.

These tests ensure our core data models work correctly and validate properly.
"""
import pytest
from dataclasses import FrozenInstanceError

from app.models.domain import (
    Faction, Unit, Stratagem, RosterData, RosterForce,
    ProcessingOptions, StratagemType, StratagemReference
)


class TestFaction:
    """Test the Faction domain model."""
    
    def test_valid_faction_creation(self):
        """Test creating a valid faction."""
        faction = Faction(id="SM", name="Space Marines")
        assert faction.id == "SM"
        assert faction.name == "Space Marines"
        assert faction.parent_id is None
        
    def test_faction_with_parent(self):
        """Test faction with parent relationship."""
        faction = Faction(id="CHUL", name="Ultramarines", parent_id="SM")
        assert faction.parent_id == "SM"
    
    def test_faction_validation_empty_id(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Faction must have both id and name"):
            Faction(id="", name="Space Marines")
    
    def test_faction_validation_empty_name(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Faction must have both id and name"):
            Faction(id="SM", name="")
    
    def test_faction_immutable(self):
        """Test that factions are immutable (frozen)."""
        faction = Faction(id="SM", name="Space Marines")
        # Test that we can't modify the frozen dataclass
        with pytest.raises(FrozenInstanceError):
            faction.id = 'NEW_ID'


class TestUnit:
    """Test the Unit domain model."""
    
    def test_valid_unit_creation(self):
        """Test creating a valid unit."""
        unit = Unit(id="sm_captain", name="Captain", faction_id="SM")
        assert unit.id == "sm_captain"
        assert unit.name == "Captain"
        assert unit.faction_id == "SM"
        assert unit.keywords == []
        
    def test_unit_with_keywords(self):
        """Test unit with keywords."""
        keywords = ["INFANTRY", "CHARACTER", "CAPTAIN"]
        unit = Unit(id="sm_captain", name="Captain", faction_id="SM", keywords=keywords)
        assert unit.keywords == keywords
    
    def test_unit_clean_name(self):
        """Test clean_name property removes apostrophes."""
        unit = Unit(id="test", name="Kâhl's Guard", faction_id="LOV")
        assert unit.clean_name == "Kâhls Guard"
        
    def test_unit_validation(self):
        """Test unit validation."""
        with pytest.raises(ValueError, match="Unit must have both id and name"):
            Unit(id="", name="Captain", faction_id="SM")


class TestStratagem:
    """Test the Stratagem domain model."""
    
    def test_valid_stratagem_creation(self):
        """Test creating a valid stratagem."""
        stratagem = Stratagem(
            id="strat_1",
            name="Honour the Chapter",
            type="Battle Tactic Stratagem",
            cp_cost=1,
            description="A test stratagem",
            legend="Test legend",
            phase="Fight phase",
            faction_id="SM"
        )
        assert stratagem.name == "Honour the Chapter"
        assert stratagem.cp_cost == 1
        assert not stratagem.is_core
        assert stratagem.stratagem_type == StratagemType.BATTLE_TACTIC
    
    def test_core_stratagem(self):
        """Test core stratagem detection."""
        stratagem = Stratagem(
            id="core_1", name="Test Core", type="Core Stratagem",
            cp_cost=0, description="", legend="", phase="", faction_id="SM"
        )
        assert stratagem.is_core
    
    def test_negative_cp_cost_validation(self):
        """Test that negative CP cost raises ValueError."""
        with pytest.raises(ValueError, match="CP cost cannot be negative"):
            Stratagem(
                id="test", name="Test", type="Battle Tactic", cp_cost=-1,
                description="", legend="", phase="", faction_id="SM"
            )
    
    def test_stratagem_type_enum(self):
        """Test stratagem type enum matching."""
        test_cases = [
            ("Battle Tactic Stratagem", StratagemType.BATTLE_TACTIC),
            ("Strategic Ploy Stratagem", StratagemType.STRATEGIC_PLOY),
            ("Epic Deed Stratagem", StratagemType.EPIC_DEED),
            ("Requisition Stratagem", StratagemType.REQUISITION),
            ("Wargear Stratagem", StratagemType.WARGEAR),
            ("Core Stratagem", StratagemType.CORE),
            ("Unknown Type", None)
        ]
        
        for type_str, expected_enum in test_cases:
            stratagem = Stratagem(
                id="test", name="Test", type=type_str, cp_cost=1,
                description="", legend="", phase="", faction_id="SM"
            )
            assert stratagem.stratagem_type == expected_enum


class TestProcessingOptions:
    """Test the ProcessingOptions model."""
    
    def test_default_options(self):
        """Test default processing options."""
        options = ProcessingOptions()
        assert not options.show_units
        assert not options.show_phases
        assert not options.show_empty
        assert not options.show_core
        assert not options.dont_show_renown
        assert not options.dont_show_before
    
    def test_from_form_data(self):
        """Test creating options from form data."""
        form_data = {
            'show_units': 'on',
            'show_core': 'on',
            'dont_show_renown': 'on'
        }
        
        options = ProcessingOptions.from_form_data(form_data)
        assert options.show_units
        assert options.show_core
        assert options.dont_show_renown
        assert not options.show_phases  # Not in form data


class TestRosterData:
    """Test roster data structures."""
    
    def test_empty_roster(self):
        """Test empty roster creation."""
        roster = RosterData()
        assert roster.name is None
        assert roster.forces == []
        assert not roster.is_multi_detachment
        assert roster.all_units == []
    
    def test_multi_detachment_detection(self):
        """Test multi-detachment detection."""
        force1 = RosterForce(catalogue_name="Space Marines")
        force2 = RosterForce(catalogue_name="Imperial Guard")
        
        roster = RosterData(forces=[force1, force2])
        assert roster.is_multi_detachment
    
    def test_all_units_aggregation(self):
        """Test aggregating units from all forces."""
        unit1 = Unit(id="1", name="Captain", faction_id="SM")
        unit2 = Unit(id="2", name="Lieutenant", faction_id="SM") 
        
        force = RosterForce(catalogue_name="Space Marines", units=[unit1, unit2])
        roster = RosterData(forces=[force])
        
        assert len(roster.all_units) == 2
        assert unit1 in roster.all_units
        assert unit2 in roster.all_units


if __name__ == "__main__":
    pytest.main([__file__, "-v"])