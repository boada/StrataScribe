"""
File operations service for BattleScribe roster files.

Handles reading, parsing, and managing .ros and .rosz files with proper
error handling, logging, and integration with our domain models.
"""
import os
import zipfile
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import xmltodict

from app.config import get_config
from app.models.domain import RosterData, FileUploadInfo
from app.models.converters import roster_xml_to_domain


# Set up logger
logger = logging.getLogger(__name__)


class FileServiceError(Exception):
    """Base exception for file service errors."""
    pass


class InvalidRosterFileError(FileServiceError):
    """Raised when roster file is invalid or corrupted."""
    pass


class FileService:
    """
    Service for handling BattleScribe file operations.
    
    Provides methods to read, parse, and manage roster files with proper
    error handling and cleanup.
    """
    
    def __init__(self, config=None):
        """Initialize file service with configuration."""
        self.config = config or get_config()
        self.upload_folder = Path(self.config.UPLOAD_FOLDER)
        self.supported_extensions = self.config.SUPPORTED_EXTENSIONS
        
        # Ensure upload folder exists
        self.upload_folder.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"FileService initialized with upload folder: {self.upload_folder}")
    
    def save_uploaded_file(self, file_storage, filename: str) -> FileUploadInfo:
        """
        Save an uploaded file to the upload directory.
        
        Args:
            file_storage: Flask file storage object
            filename: Target filename to save as
            
        Returns:
            FileUploadInfo with file metadata
            
        Raises:
            FileServiceError: If save operation fails
        """
        try:
            file_path = self.upload_folder / filename
            file_storage.save(str(file_path))
            
            file_info = FileUploadInfo(
                filename=filename,
                original_name=file_storage.filename or filename,
                file_extension=Path(filename).suffix,
                file_size=file_path.stat().st_size if file_path.exists() else None
            )
            
            logger.info(f"Saved uploaded file: {filename} ({file_info.file_size} bytes)")
            return file_info
            
        except Exception as e:
            logger.error(f"Failed to save uploaded file {filename}: {e}")
            raise FileServiceError(f"Failed to save file: {e}")
    
    def read_roster_file(self, filename: str) -> RosterData:
        """
        Read and parse a BattleScribe roster file.
        
        Args:
            filename: Name of the roster file to read
            
        Returns:
            Parsed roster data as domain model
            
        Raises:
            FileServiceError: If file cannot be read or parsed
            InvalidRosterFileError: If file format is invalid
        """
        file_path = self.upload_folder / filename
        
        if not file_path.exists():
            raise FileServiceError(f"Roster file not found: {filename}")
        
        try:
            # Handle .rosz archives
            if filename.endswith('.rosz'):
                return self._read_rosz_archive(file_path)
            
            # Handle .ros files directly
            elif filename.endswith('.ros'):
                return self._read_ros_file(file_path)
            
            else:
                raise InvalidRosterFileError(f"Unsupported file type: {Path(filename).suffix}")
                
        except Exception as e:
            if isinstance(e, (FileServiceError, InvalidRosterFileError)):
                raise
            logger.error(f"Unexpected error reading roster file {filename}: {e}")
            raise FileServiceError(f"Failed to parse roster file: {e}")
    
    def _read_rosz_archive(self, file_path: Path) -> RosterData:
        """Read roster data from .rosz archive file."""
        logger.info(f"Processing .rosz archive: {file_path.name}")
        
        try:
            with zipfile.ZipFile(file_path, "r") as zip_file:
                file_list = zip_file.namelist()
                ros_files = [f for f in file_list if f.endswith(".ros")]
                
                if not ros_files:
                    raise InvalidRosterFileError(f"No .ros file found in archive: {file_path.name}")
                
                # Use the first .ros file found
                ros_file_name = ros_files[0]
                logger.info(f"Extracting roster file: {ros_file_name}")
                
                # Extract to upload folder
                extracted_path = self.upload_folder / ros_file_name
                zip_file.extract(ros_file_name, self.upload_folder)
                
                # Parse the extracted file
                roster_data = self._read_ros_file(extracted_path)
                
                # Clean up extracted file
                try:
                    extracted_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to cleanup extracted file {ros_file_name}: {e}")
                
                return roster_data
                
        except zipfile.BadZipFile:
            raise InvalidRosterFileError(f"Invalid archive file: {file_path.name}")
    
    def _read_ros_file(self, file_path: Path) -> RosterData:
        """Read roster data from .ros XML file."""
        logger.info(f"Parsing .ros file: {file_path.name}")
        
        try:
            if file_path.stat().st_size == 0:
                raise InvalidRosterFileError(f"Empty roster file: {file_path.name}")
            
            with open(file_path, encoding="utf8", errors="replace") as xml_file:
                content = xml_file.read().strip()
                if not content:
                    raise InvalidRosterFileError(f"Roster file contains no data: {file_path.name}")
                
                # Parse XML to dictionary
                xml_dict = xmltodict.parse(content)
                
                # Validate basic structure
                if "roster" not in xml_dict:
                    raise InvalidRosterFileError("Invalid roster structure: missing 'roster' element")
                
                # Convert to domain model
                roster_data = roster_xml_to_domain(xml_dict)
                
                logger.info(f"Successfully parsed roster: {roster_data.name or 'Unnamed'}")
                return roster_data
                
        except (OSError, IOError) as e:
            logger.error(f"File system error reading {file_path.name}: {e}")
            raise FileServiceError(f"Cannot access file: {file_path.name}")
        except Exception as e:
            if isinstance(e, InvalidRosterFileError):
                raise
            logger.error(f"XML parsing error for {file_path.name}: {e}")
            raise InvalidRosterFileError(f"Failed to parse roster XML: {e}")
    
    def cleanup_old_files(self, max_age_hours: Optional[int] = None) -> int:
        """
        Clean up old roster files to prevent disk space issues.
        
        Args:
            max_age_hours: Maximum age in hours (uses config default if None)
            
        Returns:
            Number of files deleted
        """
        max_age = max_age_hours or self.config.FILE_RETENTION_HOURS
        cutoff_time = datetime.now() - timedelta(hours=max_age)
        deleted_count = 0
        
        try:
            for file_path in self.upload_folder.iterdir():
                if not file_path.is_file():
                    continue
                
                # Only clean up roster files
                if file_path.suffix.lower() not in {'.ros', '.rosz'}:
                    continue
                
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_ctime)
                    if file_time < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old roster file: {file_path.name}")
                        
                except Exception as e:
                    logger.warning(f"Could not process file {file_path.name}: {e}")
                    continue
            
            if deleted_count > 0:
                logger.info(f"Cleanup completed: {deleted_count} old files deleted")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during file cleanup: {e}")
            return 0
    
    def validate_file(self, filename: str) -> bool:
        """Validate if a filename has a supported extension."""
        extension = Path(filename).suffix.lower()
        return extension in self.supported_extensions
    
    def get_upload_path(self, filename: str) -> Path:
        """Get the full path for an uploaded file."""
        return self.upload_folder / filename