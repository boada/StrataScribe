"""
Core domain models for StrataScribe.

These dataclasses replace the scattered dictionaries throughout the codebase
and provide type safety, validation, and clear data contracts.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class StratagemType(Enum):
    """Valid stratagem types from Wahapedia."""
    BATTLE_TACTIC = "Battle Tactic Stratagem"
    STRATEGIC_PLOY = "Strategic Ploy Stratagem"
    EPIC_DEED = "Epic Deed Stratagem"
    REQUISITION = "Requisition Stratagem"
    WARGEAR = "Wargear Stratagem"
    CORE = "Core Stratagem"


@dataclass(frozen=True)
class Faction:
    """Represents a Warhammer 40k faction."""
    id: str
    name: str
    parent_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.id or not self.name:
            raise ValueError("Faction must have both id and name")


@dataclass(frozen=True)
class Unit:
    """Represents a unit from a BattleScribe roster."""
    id: str
    name: str
    faction_id: str
    keywords: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id or not self.name:
            raise ValueError("Unit must have both id and name")
    
    @property
    def clean_name(self) -> str:
        """Return name without apostrophes for matching."""
        return self.name.replace("'", "")


@dataclass(frozen=True)
class Stratagem:
    """Represents a stratagem from Wahapedia."""
    id: str
    name: str
    type: str
    cp_cost: int
    description: str
    legend: str
    phase: str
    faction_id: str
    subfaction_id: Optional[str] = None
    detachment: Optional[str] = None
    detachment_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.id or not self.name:
            raise ValueError("Stratagem must have both id and name")
        if self.cp_cost < 0:
            raise ValueError("CP cost cannot be negative")
    
    @property
    def is_core(self) -> bool:
        """Check if this is a core stratagem."""
        return "core" in self.type.lower()
    
    @property
    def stratagem_type(self) -> Optional[StratagemType]:
        """Get the standardized stratagem type."""
        for stype in StratagemType:
            if stype.value in self.type:
                return stype
        return None


@dataclass
class RosterForce:
    """Represents a single force in a BattleScribe roster."""
    catalogue_name: str
    faction: Optional[Faction] = None
    detachment: Optional[str] = None
    units: List[Unit] = field(default_factory=list)
    selections: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.catalogue_name:
            raise ValueError("Force must have a catalogue name")


@dataclass
class RosterData:
    """Complete parsed BattleScribe roster data."""
    name: Optional[str] = None
    battle_scribe_version: Optional[str] = None
    forces: List[RosterForce] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_multi_detachment(self) -> bool:
        """Check if this roster has multiple forces/detachments."""
        return len(self.forces) > 1
    
    @property
    def all_units(self) -> List[Unit]:
        """Get all units from all forces."""
        units = []
        for force in self.forces:
            units.extend(force.units)
        return units


@dataclass
class StratagemReference:
    """Links a stratagem to a specific datasheet/unit."""
    stratagem_id: str
    datasheet_id: str = ""  # Empty for faction-wide stratagems
    
    def __post_init__(self):
        if not self.stratagem_id:
            raise ValueError("Stratagem reference must have a stratagem_id")


@dataclass
class ProcessingOptions:
    """Web UI form options for stratagem processing."""
    show_units: bool = False
    show_phases: bool = False
    show_empty: bool = False
    show_core: bool = False
    dont_show_renown: bool = False
    dont_show_before: bool = False
    
    @classmethod
    def from_form_data(cls, form_data: Dict[str, str]) -> 'ProcessingOptions':
        """Create options from Flask request.form data."""
        return cls(
            show_units=form_data.get('show_units') == 'on',
            show_phases=form_data.get('show_phases') == 'on', 
            show_empty=form_data.get('show_empty') == 'on',
            show_core=form_data.get('show_core') == 'on',
            dont_show_renown=form_data.get('dont_show_renown') == 'on',
            dont_show_before=form_data.get('dont_show_before') == 'on',
        )
    
    @property 
    def ignored_phases(self) -> List[str]:
        """
        Get list of phases to ignore during processing.
        
        TODO: Implement "Before battle" phase filtering if needed for 10th edition.
        Currently returns empty list as 10th edition may not use this concept.
        """
        ignored = []
        # Legacy logic was: if dont_show_before: ignore "Before battle" phase
        # if self.dont_show_before:
        #     ignored.append("Before battle")
        return ignored





@dataclass
class ProcessingResult:
    """Final result of stratagem processing."""
    phases: List[Dict[str, List[str]]]  # Phase -> stratagem names by force
    units: List[Dict[str, List[str]]]   # Unit name -> stratagem names by force  
    all_stratagems: List[Stratagem]     # Complete list of applicable stratagems
    
    def __post_init__(self):
        if len(self.phases) != len(self.units):
            raise ValueError("Phases and units results must have same length")


# Type aliases for clarity
StratagemDict = Dict[str, Any]  # Raw stratagem dictionary from CSV
UnitDict = Dict[str, Any]       # Raw unit dictionary from CSV
FactionDict = Dict[str, Any]    # Raw faction dictionary from CSV