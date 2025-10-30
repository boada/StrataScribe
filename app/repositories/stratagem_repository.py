"""
Stratagem Repository for data access layer.

Provides clean, testable access to stratagem data from Wahapedia,
replacing the global dictionary pattern with repository pattern.
"""
import logging
from typing import List, Dict, Any, Optional

from app.services.wahapedia_service import WahapediaService
from app.models.domain import Faction, Stratagem
from app.models.external import WahapediaDatasheet


# Set up logger
logger = logging.getLogger(__name__)


class StratagemRepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class StratagemRepository:
    """
    Repository for accessing stratagem data and related game information.
    
    Provides high-level query methods for stratagems, datasheets, and factions
    while hiding the complexity of data access and transformation.
    """
    
    def __init__(self, wahapedia_service: WahapediaService):
        """
        Initialize repository with Wahapedia service dependency.
        
        Args:
            wahapedia_service: Service for accessing Wahapedia data
        """
        self.wahapedia_service = wahapedia_service
        
        # Cache for frequently accessed data
        self._factions_cache: Optional[List[Faction]] = None
        self._stratagems_cache: Optional[List[Stratagem]] = None
        self._datasheets_cache: Optional[List[WahapediaDatasheet]] = None
        self._datasheet_stratagems_cache: Optional[List[Dict[str, str]]] = None
        
        logger.info("StratagemRepository initialized")
    
    def initialize(self) -> bool:
        """
        Initialize repository by loading basic data.
        
        Returns:
            True if data was updated, False if already current
        """
        try:
            updated = self.wahapedia_service.initialize()
            
            # Clear caches if data was updated
            if updated:
                self._clear_caches()
            
            return updated
            
        except Exception as e:
            logger.error(f"Failed to initialize repository: {e}")
            raise StratagemRepositoryError(f"Repository initialization failed: {e}")
    
    def get_all_factions(self) -> List[Faction]:
        """
        Get all available factions.
        
        Returns:
            List of faction domain objects
        """
        if self._factions_cache is None:
            self._factions_cache = self.wahapedia_service.get_factions()
            logger.info(f"Loaded {len(self._factions_cache)} factions into cache")
        
        return self._factions_cache
    
    def get_faction_by_id(self, faction_id: str) -> Optional[Faction]:
        """
        Get a specific faction by ID.
        
        Args:
            faction_id: The faction identifier
            
        Returns:
            Faction domain object or None if not found
        """
        factions = self.get_all_factions()
        
        for faction in factions:
            if faction.id == faction_id:
                return faction
        
        return None
    
    def find_faction_by_name(self, faction_name: str) -> Optional[Faction]:
        """
        Find a faction by name (case-insensitive partial match).
        
        Args:
            faction_name: Name to search for
            
        Returns:
            Faction domain object or None if not found
        """
        factions = self.get_all_factions()
        faction_name_lower = faction_name.lower()
        
        # Try exact match first
        for faction in factions:
            if faction.name.lower() == faction_name_lower:
                return faction
        
        # Try partial match
        for faction in factions:
            if faction_name_lower in faction.name.lower():
                return faction
        
        return None
    
    def get_all_stratagems(self, faction_id: Optional[str] = None) -> List[Stratagem]:
        """
        Get all stratagems, optionally filtered by faction.
        
        Args:
            faction_id: Optional faction ID to filter by
            
        Returns:
            List of stratagem domain objects
        """
        if faction_id:
            # Don't cache faction-specific results
            return self.wahapedia_service.get_stratagems(faction_id=faction_id)
        
        if self._stratagems_cache is None:
            self._stratagems_cache = self.wahapedia_service.get_stratagems()
            logger.info(f"Loaded {len(self._stratagems_cache)} stratagems into cache")
        
        return self._stratagems_cache
    
    def get_stratagem_by_id(self, stratagem_id: str) -> Optional[Stratagem]:
        """
        Get a specific stratagem by ID.
        
        Args:
            stratagem_id: The stratagem identifier
            
        Returns:
            Stratagem domain object or None if not found
        """
        stratagems = self.get_all_stratagems()
        
        for stratagem in stratagems:
            if stratagem.id == stratagem_id:
                return stratagem
        
        return None
    
    def find_stratagems_by_type(self, stratagem_type: str, faction_id: Optional[str] = None) -> List[Stratagem]:
        """
        Find stratagems by type (e.g., "Core", "Battle Tactic").
        
        Args:
            stratagem_type: Type to search for (case-insensitive)
            faction_id: Optional faction ID to filter by
            
        Returns:
            List of matching stratagem domain objects
        """
        stratagems = self.get_all_stratagems(faction_id)
        type_lower = stratagem_type.lower()
        
        return [
            stratagem for stratagem in stratagems
            if type_lower in stratagem.type.lower()
        ]
    
    def find_core_stratagems(self, faction_id: Optional[str] = None) -> List[Stratagem]:
        """
        Find all core stratagems.
        
        Args:
            faction_id: Optional faction ID to filter by
            
        Returns:
            List of core stratagem domain objects
        """
        stratagems = self.get_all_stratagems(faction_id)
        return [stratagem for stratagem in stratagems if stratagem.is_core]
    
    def find_stratagems_by_phase(self, phase: str, faction_id: Optional[str] = None) -> List[Stratagem]:
        """
        Find stratagems by game phase.
        
        Args:
            phase: Game phase to search for
            faction_id: Optional faction ID to filter by
            
        Returns:
            List of matching stratagem domain objects
        """
        stratagems = self.get_all_stratagems(faction_id)
        phase_lower = phase.lower()
        
        return [
            stratagem for stratagem in stratagems
            if phase_lower in stratagem.phase.lower()
        ]
    
    def get_all_datasheets(self) -> List[WahapediaDatasheet]:
        """
        Get all unit datasheets.
        
        Returns:
            List of datasheet external models
        """
        if self._datasheets_cache is None:
            self._datasheets_cache = self.wahapedia_service.get_datasheets()
            logger.info(f"Loaded {len(self._datasheets_cache)} datasheets into cache")
        
        return self._datasheets_cache
    
    def find_datasheet_by_name(self, unit_name: str) -> Optional[WahapediaDatasheet]:
        """
        Find a datasheet by unit name (case-insensitive partial match).
        
        Args:
            unit_name: Name to search for
            
        Returns:
            Datasheet external model or None if not found
        """
        datasheets = self.get_all_datasheets()
        unit_name_lower = unit_name.lower()
        
        # Try exact match first
        for datasheet in datasheets:
            if datasheet.name.lower() == unit_name_lower:
                return datasheet
        
        # Try partial match
        for datasheet in datasheets:
            if unit_name_lower in datasheet.name.lower():
                return datasheet
        
        return None
    
    def get_datasheet_stratagems(self) -> List[Dict[str, str]]:
        """
        Get all datasheet-stratagem relationships.
        
        Returns:
            List of relationship dictionaries
        """
        if self._datasheet_stratagems_cache is None:
            self._datasheet_stratagems_cache = self.wahapedia_service.get_datasheet_stratagems()
            logger.info(f"Loaded {len(self._datasheet_stratagems_cache)} datasheet-stratagem relationships")
        
        return self._datasheet_stratagems_cache
    
    def find_stratagems_for_unit(self, unit_name: str) -> List[Stratagem]:
        """
        Find all stratagems that apply to a specific unit.
        
        Args:
            unit_name: Name of the unit
            
        Returns:
            List of applicable stratagem domain objects
        """
        # Find the unit's datasheet
        datasheet = self.find_datasheet_by_name(unit_name)
        if not datasheet:
            logger.warning(f"No datasheet found for unit: {unit_name}")
            return []
        
        # Find stratagem relationships for this datasheet
        relationships = self.get_datasheet_stratagems()
        stratagem_ids = [
            rel["stratagem_id"] for rel in relationships
            if rel.get("datasheet_id") == datasheet.id
        ]
        
        # Get the actual stratagems
        stratagems = []
        for stratagem_id in stratagem_ids:
            stratagem = self.get_stratagem_by_id(stratagem_id)
            if stratagem:
                stratagems.append(stratagem)
        
        return stratagems
    
    def find_faction_stratagems(self, faction_id: str, include_subfactions: bool = True) -> List[Stratagem]:
        """
        Find all stratagems for a specific faction.
        
        Args:
            faction_id: The faction identifier
            include_subfactions: Whether to include subfaction stratagems
            
        Returns:
            List of faction stratagem domain objects
        """
        all_stratagems = self.get_all_stratagems()
        
        faction_stratagems = []
        for stratagem in all_stratagems:
            # Direct faction match
            if stratagem.faction_id == faction_id:
                faction_stratagems.append(stratagem)
            # Subfaction match (if enabled)
            elif include_subfactions and stratagem.subfaction_id == faction_id:
                faction_stratagems.append(stratagem)
        
        return faction_stratagems
    
    def find_empty_stratagems(self, faction_ids: List[str]) -> List[Stratagem]:
        """
        Find stratagems that don't require specific units (faction-wide).
        
        Args:
            faction_ids: List of faction IDs to search
            
        Returns:
            List of faction-wide stratagem domain objects
        """
        relationships = self.get_datasheet_stratagems()
        
        # Get stratagem IDs that have unit requirements
        unit_required_ids = {rel["stratagem_id"] for rel in relationships if rel.get("datasheet_id")}
        
        # Find faction stratagems that don't have unit requirements
        empty_stratagems = []
        for faction_id in faction_ids:
            faction_stratagems = self.find_faction_stratagems(faction_id)
            for stratagem in faction_stratagems:
                if stratagem.id not in unit_required_ids:
                    empty_stratagems.append(stratagem)
        
        return empty_stratagems
    
    def _clear_caches(self):
        """Clear all cached data."""
        self._factions_cache = None
        self._stratagems_cache = None
        self._datasheets_cache = None
        self._datasheet_stratagems_cache = None
        logger.info("Repository caches cleared")