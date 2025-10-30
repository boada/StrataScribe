"""
Simple tests for domain models without external dependencies.

Run with: python tests/simple_test_models.py
"""

from app.models.domain import (
    Faction, Unit, Stratagem, RosterData, RosterForce,
    ProcessingOptions, StratagemType, StratagemReference
)


def test_faction_creation():
    """Test basic faction creation and validation."""
    print("Testing Faction model...")
    
    # Valid faction
    faction = Faction(id="SM", name="Space Marines")
    assert faction.id == "SM"
    assert faction.name == "Space Marines"
    print("  ✅ Valid faction creation")
    
    # Faction with parent
    subfaction = Faction(id="CHUL", name="Ultramarines", parent_id="SM")
    assert subfaction.parent_id == "SM"
    print("  ✅ Faction with parent")
    
    # Test validation
    try:
        invalid_faction = Faction(id="", name="Space Marines")
        print("  ❌ Should have failed validation")
    except ValueError:
        print("  ✅ Validation works for empty ID")
    
    try:
        invalid_faction = Faction(id="SM", name="")
        print("  ❌ Should have failed validation")
    except ValueError:
        print("  ✅ Validation works for empty name")


def test_unit_creation():
    """Test unit model creation and properties."""
    print("\nTesting Unit model...")
    
    # Basic unit
    unit = Unit(id="sm_captain", name="Captain", faction_id="SM")
    assert unit.id == "sm_captain"
    assert unit.name == "Captain"
    assert unit.keywords == []
    print("  ✅ Basic unit creation")
    
    # Unit with keywords
    keywords = ["INFANTRY", "CHARACTER", "CAPTAIN"]
    unit_with_keywords = Unit(id="captain2", name="Captain", faction_id="SM", keywords=keywords)
    assert unit_with_keywords.keywords == keywords
    print("  ✅ Unit with keywords")
    
    # Test clean_name property
    unit_with_apostrophe = Unit(id="test", name="Kâhl's Guard", faction_id="LOV")
    assert unit_with_apostrophe.clean_name == "Kâhls Guard"
    print("  ✅ Clean name property")


def test_stratagem_creation():
    """Test stratagem model and its properties."""
    print("\nTesting Stratagem model...")
    
    # Basic stratagem
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
    print("  ✅ Basic stratagem creation")
    
    # Core stratagem
    core_stratagem = Stratagem(
        id="core_1", name="Test Core", type="Core Stratagem", cp_cost=0,
        description="", legend="", phase="", faction_id="SM"
    )
    assert core_stratagem.is_core
    print("  ✅ Core stratagem detection")
    
    # Test validation
    try:
        invalid_stratagem = Stratagem(
            id="test", name="Test", type="Battle Tactic", cp_cost=-1,
            description="", legend="", phase="", faction_id="SM"
        )
        print("  ❌ Should have failed CP validation")
    except ValueError:
        print("  ✅ CP cost validation works")


def test_processing_options():
    """Test processing options from form data."""
    print("\nTesting ProcessingOptions...")
    
    # Default options
    options = ProcessingOptions()
    assert not options.show_units
    assert not options.show_core
    print("  ✅ Default options")
    
    # From form data
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
    print("  ✅ From form data conversion")


def test_roster_data():
    """Test roster data structures."""
    print("\nTesting RosterData...")
    
    # Empty roster
    roster = RosterData()
    assert roster.forces == []
    assert not roster.is_multi_detachment
    assert roster.all_units == []
    print("  ✅ Empty roster")
    
    # Multi-detachment detection
    force1 = RosterForce(catalogue_name="Space Marines")
    force2 = RosterForce(catalogue_name="Imperial Guard")
    
    roster = RosterData(forces=[force1, force2])
    assert roster.is_multi_detachment
    print("  ✅ Multi-detachment detection")
    
    # Units aggregation
    unit1 = Unit(id="1", name="Captain", faction_id="SM")
    unit2 = Unit(id="2", name="Lieutenant", faction_id="SM")
    
    force = RosterForce(catalogue_name="Space Marines", units=[unit1, unit2])
    roster = RosterData(forces=[force])
    
    assert len(roster.all_units) == 2
    assert unit1 in roster.all_units
    assert unit2 in roster.all_units
    print("  ✅ Units aggregation")


def run_all_tests():
    """Run all model tests."""
    print("🧪 Running Domain Model Tests\n")
    
    try:
        test_faction_creation()
        test_unit_creation()
        test_stratagem_creation()
        test_processing_options()
        test_roster_data()
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)