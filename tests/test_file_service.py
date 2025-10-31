"""
Tests for file service functionality.
"""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import zipfile
import tempfile

from app.services.file_service import (
    FileService, FileServiceError, InvalidRosterFileError
)
from app.models.domain import RosterData
from app.models.external import FileUploadInfo
from app.config.settings import TestingConfig


class TestFileService:
    """Test FileService functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestingConfig()
        self.service = FileService(self.config)
    
    def test_init_creates_upload_directory(self):
        """Test that service initialization creates upload directory."""
        assert self.service.upload_folder.exists()
        assert self.service.config == self.config
        assert self.service.supported_extensions == self.config.SUPPORTED_EXTENSIONS
    
    def test_validate_file_supported_extensions(self):
        """Test file validation with supported extensions."""
        assert self.service.validate_file("roster.ros") is True
        assert self.service.validate_file("roster.rosz") is True
        assert self.service.validate_file("roster.txt") is False
        assert self.service.validate_file("roster.pdf") is False
    
    def test_get_upload_path(self):
        """Test upload path generation."""
        filename = "test.ros"
        expected_path = self.service.upload_folder / filename
        assert self.service.get_upload_path(filename) == expected_path
    
    def test_save_uploaded_file_success(self):
        """Test successful file upload."""
        mock_file = Mock()
        mock_file.filename = "original.ros"
        mock_file.save = Mock()
        
        filename = "saved.ros"
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1024
            
            result = self.service.save_uploaded_file(mock_file, filename)
            
            assert isinstance(result, FileUploadInfo)
            assert result.filename == filename
            assert result.original_name == "original.ros"
            assert result.file_extension == ".ros"
            assert result.file_size == 1024
    
    def test_save_uploaded_file_error(self):
        """Test file upload error handling."""
        mock_file = Mock()
        mock_file.save.side_effect = Exception("Save failed")
        
        with pytest.raises(FileServiceError, match="Failed to save file"):
            self.service.save_uploaded_file(mock_file, "test.ros")
    
    def test_read_roster_file_not_found(self):
        """Test reading non-existent file."""
        with pytest.raises(FileServiceError, match="Roster file not found"):
            self.service.read_roster_file("nonexistent.ros")
    
    def test_read_roster_file_unsupported_format(self):
        """Test reading unsupported file format."""
        # Create a fake file
        test_file = self.service.upload_folder / "test.txt"
        test_file.touch()
        
        with pytest.raises(InvalidRosterFileError, match="Unsupported file type"):
            self.service.read_roster_file("test.txt")
    
    @patch('app.services.file_service.xmltodict.parse')
    @patch('app.services.file_service.roster_xml_to_domain')
    def test_read_ros_file_success(self, mock_converter, mock_xmltodict):
        """Test successful .ros file reading."""
        # Setup mocks
        mock_xmltodict.return_value = {"roster": {"@name": "Test Roster"}}
        mock_converter.return_value = RosterData(name="Test Roster")
        
        # Create test file
        test_file = self.service.upload_folder / "test.ros"
        test_content = '<?xml version="1.0"?><roster name="Test">content</roster>'
        
        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = len(test_content)
                with patch('pathlib.Path.exists', return_value=True):
                    
                    result = self.service.read_roster_file("test.ros")
                    
                    assert isinstance(result, RosterData)
                    assert result.name == "Test Roster"
                    mock_xmltodict.assert_called_once()
                    mock_converter.assert_called_once()
    
    def test_read_ros_file_empty(self):
        """Test reading empty .ros file."""
        test_file = self.service.upload_folder / "empty.ros"
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 0
            with patch('pathlib.Path.exists', return_value=True):
                
                with pytest.raises(InvalidRosterFileError, match="Empty roster file"):
                    self.service.read_roster_file("empty.ros")
    
    def test_read_ros_file_invalid_xml(self):
        """Test reading .ros file with invalid XML."""
        test_content = "not xml content"
        
        with patch("builtins.open", mock_open(read_data=test_content)):
            with patch('pathlib.Path.stat') as mock_stat:
                mock_stat.return_value.st_size = len(test_content)
                with patch('pathlib.Path.exists', return_value=True):
                    with patch('app.services.file_service.xmltodict.parse', side_effect=Exception("Parse error")):
                        
                        with pytest.raises(InvalidRosterFileError, match="Failed to parse roster XML"):
                            self.service.read_roster_file("invalid.ros")
    
    @patch('app.services.file_service.zipfile.ZipFile')
    def test_read_rosz_archive_success(self, mock_zipfile):
        """Test successful .rosz archive reading."""
        # Setup mock zipfile
        mock_zip = Mock()
        mock_zip.namelist.return_value = ["roster.ros", "other.txt"]
        mock_zip.extract = Mock()
        mock_zipfile.return_value.__enter__ = Mock(return_value=mock_zip)
        mock_zipfile.return_value.__exit__ = Mock(return_value=None)
        
        # Mock the extracted file reading
        mock_roster_data = RosterData(name="Test Roster")
        
        with patch.object(self.service, '_read_ros_file', return_value=mock_roster_data):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.unlink'):  # Mock cleanup
                    
                    result = self.service.read_roster_file("test.rosz")
                    
                    assert isinstance(result, RosterData)
                    assert result.name == "Test Roster"
                    mock_zip.extract.assert_called_once_with("roster.ros", self.service.upload_folder)
    
    @patch('app.services.file_service.zipfile.ZipFile')
    def test_read_rosz_no_ros_file(self, mock_zipfile):
        """Test .rosz archive with no .ros file."""
        mock_zip = Mock()
        mock_zip.namelist.return_value = ["other.txt", "readme.md"]
        mock_zipfile.return_value.__enter__ = Mock(return_value=mock_zip)
        mock_zipfile.return_value.__exit__ = Mock(return_value=None)
        
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(InvalidRosterFileError, match="No .ros file found in archive"):
                self.service.read_roster_file("test.rosz")
    
    def test_cleanup_old_files(self):
        """Test cleaning up old roster files."""
        from datetime import datetime, timedelta
        
        old_time = datetime.now() - timedelta(hours=48)  # 2 days old
        new_time = datetime.now() - timedelta(hours=1)   # 1 hour old
        
        # Mock the entire cleanup process using pathlib.Path
        with patch('pathlib.Path.iterdir') as mock_iterdir:
            # Create mock file objects
            mock_old_file = Mock()
            mock_old_file.name = "old.ros"
            mock_old_file.is_file.return_value = True
            mock_old_file.suffix = ".ros"
            mock_old_file.unlink = Mock()
            
            mock_new_file = Mock()
            mock_new_file.name = "new.rosz"
            mock_new_file.is_file.return_value = True
            mock_new_file.suffix = ".rosz"
            
            mock_other_file = Mock()
            mock_other_file.name = "other.txt"
            mock_other_file.is_file.return_value = True
            mock_other_file.suffix = ".txt"
            
            mock_iterdir.return_value = [mock_old_file, mock_new_file, mock_other_file]
            
            # Mock stat and fromtimestamp
            mock_old_stat = Mock()
            mock_old_stat.st_ctime = old_time.timestamp()
            mock_old_file.stat.return_value = mock_old_stat
            
            mock_new_stat = Mock()
            mock_new_stat.st_ctime = new_time.timestamp()
            mock_new_file.stat.return_value = mock_new_stat
            
            mock_other_stat = Mock()
            mock_other_stat.st_ctime = new_time.timestamp()
            mock_other_file.stat.return_value = mock_other_stat
            
            with patch('datetime.datetime') as mock_datetime_class:
                mock_datetime_class.now.return_value = datetime.now()
                mock_datetime_class.fromtimestamp.side_effect = datetime.fromtimestamp
                
                deleted_count = self.service.cleanup_old_files(max_age_hours=24)
                
                # Should delete the old .ros file
                assert deleted_count >= 0
                mock_old_file.unlink.assert_called_once()
    
    def test_cleanup_old_files_with_config_default(self):
        """Test cleanup using config default retention time."""
        # Mock empty directory using pathlib.Path.iterdir
        with patch('pathlib.Path.iterdir', return_value=[]):
            deleted_count = self.service.cleanup_old_files()
            assert deleted_count == 0


class TestFileServiceErrors:
    """Test file service error handling."""
    
    def test_file_service_error_inheritance(self):
        """Test custom exception inheritance."""
        assert issubclass(FileServiceError, Exception)
        assert issubclass(InvalidRosterFileError, FileServiceError)
    
    def test_error_messages(self):
        """Test error message handling."""
        error = FileServiceError("Test error")
        assert str(error) == "Test error"
        
        invalid_error = InvalidRosterFileError("Invalid file")
        assert str(invalid_error) == "Invalid file"