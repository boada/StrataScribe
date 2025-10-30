"""
Data models for external API responses and file formats.

These models represent data as it comes from external sources
before being transformed into domain models.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class WahapediaStratagem:
    """Raw stratagem data from Wahapedia CSV."""
    id: str
    name: str
    type: str
    cp_cost: str  # String because CSV data  
    description: str
    legend: str
    faction_id: str
    phase: Optional[str] = None  # Phase information (10th edition includes this directly)
    subfaction_id: Optional[str] = None
    detachment: Optional[str] = None
    detachment_id: Optional[str] = None
    source_id: Optional[str] = None
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'WahapediaStratagem':
        """Create from CSV dictionary row."""
        return cls(
            id=row.get('id', ''),
            name=row.get('name', ''),
            type=row.get('type', ''),
            cp_cost=row.get('cp_cost', '0'),
            description=row.get('description', ''),
            legend=row.get('legend', ''),
            faction_id=row.get('faction_id', ''),
            phase=row.get('phase') or None,  # 10th edition includes phase directly
            subfaction_id=row.get('subfaction_id') or None,
            detachment=row.get('detachment') or None, 
            detachment_id=row.get('detachment_id') or None,
            source_id=row.get('source_id') or None,
        )


@dataclass
class WahapediaDatasheet:
    """Raw unit datasheet from Wahapedia CSV."""
    id: str
    name: str
    faction_id: str
    subfaction_id: Optional[str] = None
    source_id: Optional[str] = None
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'WahapediaDatasheet':
        """Create from CSV dictionary row."""
        return cls(
            id=row.get('id', ''),
            name=row.get('name', ''), 
            faction_id=row.get('faction_id', ''),
            subfaction_id=row.get('subfaction_id') or None,
            source_id=row.get('source_id') or None,
        )


@dataclass
class WahapediaFaction:
    """Raw faction data from Wahapedia CSV."""
    id: str
    name: str
    parent_id: Optional[str] = None
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'WahapediaFaction':
        """Create from CSV dictionary row.""" 
        return cls(
            id=row.get('id', ''),
            name=row.get('name', ''),
            parent_id=row.get('parent_id') or None,
        )


@dataclass
class DatasheetStratagem:
    """Links datasheet to stratagem from CSV."""
    datasheet_id: str
    stratagem_id: str
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'DatasheetStratagem':
        """Create from CSV dictionary row."""
        return cls(
            datasheet_id=row.get('datasheet_id', ''),
            stratagem_id=row.get('stratagem_id', ''),
        )


@dataclass
class DetachmentAbility:
    """Detachment data from Wahapedia CSV."""
    detachment: str
    detachment_id: str
    name: Optional[str] = None
    type: Optional[str] = None
    
    @classmethod  
    def from_csv_row(cls, row: Dict[str, str]) -> 'DetachmentAbility':
        """Create from CSV dictionary row."""
        return cls(
            detachment=row.get('detachment', ''),
            detachment_id=row.get('detachment_id', ''),
            name=row.get('name') or None,
            type=row.get('type') or None,
        )


@dataclass
class StratagemPhase:
    """Phase information for stratagems."""
    stratagem_id: str  # Note: CSV uses 'id' but maps to stratagem
    phase: str
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'StratagemPhase':
        """Create from CSV dictionary row."""
        return cls(
            stratagem_id=row.get('id', ''),  # CSV has 'id' field
            phase=row.get('phase', ''),
        )


@dataclass  
class BattleScribeSelection:
    """Raw selection from BattleScribe XML."""
    name: str
    type: Optional[str] = None
    categories: List[Dict[str, Any]] = field(default_factory=list)
    selections: List['BattleScribeSelection'] = field(default_factory=list)
    rules: List[Dict[str, Any]] = field(default_factory=list)
    costs: List[Dict[str, Any]] = field(default_factory=list)
    raw_attributes: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_xml_dict(cls, data: Dict[str, Any]) -> 'BattleScribeSelection':
        """Create from parsed XML dictionary."""
        # Extract nested selections
        selections = []
        if 'selections' in data and 'selection' in data['selections']:
            sel_data = data['selections']['selection']
            if isinstance(sel_data, list):
                selections = [cls.from_xml_dict(s) for s in sel_data]
            elif isinstance(sel_data, dict):
                selections = [cls.from_xml_dict(sel_data)]
        
        return cls(
            name=data.get('@name', ''),
            type=data.get('@type'),
            categories=data.get('categories', []),
            selections=selections,
            rules=data.get('rules', []),
            costs=data.get('costs', []),
            raw_attributes=data,
        )


@dataclass
class FileUploadInfo:
    """Information about an uploaded roster file."""
    filename: str
    original_name: str
    file_extension: str
    upload_timestamp: datetime = field(default_factory=datetime.now)
    file_size: Optional[int] = None
    
    @property
    def is_archive(self) -> bool:
        """Check if this is a .rosz archive file."""
        return self.file_extension.lower() == '.rosz'
    
    @property
    def age_hours(self) -> float:
        """Get age of file in hours."""
        return (datetime.now() - self.upload_timestamp).total_seconds() / 3600