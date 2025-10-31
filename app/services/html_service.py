"""
HTML generation service for StrataScribe.

Converts domain data into HTML for template rendering.
This replaces the legacy prepare_html module with proper service architecture.
"""
import string
from typing import List, Dict, Any
from json2html import json2html


class HtmlService:
    """Service for generating HTML content from domain data."""
    
    # CSS Classes
    CSS_TABLE_ATTRIBUTES = 'class="table table-bordered table-striped w-auto print-friendly"; '
    CSS_STRAT_WRAPPER = "stratWrapper_CS BreakInsideAvoid"
    CSS_STRAT_FACTION = "stratFaction_CS"
    CSS_STRAT_LEGEND = "ShowFluff stratLegend2"
    CSS_STRAT_TEXT = "stratText_CS"
    CSS_STRAT_NAME_9K = "stratName_9k"
    CSS_STRAT_NAME_CS = "stratName_CS"
    CSS_STRAT_NAME_WSP = "stratName_WSP"
    CSS_STRAT_BATTLE_TACTIC = "stratBattleTactic"
    CSS_STRAT_STRATEGIC_PLOY = "stratStrategicPloy"
    CSS_STRAT_EPIC_DEED = "stratEpicDeed"
    CSS_STRAT_REQUISITION = "stratRequisition"
    CSS_STRAT_WARGEAR = "stratWargear"
    CSS_UNIT_BLOCK = "unitBlock_CS"
    CSS_UNIT_NAME = "unitName_CS"
    CSS_UNIT_STRAT_LIST = "unitStratList_CS"
    CSS_UNIT_NO_STRAT = "unitNoStrat_CS"

    # Stratagem Types
    STRATAGEM_TYPE_BATTLE_TACTIC = "Battle Tactic Stratagem"
    STRATAGEM_TYPE_STRATEGIC_PLOY = "Strategic Ploy Stratagem"
    STRATAGEM_TYPE_EPIC_DEED = "Epic Deed Stratagem"
    STRATAGEM_TYPE_REQUISITION = "Requisition Stratagem"
    STRATAGEM_TYPE_WARGEAR = "Wargear Stratagem"
    STRATAGEM_TYPE_CORE = "Core Stratagem"

    def __init__(self):
        """Initialize HTML service."""
        self.stratagem_template = (
            f'<div class="{self.CSS_STRAT_WRAPPER}">'
            '<div class="$stratagem_class"><span>$stratagem_name</span><span>${stratagem_cp_cost}CP</span></div>'
            f'<div class="{self.CSS_STRAT_FACTION}">$stratagem_type</div>'
            f'<p class="{self.CSS_STRAT_LEGEND}">$stratagem_legend</p>'
            f'<div class="{self.CSS_STRAT_TEXT}">$stratagem_description </div>'
            "</div>"
        )

    def convert_to_table(self, json_list: List[Dict[str, Any]]) -> str:
        """Convert list of dictionaries to HTML table format."""
        result_html = ""
        for json_elem in json_list:
            result_html += (
                json2html.convert(json=json_elem, table_attributes=self.CSS_TABLE_ATTRIBUTES) + " "
            )
        return result_html

    def convert_to_stratagem_list(self, stratagem_dicts: List[Dict[str, Any]]) -> str:
        """Convert list of stratagem dictionaries to HTML."""
        result_html = ""
        for stratagem_data in stratagem_dicts:
            result_html += self._render_single_stratagem(stratagem_data)
        return result_html

    def convert_units_to_divs(self, units_dict: Dict[str, List[str]]) -> str:
        """
        Convert units dictionary to HTML divs.
        
        Args:
            units_dict: Dictionary mapping unit name to list of stratagem names
            
        Returns:
            HTML string with each unit as a div
        """
        html = ""
        for unit, stratagems in units_dict.items():
            html += f'<div class="{self.CSS_UNIT_BLOCK}">'
            html += f'<div class="{self.CSS_UNIT_NAME}"><b>{unit}</b></div>'
            if stratagems:
                html += f'<ul class="{self.CSS_UNIT_STRAT_LIST}">'
                for strat in stratagems:
                    html += f"<li>{strat}</li>"
                html += "</ul>"
            else:
                html += f'<div class="{self.CSS_UNIT_NO_STRAT}"><i>No stratagems</i></div>'
            html += "</div>"
        return html

    def _render_single_stratagem(self, stratagem_data: Dict[str, Any]) -> str:
        """Render a single stratagem as HTML."""
        json_template = string.Template(self.stratagem_template)
        stratagem_class = self._get_stratagem_css_class(stratagem_data["type"])
        
        return json_template.substitute(
            stratagem_name=stratagem_data["name"],
            stratagem_cp_cost=stratagem_data["cp_cost"],
            stratagem_class=stratagem_class,
            stratagem_type=stratagem_data["type"],
            stratagem_legend=stratagem_data["legend"],
            stratagem_description=stratagem_data["description"],
        )

    def _get_stratagem_css_class(self, stratagem_type: str) -> str:
        """Determine CSS class based on stratagem type."""
        type_to_class = {
            self.STRATAGEM_TYPE_BATTLE_TACTIC: self.CSS_STRAT_BATTLE_TACTIC,
            self.STRATAGEM_TYPE_STRATEGIC_PLOY: self.CSS_STRAT_STRATEGIC_PLOY,
            self.STRATAGEM_TYPE_EPIC_DEED: self.CSS_STRAT_EPIC_DEED,
            self.STRATAGEM_TYPE_REQUISITION: self.CSS_STRAT_REQUISITION,
            self.STRATAGEM_TYPE_WARGEAR: self.CSS_STRAT_WARGEAR,
        }
        
        base_class = self.CSS_STRAT_NAME_9K
        
        if self.STRATAGEM_TYPE_CORE in stratagem_type:
            return self.CSS_STRAT_NAME_CS
        
        for type_key, class_name in type_to_class.items():
            if type_key in stratagem_type:
                return f"{base_class} {class_name}"
        
        return self.CSS_STRAT_NAME_WSP