"""
Wahapedia service for managing external data from Wahapedia API.

Handles downloading, caching, and providing access to Warhammer 40k game data
with proper error handling, retry logic, and integration with our domain models.
"""
import csv
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from app.config import get_config
from app.models.domain import Faction, Stratagem
from app.models.external import WahapediaFaction, WahapediaStratagem, WahapediaDatasheet
from app.models.converters import wahapedia_faction_to_domain, wahapedia_stratagem_to_domain


# Set up logger
logger = logging.getLogger(__name__)


class WahapediaServiceError(Exception):
    """Base exception for Wahapedia service errors."""
    pass


class WahapediaDownloadError(WahapediaServiceError):
    """Raised when data download fails."""
    pass


class WahapediaDataError(WahapediaServiceError):
    """Raised when data is invalid or corrupted."""
    pass


class WahapediaService:
    """
    Service for accessing Wahapedia game data.
    
    Manages downloading, caching, and parsing CSV data from Wahapedia
    with automatic updates and proper error handling.
    """
    
    def __init__(self, config=None):
        """Initialize Wahapedia service with configuration."""
        self.config = config or get_config()
        
        # Directory setup
        self.data_dir = Path(self.config.WAHAPEDIA_DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # File tracking
        self.file_list_path = self.data_dir / "_file_list.json"
        
        # Download settings
        self.base_url = self.config.WAHAPEDIA_BASE_URL
        self.csv_files = self.config.WAHAPEDIA_CSV_FILES
        self.max_retries = self.config.WAHAPEDIA_MAX_RETRIES
        self.retry_delay = self.config.WAHAPEDIA_RETRY_DELAY
        self.rate_limit_delay = self.config.WAHAPEDIA_RATE_LIMIT_DELAY
        
        logger.info(f"WahapediaService initialized with data directory: {self.data_dir}")
    
    def initialize(self) -> bool:
        """
        Initialize local database by checking for updates.
        
        Returns:
            True if any files were updated, False otherwise
            
        Raises:
            WahapediaServiceError: If initialization fails
        """
        try:
            updated = False
            
            if self._has_updates():
                for csv_file in self.csv_files:
                    if self._update_csv_file(csv_file):
                        updated = True
            
            logger.info(f"Wahapedia initialization complete. Updated: {updated}")
            return updated
            
        except Exception as e:
            logger.error(f"Failed to initialize Wahapedia database: {e}")
            raise WahapediaServiceError(f"Initialization failed: {e}")
    
    def get_factions(self) -> List[Faction]:
        """
        Get all factions as domain models.
        
        Returns:
            List of faction domain objects
            
        Raises:
            WahapediaDataError: If faction data is invalid
        """
        try:
            factions_csv = self._read_csv_file("Factions.csv")
            
            domain_factions = []
            for row in factions_csv:
                try:
                    wh_faction = WahapediaFaction.from_csv_row(row)
                    domain_faction = wahapedia_faction_to_domain(wh_faction)
                    domain_factions.append(domain_faction)
                except Exception as e:
                    logger.warning(f"Skipping invalid faction row: {e}")
                    continue
            
            logger.info(f"Loaded {len(domain_factions)} factions from Wahapedia")
            return domain_factions
            
        except Exception as e:
            logger.error(f"Failed to load factions: {e}")
            raise WahapediaDataError(f"Cannot load factions: {e}")
    
    def get_stratagems(self, faction_id: Optional[str] = None) -> List[Stratagem]:
        """
        Get stratagems as domain models, optionally filtered by faction.
        
        Args:
            faction_id: Optional faction ID to filter by
            
        Returns:
            List of stratagem domain objects
            
        Raises:
            WahapediaDataError: If stratagem data is invalid
        """
        try:
            stratagems_csv = self._read_csv_file("Stratagems.csv")
            
            # Note: Phase information is now included directly in Stratagems.csv (10th edition)
            # No need for separate StratagemPhases.csv file
            
            domain_stratagems = []
            for row in stratagems_csv:
                try:
                    wh_stratagem = WahapediaStratagem.from_csv_row(row)
                    
                    # Filter by faction if specified
                    if faction_id and wh_stratagem.faction_id != faction_id:
                        continue
                    
                    # Phase info is now part of the stratagem data directly (10th edition)
                    phase = wh_stratagem.phase or ''
                    
                    domain_stratagem = wahapedia_stratagem_to_domain(wh_stratagem, phase)
                    domain_stratagems.append(domain_stratagem)
                    
                except Exception as e:
                    logger.warning(f"Skipping invalid stratagem row: {e}")
                    continue
            
            logger.info(f"Loaded {len(domain_stratagems)} stratagems from Wahapedia")
            return domain_stratagems
            
        except Exception as e:
            logger.error(f"Failed to load stratagems: {e}")
            raise WahapediaDataError(f"Cannot load stratagems: {e}")
    
    def get_datasheets(self) -> List[WahapediaDatasheet]:
        """
        Get all datasheets (raw external models for now).
        
        Returns:
            List of datasheet external models
            
        Raises:
            WahapediaDataError: If datasheet data is invalid
        """
        try:
            datasheets_csv = self._read_csv_file("Datasheets.csv")
            
            datasheets = []
            for row in datasheets_csv:
                try:
                    datasheet = WahapediaDatasheet.from_csv_row(row)
                    datasheets.append(datasheet)
                except Exception as e:
                    logger.warning(f"Skipping invalid datasheet row: {e}")
                    continue
            
            logger.info(f"Loaded {len(datasheets)} datasheets from Wahapedia")
            return datasheets
            
        except Exception as e:
            logger.error(f"Failed to load datasheets: {e}")
            raise WahapediaDataError(f"Cannot load datasheets: {e}")
    
    def get_datasheet_stratagems(self) -> List[Dict[str, str]]:
        """
        Get datasheet-stratagem relationships.
        
        Returns:
            List of relationship dictionaries
            
        Raises:
            WahapediaDataError: If relationship data is invalid
        """
        try:
            relationships_csv = self._read_csv_file("Datasheets_stratagems.csv")
            logger.info(f"Loaded {len(relationships_csv)} datasheet-stratagem relationships")
            return relationships_csv
            
        except Exception as e:
            logger.error(f"Failed to load datasheet stratagems: {e}")
            raise WahapediaDataError(f"Cannot load datasheet stratagems: {e}")
    
    def get_detachment_abilities(self) -> List[Dict[str, str]]:
        """
        Get detachment abilities data.
        
        Returns:
            List of detachment ability dictionaries with keys like:
            - id: Unique identifier
            - faction_id: Associated faction
            - name: Ability name
            - detachment: Detachment name
            - detachment_id: Detachment identifier
            - description: Ability description
            
        Raises:
            WahapediaDataError: If detachment data is invalid
        """
        try:
            detachment_csv = self._read_csv_file("Detachment_abilities.csv")
            logger.info(f"Loaded {len(detachment_csv)} detachment abilities")
            return detachment_csv
            
        except Exception as e:
            logger.error(f"Failed to load detachment abilities: {e}")
            raise WahapediaDataError(f"Cannot load detachment abilities: {e}")
    
    def _has_updates(self) -> bool:
        """Check if Wahapedia has any new updates."""
        last_update_path = self.data_dir / "Last_update.csv"
        
        if not last_update_path.exists():
            logger.info("No existing update file found, checking for updates")
            return True
        
        try:
            # Get old update info
            old_update = self._read_csv_file("Last_update.csv")
            old_timestamp = old_update[0]["last_update"] if old_update else ""
            
            # Download fresh update info
            self._update_csv_file("Last_update.csv")
            
            # Get new update info
            new_update = self._read_csv_file("Last_update.csv")
            new_timestamp = new_update[0]["last_update"] if new_update else ""
            
            has_update = old_timestamp != new_timestamp
            if has_update:
                logger.info("Wahapedia has updates available")
            else:
                logger.info("Wahapedia data is up to date")
            
            return has_update
            
        except Exception as e:
            logger.warning(f"Could not check for updates: {e}")
            return True  # Assume updates available on error
    
    def _update_csv_file(self, filename: str) -> bool:
        """
        Update a CSV file if needed.
        
        Args:
            filename: Name of CSV file to update
            
        Returns:
            True if file was updated, False if already current
        """
        file_path = self.data_dir / filename
        
        # Check if file needs updating
        if file_path.exists() and self._is_file_current(filename):
            return False
        
        try:
            logger.info(f"Updating {filename}...")
            
            # Download file
            url = self.base_url + filename
            download_path = self._download_file(url, filename)
            
            # Register in file list
            self._register_file_update(filename)
            
            logger.info(f"Successfully updated {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update {filename}: {e}")
            raise WahapediaDownloadError(f"Cannot update {filename}: {e}")
    
    def _download_file(self, url: str, filename: str) -> Path:
        """Download a file with retry logic and rate limiting."""
        save_path = self.data_dir / filename
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Downloading {filename} (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Save file
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                # Check for rate limiting (small HTML files)
                if save_path.stat().st_size < 2048 and self._is_html_file(save_path):
                    logger.warning(f"Rate limited downloading {filename}, waiting {self.rate_limit_delay}s")
                    save_path.unlink()  # Remove invalid file
                    time.sleep(self.rate_limit_delay)
                    continue
                
                logger.debug(f"Successfully downloaded {filename} ({save_path.stat().st_size} bytes)")
                return save_path
                
            except requests.RequestException as e:
                logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise WahapediaDownloadError(f"Failed to download {filename} after {self.max_retries} attempts")
        
        raise WahapediaDownloadError(f"Failed to download {filename}")
    
    def _is_html_file(self, file_path: Path) -> bool:
        """Check if file is HTML (indicates rate limiting)."""
        try:
            with open(file_path, 'r', encoding='ascii', errors='ignore') as f:
                content = f.read(512)  # Just check first 512 bytes
                return "<!DOCTYPE html>" in content
        except Exception:
            return False
    
    def _read_csv_file(self, filename: str) -> List[Dict[str, str]]:
        """Read and parse CSV file."""
        file_path = self.data_dir / filename
        
        if not file_path.exists():
            raise WahapediaDataError(f"CSV file not found: {filename}")
        
        try:
            results = []
            with open(file_path, 'r', encoding='ascii', errors='ignore') as csvfile:
                reader = csv.DictReader(csvfile, delimiter='|', quoting=csv.QUOTE_NONE)
                for row in reader:
                    # Remove empty keys caused by malformed delimiters
                    clean_row = {k: v for k, v in row.items() if k.strip()}
                    results.append(clean_row)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to read CSV file {filename}: {e}")
            raise WahapediaDataError(f"Cannot parse {filename}: {e}")
    
    def _is_file_current(self, filename: str) -> bool:
        """Check if file is current based on file list tracking."""
        if not self.file_list_path.exists():
            self._create_file_list()
            return False
        
        try:
            with open(self.file_list_path, 'r') as f:
                file_list = json.load(f)
            
            if filename not in file_list:
                return False
            
            # Check if file was updated in last 24 hours
            last_update = datetime.fromisoformat(file_list[filename])
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            return last_update > cutoff_time
            
        except Exception as e:
            logger.warning(f"Could not check file currency for {filename}: {e}")
            return False
    
    def _register_file_update(self, filename: str):
        """Register file update in tracking list."""
        try:
            if self.file_list_path.exists():
                with open(self.file_list_path, 'r') as f:
                    file_list = json.load(f)
            else:
                file_list = {}
            
            file_list[filename] = datetime.now().isoformat()
            
            with open(self.file_list_path, 'w') as f:
                json.dump(file_list, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Could not register file update for {filename}: {e}")
    
    def _create_file_list(self):
        """Create empty file tracking list."""
        try:
            with open(self.file_list_path, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            logger.warning(f"Could not create file list: {e}")