"""
Model conversion utilities.

Functions to transform between external data models and domain models.
"""
from typing import List, Dict, Any, Optional

from .domain import Faction, Unit, Stratagem, RosterForce, RosterData, StratagemReference
from .external import (
    WahapediaFaction, WahapediaDatasheet, WahapediaStratagem, 
    DatasheetStratagem, BattleScribeSelection
)


def wahapedia_faction_to_domain(wh_faction: WahapediaFaction) -> Faction:
    """Convert Wahapedia faction to domain faction."""
    return Faction(
        id=wh_faction.id,
        name=wh_faction.name,
        parent_id=wh_faction.parent_id
    )


def wahapedia_datasheet_to_unit(wh_datasheet: WahapediaDatasheet, keywords: Optional[List[str]] = None) -> Unit:
    """Convert Wahapedia datasheet to domain unit."""
    return Unit(
        id=wh_datasheet.id,
        name=wh_datasheet.name,
        faction_id=wh_datasheet.faction_id,
        keywords=keywords or []
    )


def wahapedia_stratagem_to_domain(wh_stratagem: WahapediaStratagem, phase: str = "") -> Stratagem:
    """Convert Wahapedia stratagem to domain stratagem."""
    try:
        cp_cost = int(wh_stratagem.cp_cost) if wh_stratagem.cp_cost.isdigit() else 0
    except (ValueError, AttributeError):
        cp_cost = 0
    
    return Stratagem(
        id=wh_stratagem.id,
        name=wh_stratagem.name,
        type=wh_stratagem.type,
        cp_cost=cp_cost,
        description=wh_stratagem.description,
        legend=wh_stratagem.legend,
        phase=phase,
        faction_id=wh_stratagem.faction_id,
        subfaction_id=wh_stratagem.subfaction_id,
        detachment=wh_stratagem.detachment,
        detachment_id=wh_stratagem.detachment_id
    )


def datasheet_stratagem_to_reference(ds_strat: DatasheetStratagem) -> StratagemReference:
    """Convert datasheet-stratagem link to reference."""
    return StratagemReference(
        stratagem_id=ds_strat.stratagem_id,
        datasheet_id=ds_strat.datasheet_id
    )


def battlescribe_to_unit(bs_selection: BattleScribeSelection, faction_id: str) -> Optional[Unit]:
    """Convert BattleScribe selection to domain unit if it represents a unit."""
    # Skip non-unit selections
    from app.config import SELECTION_NON_UNIT_TYPES
    if bs_selection.name in SELECTION_NON_UNIT_TYPES:
        return None
    
    # Extract keywords from categories or rules
    keywords = []
    for category in bs_selection.categories:
        if isinstance(category, dict) and 'name' in category:
            keywords.append(category['name'])
    
    # For now, we'll generate a simple ID based on name
    # In practice, this would need to match against Wahapedia datasheets
    unit_id = bs_selection.name.lower().replace(' ', '_')
    
    return Unit(
        id=unit_id,
        name=bs_selection.name,
        faction_id=faction_id,
        keywords=keywords
    )


def roster_xml_to_domain(xml_data: Dict[str, Any]) -> RosterData:
    """Convert parsed BattleScribe XML to domain roster."""
    roster_dict = xml_data.get('roster', {})
    
    # Extract basic roster info
    roster_name = roster_dict.get('@name')
    bs_version = roster_dict.get('@battleScribeVersion')
    
    # Extract forces
    forces = []
    forces_data = roster_dict.get('forces', {}).get('force', [])
    
    # Handle single force vs multiple forces
    if isinstance(forces_data, dict):
        forces_data = [forces_data]
    
    for force_data in forces_data:
        catalogue_name = force_data.get('@catalogueName', '')
        
        # Extract units from selections - simplified for now
        selections_data = force_data.get('selections', {}).get('selection', [])
        if isinstance(selections_data, dict):
            selections_data = [selections_data]
        
        # Extract basic unit information from selections
        units = []
        for selection in selections_data:
            # Look for unit-type selections (categories indicate unit types)
            categories = selection.get('categories', {}).get('category', [])
            if isinstance(categories, dict):
                categories = [categories]
                
            # Check if this looks like a unit (has unit-type categories)
            is_unit = False
            for category in categories:
                cat_name = category.get('@name', '').lower()
                # Common unit type indicators in BattleScribe
                if any(unit_type in cat_name for unit_type in ['character', 'battleline', 'infantry', 'vehicle', 'monster', 'unit']):
                    is_unit = True
                    break
            
            if is_unit:
                unit_name = selection.get('@name', '')
                unit_id = selection.get('@id', '')
                if unit_name:  # Only add if we have a name
                    # Standardize unit name using clean architecture mappings
                    from app.models.mappings import standardize_unit_name
                    standardized_name = standardize_unit_name(unit_name)
                    
                    # Ensure we have a valid string name
                    if not standardized_name or not isinstance(standardized_name, str):
                        standardized_name = unit_name
                    
                    unit = Unit(
                        id=unit_id,
                        name=standardized_name,
                        faction_id='',  # Will be filled by service layer
                        keywords=[]     # Will be extracted by service layer if needed
                    )
                    units.append(unit)
        
        # Create force with extracted units
        force = RosterForce(
            catalogue_name=catalogue_name,
            units=units,
            selections={'selection': selections_data}  # Keep raw data for further processing
        )
        forces.append(force)
    
    return RosterData(
        name=roster_name,
        battle_scribe_version=bs_version,
        forces=forces,
        raw_data=xml_data
    )


def convert_legacy_dict_list(dict_list: List[Dict[str, Any]], converter_func) -> List[Any]:
    """Helper to convert lists of legacy dictionaries to domain models."""
    results = []
    for item_dict in dict_list:
        try:
            domain_obj = converter_func(item_dict)
            results.append(domain_obj)
        except (KeyError, ValueError) as e:
            # Log error but continue processing
            print(f"Warning: Failed to convert dictionary {item_dict}: {e}")
            continue
    return results


# Convenience functions for batch conversion
def convert_wahapedia_factions(faction_dicts: List[Dict[str, Any]]) -> List[Faction]:
    """Convert list of faction dictionaries to domain factions."""
    wh_factions = [WahapediaFaction.from_csv_row(d) for d in faction_dicts]
    return [wahapedia_faction_to_domain(f) for f in wh_factions]


def convert_wahapedia_stratagems(stratagem_dicts: List[Dict[str, Any]], 
                                phase_dicts: Optional[List[Dict[str, Any]]] = None) -> List[Stratagem]:
    """Convert list of stratagem dictionaries to domain stratagems."""
    # Build phase lookup
    phase_lookup = {}
    if phase_dicts:
        for phase_dict in phase_dicts:
            strat_id = phase_dict.get('id', '')
            phase = phase_dict.get('phase', '')
            phase_lookup[strat_id] = phase
    
    wh_stratagems = [WahapediaStratagem.from_csv_row(d) for d in stratagem_dicts]
    return [
        wahapedia_stratagem_to_domain(s, phase_lookup.get(s.id, ''))
        for s in wh_stratagems
    ]