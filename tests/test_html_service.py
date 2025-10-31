"""Tests for HtmlService."""
import pytest
from app.services.html_service import HtmlService


class TestHtmlService:
    """Test the HTML generation service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.html_service = HtmlService()

    def test_convert_to_table_empty_list(self):
        """Test table conversion with empty list."""
        result = self.html_service.convert_to_table([])
        assert result == ""

    def test_convert_to_table_single_item(self):
        """Test table conversion with single dictionary."""
        data = [{"phase": "Command", "stratagems": ["Stratagem A"]}]
        result = self.html_service.convert_to_table(data)
        
        assert "table" in result.lower()
        assert "command" in result.lower()
        assert "stratagem a" in result.lower()

    def test_convert_to_stratagem_list_empty(self):
        """Test stratagem list conversion with empty list."""
        result = self.html_service.convert_to_stratagem_list([])
        assert result == ""

    def test_convert_to_stratagem_list_single_stratagem(self):
        """Test stratagem list conversion with single stratagem."""
        stratagem = {
            "name": "Test Stratagem",
            "cp_cost": 1,
            "type": "Battle Tactic Stratagem",
            "legend": "Test legend",
            "description": "Test description"
        }
        
        result = self.html_service.convert_to_stratagem_list([stratagem])
        
        assert "Test Stratagem" in result
        assert "1CP" in result
        assert "Battle Tactic Stratagem" in result
        assert "Test legend" in result
        assert "Test description" in result

    def test_convert_units_to_divs_empty(self):
        """Test units conversion with empty dictionary."""
        result = self.html_service.convert_units_to_divs({})
        assert result == ""

    def test_convert_units_to_divs_with_stratagems(self):
        """Test units conversion with units that have stratagems."""
        units = {
            "Captain": ["Honor the Chapter", "Rapid Fire"],
            "Scouts": ["Forward Deploy"]
        }
        
        result = self.html_service.convert_units_to_divs(units)
        
        assert "Captain" in result
        assert "Honor the Chapter" in result
        assert "Rapid Fire" in result
        assert "Scouts" in result
        assert "Forward Deploy" in result
        assert self.html_service.CSS_UNIT_BLOCK in result

    def test_convert_units_to_divs_no_stratagems(self):
        """Test units conversion with units that have no stratagems."""
        units = {"Servitors": []}
        
        result = self.html_service.convert_units_to_divs(units)
        
        assert "Servitors" in result
        assert "No stratagems" in result
        assert self.html_service.CSS_UNIT_NO_STRAT in result

    def test_get_stratagem_css_class_core(self):
        """Test CSS class selection for core stratagems."""
        css_class = self.html_service._get_stratagem_css_class("Core Stratagem")
        assert css_class == self.html_service.CSS_STRAT_NAME_CS

    def test_get_stratagem_css_class_battle_tactic(self):
        """Test CSS class selection for battle tactic stratagems."""
        css_class = self.html_service._get_stratagem_css_class("Battle Tactic Stratagem")
        expected = f"{self.html_service.CSS_STRAT_NAME_9K} {self.html_service.CSS_STRAT_BATTLE_TACTIC}"
        assert css_class == expected

    def test_get_stratagem_css_class_unknown(self):
        """Test CSS class selection for unknown stratagem types."""
        css_class = self.html_service._get_stratagem_css_class("Unknown Type")
        assert css_class == self.html_service.CSS_STRAT_NAME_WSP

    def test_render_single_stratagem_complete(self):
        """Test rendering a complete stratagem."""
        stratagem = {
            "name": "Honor the Chapter",
            "cp_cost": 2,
            "type": "Epic Deed Stratagem",
            "legend": "Use in the Fight phase",
            "description": "Select one unit to fight twice"
        }
        
        result = self.html_service._render_single_stratagem(stratagem)
        
        assert "Honor the Chapter" in result
        assert "2CP" in result
        assert "Epic Deed Stratagem" in result
        assert "Use in the Fight phase" in result
        assert "Select one unit to fight twice" in result
        assert self.html_service.CSS_STRAT_WRAPPER in result