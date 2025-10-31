import string

from json2html import json2html

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

table_attributes = CSS_TABLE_ATTRIBUTES

stratagem_template = (
    f'<div class="{CSS_STRAT_WRAPPER}">'
    '<div class="$stratagem_class"><span>$stratagem_name</span><span>${stratagem_cp_cost}CP</span></div>'
    f'<div class="{CSS_STRAT_FACTION}">$stratagem_type</div>'
    f'<p class="{CSS_STRAT_LEGEND}">$stratagem_legend</p>'
    f'<div class="{CSS_STRAT_TEXT}">$stratagem_description </div>'
    "</div>"
)


# def convert_to_table(json_dict):
#     return json2html.convert(json=json_dict, table_attributes=table_attributes)


def convert_to_table(json_list):
    result_html = ""
    for json_elem in json_list:
        result_html += (
            json2html.convert(json=json_elem, table_attributes=table_attributes) + " "
        )

    return result_html


def convert_to_stratagem_list(json_list):
    """Convert list of stratagem dictionaries to HTML"""
    result_html = ""
    for json_elem in json_list:
        result_html += _render_single_stratagem(json_elem)
    return result_html


def _render_single_stratagem(stratagem_data):
    """Render a single stratagem as HTML"""
    json_template = string.Template(stratagem_template)
    stratagem_class = _get_stratagem_css_class(stratagem_data["type"])
    
    return json_template.substitute(
        stratagem_name=stratagem_data["name"],
        stratagem_cp_cost=stratagem_data["cp_cost"],
        stratagem_class=stratagem_class,
        stratagem_type=stratagem_data["type"],
        stratagem_legend=stratagem_data["legend"],
        stratagem_description=stratagem_data["description"],
    )


def _get_stratagem_css_class(stratagem_type):
    """Determine CSS class based on stratagem type"""
    # Create a mapping for cleaner logic
    type_to_class = {
        STRATAGEM_TYPE_BATTLE_TACTIC: CSS_STRAT_BATTLE_TACTIC,
        STRATAGEM_TYPE_STRATEGIC_PLOY: CSS_STRAT_STRATEGIC_PLOY,
        STRATAGEM_TYPE_EPIC_DEED: CSS_STRAT_EPIC_DEED,
        STRATAGEM_TYPE_REQUISITION: CSS_STRAT_REQUISITION,
        STRATAGEM_TYPE_WARGEAR: CSS_STRAT_WARGEAR,
    }
    
    base_class = CSS_STRAT_NAME_9K
    
    if STRATAGEM_TYPE_CORE in stratagem_type:
        return CSS_STRAT_NAME_CS
    
    for type_key, class_name in type_to_class.items():
        if type_key in stratagem_type:
            return f"{base_class} {class_name}"
    
    return CSS_STRAT_NAME_WSP


# New function: render units and their stratagems as divs for column layout
def convert_units_to_divs(units_dict):
    """
    units_dict: dict mapping unit name to list of stratagem names
    Returns HTML string with each unit as a div, unit name as heading, stratagems as a list.
    """
    html = ""
    for unit, stratagems in units_dict.items():
        html += f'<div class="{CSS_UNIT_BLOCK}">'
        html += f'<div class="{CSS_UNIT_NAME}"><b>{unit}</b></div>'
        if stratagems:
            html += f'<ul class="{CSS_UNIT_STRAT_LIST}">'
            for strat in stratagems:
                html += f"<li>{strat}</li>"
            html += "</ul>"
        else:
            html += f'<div class="{CSS_UNIT_NO_STRAT}"><i>No stratagems</i></div>'
        html += "</div>"
    return html
