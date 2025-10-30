"""Data models and domain entities."""

# Domain models
from .domain import (
    Faction, Unit, Stratagem, RosterForce, RosterData,
    StratagemReference, ProcessingOptions, ProcessingResult,
    StratagemType, StratagemDict, UnitDict, FactionDict
)

# External API models  
from .external import (
    WahapediaStratagem, WahapediaDatasheet, WahapediaFaction,
    DatasheetStratagem, DetachmentAbility, StratagemPhase,
    BattleScribeSelection, FileUploadInfo
)

# Conversion utilities
from .converters import (
    wahapedia_faction_to_domain, wahapedia_datasheet_to_unit,
    wahapedia_stratagem_to_domain, datasheet_stratagem_to_reference,
    battlescribe_to_unit, roster_xml_to_domain,
    convert_wahapedia_factions, convert_wahapedia_stratagems
)

__all__ = [
    # Domain models
    'Faction', 'Unit', 'Stratagem', 'RosterForce', 'RosterData',
    'StratagemReference', 'ProcessingOptions', 'ProcessingResult',
    'StratagemType', 'StratagemDict', 'UnitDict', 'FactionDict',
    
    # External models
    'WahapediaStratagem', 'WahapediaDatasheet', 'WahapediaFaction', 
    'DatasheetStratagem', 'DetachmentAbility', 'StratagemPhase',
    'BattleScribeSelection', 'FileUploadInfo',
    
    # Converters
    'wahapedia_faction_to_domain', 'wahapedia_datasheet_to_unit',
    'wahapedia_stratagem_to_domain', 'datasheet_stratagem_to_reference',
    'battlescribe_to_unit', 'roster_xml_to_domain',
    'convert_wahapedia_factions', 'convert_wahapedia_stratagems',
]