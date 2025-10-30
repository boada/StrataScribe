"""
Example showing the benefits of the new data models.

Compare old dictionary-based approach with new type-safe dataclasses.
"""
from app.models import Faction, Unit, Stratagem, ProcessingOptions


def old_way_example():
    """How data was handled before - error-prone dictionaries."""
    
    # Old: Raw dictionaries everywhere, no validation, typos possible
    faction_dict = {
        'id': 'SM',
        'name': 'Space Marines', 
        'parent_id': None
    }
    
    unit_dict = {
        'id': 'sm_captain',
        'name': 'Captain',
        'faction_id': 'SM'
        # Missing keywords field - silent bug!
    }
    
    stratagem_dict = {
        'id': 'strat_1',
        'name': 'Honour the Chapter',
        'typ': 'Battle Tactic Stratagem',  # Typo in 'type' - silent bug!
        'cp_cost': '1',  # String instead of int - runtime error later
        'description': 'Description here',
        'phase': 'Fight phase',
        'faction_id': 'SM'
    }
    
    # Accessing data requires key lookups, no IDE support
    print(f"Old faction: {faction_dict.get('name', 'Unknown')}")
    print(f"Old unit keywords: {unit_dict.get('keywords', [])}")  # Missing field
    print(f"Old stratagem cost: {int(stratagem_dict['cp_cost'])}")  # Manual conversion
    
    return faction_dict, unit_dict, stratagem_dict


def new_way_example():
    """How data is handled now - type-safe and validated."""
    
    # New: Type-safe dataclasses with validation
    faction = Faction(id='SM', name='Space Marines')
    
    unit = Unit(
        id='sm_captain', 
        name='Captain',
        faction_id='SM',
        keywords=['INFANTRY', 'CHARACTER']  # Required field, no missing data
    )
    
    stratagem = Stratagem(
        id='strat_1',
        name='Honour the Chapter',
        type='Battle Tactic Stratagem',  # IDE catches typos
        cp_cost=1,  # Correct type enforced
        description='Description here',
        legend='Legend here',
        phase='Fight phase',
        faction_id='SM'
    )
    
    # Clean property access with IDE support and type safety
    print(f"New faction: {faction.name}")
    print(f"New unit keywords: {unit.keywords}")
    print(f"New stratagem cost: {stratagem.cp_cost}")
    print(f"Is core stratagem: {stratagem.is_core}")
    print(f"Stratagem type: {stratagem.stratagem_type}")
    
    return faction, unit, stratagem


def comparison_demo():
    """Show the key improvements."""
    
    print("=== OLD WAY (Dictionaries) ===")
    try:
        old_way_example()
    except Exception as e:
        print(f"❌ Error with old approach: {e}")
    
    print("\n=== NEW WAY (Dataclasses) ===")
    try:
        faction, unit, stratagem = new_way_example()
        
        # Show validation in action
        print("\n🔒 Validation Examples:")
        try:
            invalid_faction = Faction(id='', name='Space Marines')
        except ValueError as e:
            print(f"✅ Caught invalid faction: {e}")
        
        try:
            invalid_stratagem = Stratagem(
                id='test', name='Test', type='Battle Tactic', 
                cp_cost=-1, description='', legend='', phase='', faction_id='SM'
            )
        except ValueError as e:
            print(f"✅ Caught invalid stratagem: {e}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    comparison_demo()