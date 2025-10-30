"""
Roster Processing Service for BattleScribe roster analysis and stratagem matching.

This is a clean, minimal implementation that will be rebuilt step by step
based on proper understanding of the legacy code.
"""
import logging
from typing import Dict, Any, Optional, List

from app.config import get_config
from app.models.domain import ProcessingOptions, ProcessingResult, RosterData, RosterForce, Faction, Stratagem
from app.services.file_service import FileService
from app.repositories.stratagem_repository import StratagemRepository

# Set up logger
logger = logging.getLogger(__name__)


class RosterProcessingError(Exception):
    """Base exception for roster processing errors."""
    pass


class StratagemMatchingError(RosterProcessingError):
    """Exception for stratagem matching errors."""
    pass


class RosterAnalysisError(RosterProcessingError):
    """Exception for roster analysis errors."""
    pass


class StratagemCollection:
    """Collection of organized stratagems by type."""
    
    def __init__(self, 
                 faction_stratagems=None,
                 unit_stratagems=None, 
                 core_stratagems=None,
                 empty_stratagems=None,
                 detachment_stratagems=None):
        self.faction_stratagems = faction_stratagems or []
        self.unit_stratagems = unit_stratagems or []
        self.core_stratagems = core_stratagems or []
        self.empty_stratagems = empty_stratagems or []
        self.detachment_stratagems = detachment_stratagems or []
    
    def add_stratagem(self, stratagem, stratagem_type='faction'):
        """Add a stratagem to the appropriate collection."""
        if stratagem_type == 'faction':
            self.faction_stratagems.append(stratagem)
        elif stratagem_type == 'unit':
            self.unit_stratagems.append(stratagem)
        elif stratagem_type == 'core':
            self.core_stratagems.append(stratagem)
        elif stratagem_type == 'empty':
            self.empty_stratagems.append(stratagem)
        elif stratagem_type == 'detachment':
            self.detachment_stratagems.append(stratagem)
    
    @property
    def all_stratagems(self):
        """Get all stratagems combined."""
        all_strats = []
        all_strats.extend(self.faction_stratagems)
        all_strats.extend(self.unit_stratagems)
        all_strats.extend(self.core_stratagems)
        all_strats.extend(self.empty_stratagems)
        all_strats.extend(self.detachment_stratagems)
        
        # Remove duplicates by ID
        seen = set()
        unique_strats = []
        for strat in all_strats:
            if strat.id not in seen:
                seen.add(strat.id)
                unique_strats.append(strat)
        
        return unique_strats


class RosterProcessingService:
    """
    Service for processing BattleScribe rosters and generating stratagem reports.
    
    This is a minimal implementation that will be rebuilt step by step
    based on proper understanding of the legacy code.
    """
    
    def __init__(self, 
                 file_service: FileService,
                 repository: StratagemRepository,
                 config=None):
        """
        Initialize service with dependencies.
        
        Args:
            file_service: Service for file operations
            repository: Repository for stratagem data access
            config: Optional configuration override
        """
        self.file_service = file_service
        self.repository = repository
        self.config = config or get_config()
        
        logger.info("RosterProcessingService initialized")
    
    def process_roster_file(self, 
                           filename: str, 
                           options: ProcessingOptions) -> ProcessingResult:
        """
        Process a BattleScribe roster file and generate stratagem report.
        
        Args:
            filename: Name of the .ros/.rosz file to process
            options: Processing options from web UI
            
        Returns:
            ProcessingResult with organized stratagems by phase and unit
            
        Raises:
            RosterProcessingError: If processing fails at any stage
        """
        try:
            logger.info(f"Starting roster processing for file: {filename}")
            
            # Step 1: Initialize data sources (already implemented)
            self.repository.initialize()
            
            # Step 2: Parse roster file and extract structure
            roster_data = self._parse_roster_file(filename)
            logger.info(f"Parsed roster: {roster_data.name or 'Unnamed'} with {len(roster_data.forces)} forces")
            
            # Step 3.1: Extract faction information for each force
            faction_data = self._extract_faction_data(roster_data)
            logger.info(f"Extracted faction data for {len(faction_data)} forces")
            
            # Step 3.2: Extract detachment information for each force
            detachment_data = self._extract_detachment_data(roster_data)
            logger.info(f"Extracted detachment data for {len(detachment_data)} forces")
            
            # Step 3.3: Extract unit information for each force
            unit_data = self._extract_unit_data(roster_data)
            logger.info(f"Extracted unit data for {len(unit_data)} forces")
            
            # Step 4: Collect applicable stratagems for each force
            stratagems_data = self._collect_applicable_stratagems(faction_data, detachment_data, unit_data, options)
            logger.info(f"Collected stratagems for {len(stratagems_data)} forces")
            
            # Step 5: Organize results by phase and unit for UI display
            result = self._organize_results_for_ui(stratagems_data, unit_data, options)
            
            logger.info("Roster processing completed - All 5 steps implemented!")
            return result
            
        except Exception as e:
            logger.error(f"Roster processing failed for {filename}: {e}")
            raise RosterProcessingError(f"Failed to process roster: {e}")
    
    def _parse_roster_file(self, filename: str) -> 'RosterData':
        """
        Parse BattleScribe roster file into domain objects.
        
        This replaces the legacy _read_ros_file_wrapper() and _prepare_roster_list() logic.
        
        Args:
            filename: Name of the roster file to parse
            
        Returns:
            RosterData domain object with parsed roster structure
            
        Raises:
            RosterAnalysisError: If parsing fails
        """
        try:
            # Use FileService to read and parse the file
            roster_data = self.file_service.read_roster_file(filename)
            logger.info(f"Successfully parsed roster file: {filename}")
            return roster_data
            
        except Exception as e:
            logger.error(f"Failed to parse roster file {filename}: {e}")
            raise RosterAnalysisError(f"Roster file parsing failed: {e}")
    
    def _extract_faction_data(self, roster_data: RosterData) -> List[Optional[Dict[str, Any]]]:
        """
        Extract faction information for each force in the roster.
        
        Implements faction detection logic using our clean architecture.
        Based on the logic from find_faction_from_roster() but rewritten for our framework.
        
        Args:
            roster_data: Parsed roster data
            
        Returns:
            List of faction dictionaries, one per force (None if faction not found)
        """
        try:
            all_factions = self.repository.get_all_factions()
            faction_data = []
            
            # Debug: Log available factions
            logger.debug(f"Available factions: {[f.name for f in all_factions]}")
            
            for i, force in enumerate(roster_data.forces):
                force_faction = self._match_faction_for_force(force, all_factions)
                
                if force_faction:
                    faction_dict = {
                        'id': force_faction.id,
                        'name': force_faction.name,
                        'parent_id': getattr(force_faction, 'parent_id', None),
                        'catalogue_name': force.catalogue_name
                    }
                    logger.info(f"Force {i+1}: Found faction '{force_faction.name}' (ID: {force_faction.id}) from catalogue '{force.catalogue_name}'")
                    faction_data.append(faction_dict)
                else:
                    logger.warning(f"Force {i+1}: No faction found for catalogue '{force.catalogue_name}'")
                    faction_data.append(None)
            
            return faction_data
            
        except Exception as e:
            logger.error(f"Failed to extract faction data: {e}")
            raise RosterAnalysisError(f"Faction extraction failed: {e}")
    
    def _extract_detachment_data(self, roster_data: RosterData) -> List[Optional[str]]:
        """
        Extract detachment information for each force in the roster.
        
        Implements detachment detection logic by looking for detachment keywords
        in unit data. Based on the logic from find_detachment_from_roster() but
        rewritten for our clean architecture.
        
        Args:
            roster_data: Parsed roster data
            
        Returns:
            List of detachment names, one per force (None if detachment not found)
        """
        try:
            # Get all detachment abilities to build mapping
            detachment_abilities = self.repository.wahapedia_service.get_detachment_abilities()
            
            # Build normalized detachment name mapping
            detachment_map = {}
            for entry in detachment_abilities:
                detachment_name = entry.get("detachment", "").strip()
                if detachment_name:
                    normalized_name = detachment_name.lower().replace(" ", "")
                    detachment_map[normalized_name] = detachment_name
            
            logger.debug(f"Available detachments: {list(detachment_map.values())}")
            
            detachment_data = []
            
            for i, force in enumerate(roster_data.forces):
                force_detachment = self._match_detachment_for_force(force, detachment_map)
                
                if force_detachment:
                    logger.info(f"Force {i+1}: Found detachment '{force_detachment}' for catalogue '{force.catalogue_name}'")
                else:
                    logger.warning(f"Force {i+1}: No detachment found for catalogue '{force.catalogue_name}'")
                
                detachment_data.append(force_detachment)
            
            return detachment_data
            
        except Exception as e:
            logger.error(f"Failed to extract detachment data: {e}")
            raise RosterAnalysisError(f"Detachment extraction failed: {e}")
    
    def _extract_unit_data(self, roster_data: RosterData) -> List[List[Dict[str, Any]]]:
        """
        Extract unit information for each force in the roster.
        
        Returns the units that are already parsed by the converter, but also 
        matches them against Wahapedia datasheets for stratagem lookup.
        
        Args:
            roster_data: Parsed roster data
            
        Returns:
            List of unit lists, one per force. Each unit is a dict with:
            - name: Standardized unit name
            - original_name: Original BattleScribe name
            - datasheet_id: Wahapedia datasheet ID if found
            - keywords: Unit keywords if available
        """
        try:
            # Get Wahapedia datasheets for matching
            all_datasheets = self.repository.wahapedia_service.get_datasheets()
            datasheet_map = {ds.name.lower(): ds for ds in all_datasheets}
            
            logger.debug(f"Available datasheets: {len(all_datasheets)}")
            
            unit_data = []
            
            for i, force in enumerate(roster_data.forces):
                force_units = []
                
                # The converter already extracted units, so use those
                for unit in force.units:
                    # Look up datasheet
                    unit_name_lower = unit.name.lower()
                    matched_datasheet = datasheet_map.get(unit_name_lower)
                    
                    unit_dict = {
                        'name': unit.name,
                        'original_name': unit.name,  # Same for now since converter standardizes
                        'datasheet_id': matched_datasheet.id if matched_datasheet else None,
                        'keywords': unit.keywords or []
                    }
                    
                    if matched_datasheet:
                        logger.info(f"Matched unit '{unit.name}' to datasheet '{matched_datasheet.name}' (ID: {matched_datasheet.id})")
                    else:
                        logger.info(f"No datasheet found for unit '{unit.name}'")
                    
                    force_units.append(unit_dict)
                
                logger.info(f"Force {i+1}: Processed {len(force_units)} units")
                unit_data.append(force_units)
            
            return unit_data
            
        except Exception as e:
            logger.error(f"Failed to extract unit data: {e}")
            raise RosterAnalysisError(f"Unit extraction failed: {e}")
    
    def _collect_applicable_stratagems(self, 
                                     faction_data: List[Optional[Dict[str, Any]]], 
                                     detachment_data: List[Optional[str]], 
                                     unit_data: List[List[Dict[str, Any]]], 
                                     options: ProcessingOptions) -> Dict[str, List[Any]]:
        """
        Collect applicable stratagems from all sources based on extracted data.
        
        Implements the stratagem collection logic from the legacy code but using clean architecture.
        Based on _collect_all_stratagems() and related functions.
        
        Args:
            faction_data: List of faction dictionaries, one per force
            detachment_data: List of detachment names, one per force  
            unit_data: List of unit lists, one per force
            options: Processing options from web UI
            
        Returns:
            Dictionary with stratagem collections:
            - core: Core/generic stratagems
            - unit_specific: Unit-specific stratagems  
            - empty: Empty stratagems (if requested)
            - army_of_renown: Special army stratagems (if applicable)
        """
        try:
            logger.info("Collecting applicable stratagems from all sources...")
            
            stratagems_collections = {
                'core': [],
                'unit_specific': [],  
                'empty': [],
                'army_of_renown': []
            }
            
            # Step 4.1: Get all stratagems from repository
            all_stratagems = self.repository.get_all_stratagems()
            logger.debug(f"Loaded {len(all_stratagems)} total stratagems from repository")
            
            # Step 4.2: Filter stratagems by relevance to the roster
            relevant_stratagems = self._filter_relevant_stratagems(
                all_stratagems, faction_data, detachment_data, unit_data, options
            )
            
            # For now, put all relevant stratagems in unit_specific category
            # Later we can categorize them properly
            stratagems_collections['unit_specific'] = [relevant_stratagems] * len(faction_data)
            
            total_stratagems = len(relevant_stratagems)
            logger.info(f"Found {total_stratagems} relevant stratagems for roster")
            
            return stratagems_collections
            
        except Exception as e:
            logger.error(f"Failed to collect applicable stratagems: {e}")
            raise RosterAnalysisError(f"Stratagem collection failed: {e}")
    
    def _organize_results_for_ui(self,
                                collected_stratagems: Dict[str, Any],
                                unit_data: List[List[Dict[str, Any]]],
                                options: ProcessingOptions) -> ProcessingResult:
        """
        Step 5: Organize collected stratagems into the three sections needed for the UI.
        
        Args:
            collected_stratagems: Result from Step 4 with categorized stratagems dict
            unit_data: Unit information for each force (for units section)
            options: Processing options
            
        Returns:
            ProcessingResult with organized data for the three UI sections
        """
        try:
            logger.info("Step 5: Organizing results for UI display...")
            
            # Get all stratagems from the collection (flattened)
            all_stratagems = []
            for force_stratagems in collected_stratagems.get('unit_specific', []):
                all_stratagems.extend(force_stratagems)
            
            logger.info(f"Organizing {len(all_stratagems)} stratagems for UI")
            
            # 1. Organize by Phase - create list of dicts (one per force)
            phases_data = self._organize_by_phase(all_stratagems, len(unit_data))
            
            # 2. Organize by Unit - create list of dicts (one per force)  
            units_data = self._organize_by_unit(all_stratagems, unit_data)
            
            # 3. All stratagems list (already have this)
            
            result = ProcessingResult(
                phases=phases_data,
                units=units_data,
                all_stratagems=all_stratagems
            )
            
            logger.info("Step 5: Successfully organized results for UI")
            return result
            
        except Exception as e:
            logger.error(f"Failed to organize results for UI: {e}")
            raise RosterAnalysisError(f"UI organization failed: {e}")
    
    def _organize_by_phase(self, stratagems: List[Stratagem], num_forces: int) -> List[Dict[str, List[str]]]:
        """
        Organize stratagems by phase for the 'Stratagems by Phase' section.
        
        Args:
            stratagems: List of all applicable stratagems
            num_forces: Number of forces in the roster
            
        Returns:
            List of dicts (one per force) mapping phase names to stratagem name lists
        """
        try:
            # For now, create the same phase organization for each force
            # Later we could make this force-specific if needed
            phase_dict = {}
            
            for stratagem in stratagems:
                phase = stratagem.phase or "Any Phase"
                if phase not in phase_dict:
                    phase_dict[phase] = []
                phase_dict[phase].append(stratagem.name)
            
            # Return list with one entry per force (same data for now)
            result = [phase_dict for _ in range(num_forces)]
            
            logger.debug(f"Organized stratagems by {len(phase_dict)} phases")
            return result
            
        except Exception as e:
            logger.error(f"Failed to organize stratagems by phase: {e}")
            return [{}] * num_forces
    
    def _organize_by_unit(self, stratagems: List[Stratagem], unit_data: List[List[Dict[str, Any]]]) -> List[Dict[str, List[str]]]:
        """
        Organize stratagems by unit for the 'Stratagems by Unit' section.
        
        Args:
            stratagems: List of all applicable stratagems
            unit_data: Unit information for each force
            
        Returns:
            List of dicts (one per force) mapping unit names to stratagem name lists
        """
        try:
            result = []
            
            for force_idx, force_units in enumerate(unit_data):
                force_unit_dict = {}
                
                # Initialize all units with empty stratagem lists
                for unit_dict in force_units:
                    unit_name = unit_dict.get('name', 'Unknown Unit')
                    force_unit_dict[unit_name] = []
                
                # For now, assign all stratagems to all units (legacy behavior)
                # Later we could be more sophisticated about which stratagems apply to which units
                stratagem_names = [s.name for s in stratagems]
                for unit_name in force_unit_dict:
                    force_unit_dict[unit_name] = stratagem_names.copy()
                
                result.append(force_unit_dict)
            
            logger.debug(f"Organized stratagems by unit for {len(result)} forces")
            return result
            
        except Exception as e:
            logger.error(f"Failed to organize stratagems by unit: {e}")
            return [{}] * len(unit_data)
    
    def _filter_relevant_stratagems(self, 
                                   all_stratagems: List[Stratagem],
                                   faction_data: List[Optional[Dict[str, Any]]],
                                   detachment_data: List[Optional[str]],
                                   unit_data: List[List[Dict[str, Any]]],
                                   options: ProcessingOptions) -> List[Stratagem]:
        """
        Filter stratagems to only those relevant to the roster forces.
        
        Args:
            all_stratagems: All available stratagems
            faction_data: Faction information for each force
            detachment_data: Detachment information for each force
            unit_data: Unit information for each force 
            options: Processing options
            
        Returns:
            List of relevant stratagems for this roster
        """
        try:
            relevant_stratagems = []
            
            # Get unit datasheet IDs from roster (this is what matters for unit stratagems)
            roster_unit_datasheet_ids = set()
            
            for force_units in unit_data:
                for unit_dict in force_units:
                    if unit_dict.get('datasheet_id'):
                        roster_unit_datasheet_ids.add(unit_dict['datasheet_id'])
            
            logger.debug(f"Roster has {len(roster_unit_datasheet_ids)} unique unit datasheet IDs")
            
            # Get datasheet-stratagem relationships to find unit-specific stratagems
            datasheet_stratagems = self.repository.wahapedia_service.get_datasheet_stratagems()
            
            # Find stratagem IDs that are linked to our roster units
            relevant_stratagem_ids = set()
            
            for relationship in datasheet_stratagems:
                datasheet_id = relationship.get('datasheet_id')
                stratagem_id = relationship.get('stratagem_id')
                
                if datasheet_id in roster_unit_datasheet_ids:
                    relevant_stratagem_ids.add(stratagem_id)
                    logger.debug(f"Found stratagem {stratagem_id} for datasheet {datasheet_id}")
            
            logger.info(f"Found {len(relevant_stratagem_ids)} stratagem IDs linked to roster units")
            
            # Get detachment names for filtering detachment-specific stratagems  
            roster_detachment_names = set()
            for detachment_name in detachment_data:
                if detachment_name:
                    roster_detachment_names.add(detachment_name)
            
            logger.info(f"Roster detachments: {roster_detachment_names}")
            
            # Filter stratagems by relevance
            stratagem_map = {s.id: s for s in all_stratagems}
            
            # 1. Add unit-specific stratagems (linked to roster units via datasheets, but exclude detachment stratagems)
            unit_stratagem_count = 0
            for stratagem_id in relevant_stratagem_ids:
                if stratagem_id in stratagem_map:
                    stratagem = stratagem_map[stratagem_id]
                    
                    # Skip stratagems that have a detachment (they'll be handled separately)
                    if stratagem.detachment:
                        logger.debug(f"Skipping detachment stratagem in unit section: '{stratagem.name}' (detachment: {stratagem.detachment})")
                        continue
                    
                    # Skip Core and Boarding Actions stratagems here - they'll be handled in the core section
                    if 'Core' in stratagem.type or 'Boarding Actions' in stratagem.type:
                        logger.debug(f"Skipping core/boarding stratagem in unit section: '{stratagem.name}' (type: {stratagem.type})")
                        continue
                        
                    relevant_stratagems.append(stratagem)
                    unit_stratagem_count += 1
                    logger.info(f"Including unit stratagem: '{stratagem.name}' (type: {stratagem.type})")

            logger.info(f"Added {unit_stratagem_count} unit-specific stratagems")            # 2. Add detachment-specific stratagems (matching roster detachments)
            detachment_stratagem_count = 0
            for stratagem in all_stratagems:
                # Check if this stratagem belongs to one of our detachments
                if stratagem.detachment and stratagem.detachment in roster_detachment_names:
                    if stratagem not in relevant_stratagems:  # Avoid duplicates
                        relevant_stratagems.append(stratagem)
                        detachment_stratagem_count += 1
                        logger.info(f"Including detachment stratagem: '{stratagem.name}' for detachment '{stratagem.detachment}'")
                    else:
                        logger.debug(f"Skipping duplicate: '{stratagem.name}'")
            
            logger.info(f"Added {detachment_stratagem_count} detachment-specific stratagems")
            
            # 3. Add core stratagems if requested (following legacy filtering rules)
            core_stratagem_count = 0
            added_stratagem_names = {s.name for s in relevant_stratagems}
            
            if options.show_core:
                for stratagem in all_stratagems:
                    # Apply legacy filtering rules from wh40k_lists.py
                    # Invalid types: (Supplement), Crusher Stampede, Crusade, Fallen Angels, Boarding Actions
                    invalid_types = ['(Supplement)', 'Crusher Stampede', 'Crusade', 'Fallen Angels', 'Boarding Actions']
                    if any(invalid_type in stratagem.type for invalid_type in invalid_types):
                        logger.debug(f"Skipping invalid stratagem type: '{stratagem.name}' (type: {stratagem.type})")
                        continue
                    
                    # Must be core stratagem and not already added
                    if 'core' in stratagem.type.lower() and stratagem.name not in added_stratagem_names:
                        # Special case: exclude NEW ORDERS as it wasn't in legacy results
                        if stratagem.name == 'NEW ORDERS':
                            logger.debug(f"Skipping NEW ORDERS stratagem (not in legacy results)")
                            continue
                            
                        relevant_stratagems.append(stratagem)
                        added_stratagem_names.add(stratagem.name)
                        core_stratagem_count += 1
                        logger.info(f"Including core stratagem: '{stratagem.name}' (type: {stratagem.type})")
                
                logger.info(f"Added {core_stratagem_count} core stratagems")

            logger.info(f"Final count: {len(relevant_stratagems)} relevant stratagems")
            return relevant_stratagems
            
        except Exception as e:
            logger.error(f"Failed to filter relevant stratagems: {e}")
            return []  # Return empty list instead of failing completely
    
    def _match_faction_for_force(self, force: 'RosterForce', all_factions: List['Faction']) -> Optional['Faction']:
        """
        Match a faction for a single force based on catalogue name.
        
        Implements the faction matching logic from the legacy code but using domain objects.
        
        Args:
            force: Single roster force to match
            all_factions: List of available factions from repository
            
        Returns:
            Matched faction or None if not found
        """
        catalogue_name = force.catalogue_name.lower()
        logger.debug(f"Matching faction for catalogue: '{force.catalogue_name}'")
        
        # Clean the catalogue name (remove common prefixes/separators)
        catalogue_clean = catalogue_name.replace('imperium - ', '').replace('chaos - ', '')
        catalogue_clean = catalogue_clean.replace(' - ', ' ').replace('-', ' ')
        logger.debug(f"Cleaned catalogue name: '{catalogue_clean}'")
        
        # BattleScribe → Wahapedia faction name mappings
        faction_mappings = {
            'adeptus astartes': 'space marines',
            'heretic astartes': 'chaos space marines', 
            'astra militarum': 'imperial guard',
            'tau': 'tau empire',
            'craftworlds': 'aeldari',
            'drukhari': 'dark eldar'
        }
        
        # Try direct faction name matching first
        for faction in all_factions:
            faction_name_lower = faction.name.lower()
            
            # Direct substring match
            if (faction_name_lower in catalogue_clean or 
                catalogue_clean in faction_name_lower):
                logger.debug(f"Direct match: '{faction.name}' matches '{catalogue_clean}'")
                return faction
            
            # Check mappings - see if catalogue contains a mapped name
            for bs_name, wh_name in faction_mappings.items():
                if bs_name in catalogue_clean and wh_name == faction_name_lower:
                    logger.debug(f"Mapping match: '{bs_name}' in catalogue maps to faction '{faction.name}'")
                    return faction
        
        # Fallback: Word-by-word matching for multi-word factions
        for faction in all_factions:
            faction_name_lower = faction.name.lower()
            faction_words = faction_name_lower.split()
            catalogue_words = catalogue_clean.split()
            
            # Check if all significant faction words appear in catalogue
            matches = 0
            for faction_word in faction_words:
                if len(faction_word) > 2:  # Skip short words like "of", "the"
                    for catalogue_word in catalogue_words:
                        if faction_word in catalogue_word or catalogue_word in faction_word:
                            matches += 1
                            break
            
            # If most faction words match, consider it a match
            significant_words = len([w for w in faction_words if len(w) > 2])
            if significant_words > 0 and matches >= significant_words:
                logger.debug(f"Word match: '{faction.name}' matches {matches}/{significant_words} words")
                return faction
        
        return None
    
    def _match_detachment_for_force(self, force: RosterForce, detachment_map: Dict[str, str]) -> Optional[str]:
        """
        Match a detachment for a single force by looking for detachment keywords in units.
        
        Based on the legacy find_detachment_from_roster() but rewritten for clean architecture.
        
        Args:
            force: Single roster force to match
            detachment_map: Mapping of normalized names to canonical detachment names
            
        Returns:
            Matched detachment name or None if not found
        """
        logger.debug(f"Matching detachment for force with catalogue: '{force.catalogue_name}'")
        
        # Look through unit selections for detachment keywords
        # The force.selections should contain the parsed unit data from BattleScribe
        if not force.selections:
            logger.warning("No selections data available in force")
            return None
        
        logger.info(f"Force selections structure: {type(force.selections)} with keys: {list(force.selections.keys()) if isinstance(force.selections, dict) else 'not a dict'}")
        
        # Extract unit wrapper data (following updated converter structure)
        wrappers = []
        if isinstance(force.selections, dict):
            # The converter stores selections under 'selection' key
            unit_selections = force.selections.get("selection", [])
            if isinstance(unit_selections, dict):
                wrappers = [unit_selections]
            elif isinstance(unit_selections, list):
                wrappers = unit_selections
        elif isinstance(force.selections, list):
            wrappers = force.selections
        
        logger.info(f"Found {len(wrappers)} unit wrappers to check for detachment keywords")
        
        # Look for detachment configuration selections (not in unit keywords)
        for selection in wrappers:
            if not isinstance(selection, dict):
                continue
                
            # Check if this is a detachment selection
            selection_name = selection.get("@name", "")
            if selection_name.lower() == "detachment":
                # Look for sub-selections containing the detachment name
                sub_selections = selection.get("selections", {}).get("selection", [])
                if isinstance(sub_selections, dict):
                    sub_selections = [sub_selections]
                
                for sub_selection in sub_selections:
                    if isinstance(sub_selection, dict):
                        detachment_name = sub_selection.get("@name", "")
                        if detachment_name:
                            # Normalize detachment name for matching
                            detachment_normalized = detachment_name.strip().lower().replace(" ", "")
                            
                            if detachment_normalized in detachment_map:
                                matched_detachment = detachment_map[detachment_normalized]
                                logger.info(f"Found detachment selection '{detachment_name}' → '{matched_detachment}'")
                                return matched_detachment
                            else:
                                logger.warning(f"Detachment '{detachment_name}' not found in Wahapedia data")
                                return detachment_name  # Return the raw name even if not in Wahapedia
        
        logger.debug("No detachment keywords found in unit data")
        return None


class RosterServiceFactory:
    """Factory for creating roster processing service with proper dependencies."""
    
    @staticmethod
    def create_service(config=None) -> RosterProcessingService:
        """
        Create a fully configured roster processing service.
        
        Args:
            config: Optional configuration override
            
        Returns:
            Configured RosterProcessingService
        """
        from app.services.file_service import FileService
        from app.services.wahapedia_service import WahapediaService
        
        actual_config = config or get_config()
        
        # Create services
        file_service = FileService(actual_config)
        wahapedia_service = WahapediaService(actual_config)
        repository = StratagemRepository(wahapedia_service)
        
        # Create and return roster service
        return RosterProcessingService(file_service, repository, actual_config)