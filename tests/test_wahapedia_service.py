"""
Tests for Wahapedia service functionality.
"""
import pytest
from unittest.mock import Mock, patch, mock_open
import json
from datetime import datetime, timedelta

from app.services.wahapedia_service import (
    WahapediaService, WahapediaServiceError, WahapediaDownloadError, WahapediaDataError
)
from app.models.domain import Faction, Stratagem
from app.config.settings import TestingConfig


class TestWahapediaService:
    """Test WahapediaService functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = TestingConfig()
        self.service = WahapediaService(self.config)
    
    def test_init_creates_data_directory(self):
        """Test service initialization creates data directory."""
        assert self.service.data_dir.exists()
        assert self.service.config == self.config
        assert self.service.base_url == self.config.WAHAPEDIA_BASE_URL
        assert self.service.csv_files == self.config.WAHAPEDIA_CSV_FILES
    
    def test_initialize_no_updates(self):
        """Test initialization when no updates are needed."""
        with patch.object(self.service, '_has_updates', return_value=False):
            result = self.service.initialize()
            assert result is False
    
    def test_initialize_with_updates(self):
        """Test initialization when updates are needed."""
        with patch.object(self.service, '_has_updates', return_value=True):
            with patch.object(self.service, '_update_csv_file', return_value=True) as mock_update:
                result = self.service.initialize()
                assert result is True
                assert mock_update.call_count == len(self.service.csv_files)
    
    def test_initialize_error_handling(self):
        """Test initialization error handling."""
        with patch.object(self.service, '_has_updates', side_effect=Exception("Network error")):
            with pytest.raises(WahapediaServiceError, match="Initialization failed"):
                self.service.initialize()
    
    @patch.object(WahapediaService, '_read_csv_file')
    def test_get_factions_success(self, mock_read_csv):
        """Test successful faction retrieval."""
        mock_read_csv.return_value = [
            {"id": "1", "name": "Space Marines", "parent_id": ""},
            {"id": "2", "name": "Chaos Space Marines", "parent_id": ""}
        ]
        
        with patch('app.services.wahapedia_service.WahapediaFaction') as mock_faction_class:
            mock_faction = Mock()
            mock_faction_class.from_csv_row.return_value = mock_faction
            
            with patch('app.services.wahapedia_service.wahapedia_faction_to_domain') as mock_converter:
                test_faction = Faction(id="1", name="Space Marines")
                mock_converter.return_value = test_faction
                
                result = self.service.get_factions()
                
                assert len(result) == 2
                assert all(isinstance(f, Faction) for f in result)
    
    def test_get_factions_data_error(self):
        """Test faction retrieval with data error."""
        with patch.object(self.service, '_read_csv_file', side_effect=Exception("CSV error")):
            with pytest.raises(WahapediaDataError, match="Cannot load factions"):
                self.service.get_factions()
    
    @patch.object(WahapediaService, '_read_csv_file')
    def test_get_stratagems_success(self, mock_read_csv):
        """Test successful stratagem retrieval."""
        # In 10th edition, phase information is included directly in Stratagems.csv
        mock_read_csv.return_value = [{"id": "1", "name": "Test Stratagem", "faction_id": "sm", "phase": "Command"}]
        
        with patch('app.services.wahapedia_service.WahapediaStratagem') as mock_strat_class:
            mock_stratagem = Mock()
            mock_stratagem.id = "1"
            mock_stratagem.faction_id = "sm"
            mock_stratagem.phase = "Command"  # Include phase field
            mock_strat_class.from_csv_row.return_value = mock_stratagem
            
            with patch('app.services.wahapedia_service.wahapedia_stratagem_to_domain') as mock_converter:
                test_stratagem = Stratagem(
                    id="1", name="Test Stratagem", type="Battle Tactic",
                    cp_cost=1, description="Test", legend="", phase="Command",
                    faction_id="sm"
                )
                mock_converter.return_value = test_stratagem
                
                result = self.service.get_stratagems()
                
                assert len(result) == 1
                assert isinstance(result[0], Stratagem)
    
    @patch.object(WahapediaService, '_read_csv_file')
    def test_get_stratagems_filtered_by_faction(self, mock_read_csv):
        """Test stratagem retrieval filtered by faction."""
        mock_read_csv.return_value = [
            {"id": "1", "name": "SM Stratagem", "faction_id": "sm", "phase": "Command"},
            {"id": "2", "name": "CSM Stratagem", "faction_id": "csm", "phase": "Shooting"}
        ]
        
        with patch('app.services.wahapedia_service.WahapediaStratagem') as mock_strat_class:
            def create_mock_stratagem(row):
                mock = Mock()
                mock.id = row["id"]
                mock.faction_id = row["faction_id"]
                mock.phase = row.get("phase", "")
                return mock
            
            mock_strat_class.from_csv_row.side_effect = create_mock_stratagem
            
            with patch('app.services.wahapedia_service.wahapedia_stratagem_to_domain') as mock_converter:
                mock_converter.return_value = Mock()
                
                result = self.service.get_stratagems(faction_id="sm")
                
                # Should only get one stratagem (the SM one)
                assert len([call for call in mock_converter.call_args_list]) == 1
    
    def test_has_updates_no_existing_file(self):
        """Test update check when no existing file."""
        last_update_path = self.service.data_dir / "Last_update.csv"
        
        with patch('pathlib.Path.exists', return_value=False):
            result = self.service._has_updates()
            assert result is True
    
    def test_has_updates_different_timestamps(self):
        """Test update check with different timestamps."""
        old_data = [{"last_update": "2023-01-01"}]
        new_data = [{"last_update": "2023-01-02"}]
        
        def read_csv_side_effect(filename):
            if not hasattr(read_csv_side_effect, 'call_count'):
                read_csv_side_effect.call_count = 0
            read_csv_side_effect.call_count += 1
            
            return old_data if read_csv_side_effect.call_count == 1 else new_data
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(self.service, '_read_csv_file', side_effect=read_csv_side_effect):
                with patch.object(self.service, '_update_csv_file'):
                    result = self.service._has_updates()
                    assert result is True
    
    def test_has_updates_same_timestamps(self):
        """Test update check with same timestamps."""
        same_data = [{"last_update": "2023-01-01"}]
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(self.service, '_read_csv_file', return_value=same_data):
                with patch.object(self.service, '_update_csv_file'):
                    result = self.service._has_updates()
                    assert result is False
    
    def test_update_csv_file_already_current(self):
        """Test CSV file update when file is already current."""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(self.service, '_is_file_current', return_value=True):
                result = self.service._update_csv_file("test.csv")
                assert result is False
    
    def test_update_csv_file_needs_update(self):
        """Test CSV file update when file needs updating."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.object(self.service, '_download_file', return_value=Mock()):
                with patch.object(self.service, '_register_file_update'):
                    result = self.service._update_csv_file("test.csv")
                    assert result is True
    
    @patch('app.services.wahapedia_service.requests.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        mock_response = Mock()
        mock_response.content = b"CSV data"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 1024
            with patch.object(self.service, '_is_html_file', return_value=False):
                with patch("builtins.open", mock_open()) as mock_file:
                    
                    result = self.service._download_file("http://test.com/file.csv", "file.csv")
                    
                    assert result == self.service.data_dir / "file.csv"
                    mock_get.assert_called_once()
                    mock_file.assert_called_once()
    
    @patch('app.services.wahapedia_service.requests.get')
    def test_download_file_rate_limited(self, mock_get):
        """Test file download with rate limiting."""
        mock_response = Mock()
        mock_response.content = b"<html>Rate limited</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 100  # Small file indicates rate limiting
            with patch.object(self.service, '_is_html_file', return_value=True):
                with patch('pathlib.Path.unlink'):
                    with patch('time.sleep'):  # Don't actually sleep in tests
                        
                        with pytest.raises(WahapediaDownloadError):
                            self.service._download_file("http://test.com/file.csv", "file.csv")
    
    def test_is_html_file_true(self):
        """Test HTML file detection (rate limiting)."""
        html_content = "<!DOCTYPE html><html><body>Rate limited</body></html>"
        
        with patch("builtins.open", mock_open(read_data=html_content)):
            result = self.service._is_html_file(self.service.data_dir / "test.html")
            assert result is True
    
    def test_is_html_file_false(self):
        """Test non-HTML file detection."""
        csv_content = "id|name|faction\n1|Test|SM"
        
        with patch("builtins.open", mock_open(read_data=csv_content)):
            result = self.service._is_html_file(self.service.data_dir / "test.csv")
            assert result is False
    
    def test_read_csv_file_success(self):
        """Test successful CSV file reading."""
        csv_content = "id|name|faction\n1|Test Stratagem|SM\n2|Another|CSM"
        
        with patch("builtins.open", mock_open(read_data=csv_content)):
            with patch('pathlib.Path.exists', return_value=True):
                result = self.service._read_csv_file("test.csv")
                
                assert len(result) == 2
                assert result[0]["id"] == "1"
                assert result[0]["name"] == "Test Stratagem"
                assert result[1]["faction"] == "CSM"
    
    def test_read_csv_file_not_found(self):
        """Test CSV file reading when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(WahapediaDataError, match="CSV file not found"):
                self.service._read_csv_file("nonexistent.csv")
    
    def test_is_file_current_no_file_list(self):
        """Test file currency check with no file list."""
        with patch('pathlib.Path.exists', return_value=False):
            with patch.object(self.service, '_create_file_list'):
                result = self.service._is_file_current("test.csv")
                assert result is False
    
    def test_is_file_current_recent_file(self):
        """Test file currency check with recent file."""
        recent_time = datetime.now() - timedelta(hours=1)
        file_list = {"test.csv": recent_time.isoformat()}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(file_list))):
                result = self.service._is_file_current("test.csv")
                assert result is True
    
    def test_is_file_current_old_file(self):
        """Test file currency check with old file."""
        old_time = datetime.now() - timedelta(hours=48)
        file_list = {"test.csv": old_time.isoformat()}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(file_list))):
                result = self.service._is_file_current("test.csv")
                assert result is False
    
    def test_register_file_update(self):
        """Test file update registration."""
        existing_list = {"other.csv": "2023-01-01T00:00:00"}
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(existing_list))) as mock_file:
                self.service._register_file_update("test.csv")
                
                # Check that file was written
                mock_file.assert_called()


class TestWahapediaServiceErrors:
    """Test Wahapedia service error handling."""
    
    def test_error_inheritance(self):
        """Test custom exception inheritance."""
        assert issubclass(WahapediaServiceError, Exception)
        assert issubclass(WahapediaDownloadError, WahapediaServiceError)
        assert issubclass(WahapediaDataError, WahapediaServiceError)
    
    def test_error_messages(self):
        """Test error message handling."""
        service_error = WahapediaServiceError("Service error")
        assert str(service_error) == "Service error"
        
        download_error = WahapediaDownloadError("Download failed")
        assert str(download_error) == "Download failed"
        
        data_error = WahapediaDataError("Invalid data")
        assert str(data_error) == "Invalid data"