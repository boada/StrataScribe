"""
Faction, detachment, and subfaction detection utilities for BattleScribe parser.
"""


def safe_lower(val):
    """Return val.lower() if val is a string, else ''."""
    return val.lower() if isinstance(val, str) else ""


def match_faction_name(faction_name, candidate_name):
    """Return True if names match (case-insensitive, substring)."""
    f = safe_lower(faction_name)
    c = safe_lower(candidate_name)
    return f in c or c in f


def extract_subfaction_names(roster_elem, subfaction_types):
    """Extract subfaction names from a roster element."""
    subfaction_names = []
    selections = roster_elem.get("selections", {}).get("selection", [])
    if not isinstance(selections, list):
        selections = [selections]
    for selection in selections:
        if selection.get("@name") in subfaction_types:
            nested = selection.get("selections", {}).get("selection", [])
            if not isinstance(nested, list):
                nested = [nested]
            for element in nested:
                name_clean = element.get("@name", "").replace("'", "")
                subfaction_names.append(name_clean)
    return subfaction_names


# Add more helpers for faction/detachment/subfaction logic as needed.
