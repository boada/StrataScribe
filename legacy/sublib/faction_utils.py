"""
Faction, detachment, and subfaction detection utilities for BattleScribe parser.
"""
from typing import Dict, List, Optional, Any, Callable


def safe_lower(val: Any) -> str:
    """Return val.lower() if val is a string, else ''."""
    return val.lower() if isinstance(val, str) else ""


def match_faction_name(faction_name: str, candidate_name: str) -> bool:
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


def get_faction_name(catalogue_name, subfaction_rename_dict, remove_symbol_func):
    """Extract faction name from catalogue name."""
    catalogue_array = remove_symbol_func(catalogue_name.split(" - "), "'")
    faction_name = catalogue_array[-1]

    if catalogue_array[-1] == "Craftworlds":
        faction_name = catalogue_array[0]

    if faction_name in subfaction_rename_dict:
        faction_name = subfaction_rename_dict.get(faction_name)

    return faction_name


def compare_unit_names(wahapedia_name, battlescribe_name, unit_rename_dict):
    """Compare battlescribe and wahapedia names according to rename dictionary."""
    clean_battlescribe_name = battlescribe_name.replace("'", "")
    if clean_battlescribe_name in unit_rename_dict:
        if unit_rename_dict[clean_battlescribe_name] == wahapedia_name:
            return True

    if wahapedia_name == clean_battlescribe_name:
        return True

    return False


def find_faction_from_roster(roster_list, factions_dict, subfaction_types, subfaction_rename_dict, get_faction_name_func):
    """Find faction for each force in the roster."""
    result_faction = []

    for roster_elem in roster_list:
        force_faction = None
        catalogueName = roster_elem["@catalogueName"]
        catalogueName_clean = get_faction_name_func(catalogueName, subfaction_rename_dict, lambda arr, symbol: [word.replace(symbol, "") for word in arr])

        # Try to match catalogue name directly to faction name
        for faction in factions_dict:
            faction_name = safe_lower(faction.get("name", ""))
            cat_name_clean_lower = safe_lower(catalogueName_clean)
            if (
                faction_name in cat_name_clean_lower
                or cat_name_clean_lower in faction_name
            ):
                force_faction = faction
                break

        # If no match yet, try using subfaction logic
        if not force_faction and "selections" in roster_elem:
            subfaction_names = extract_subfaction_names(roster_elem, subfaction_types)

            # Try to match subfaction names to known faction names
            for subfaction_name in subfaction_names:
                subfaction_lookup = subfaction_rename_dict.get(
                    subfaction_name, subfaction_name
                )
                for faction in factions_dict:
                    if match_faction_name(faction.get("name", ""), subfaction_lookup):
                        force_faction = faction
                        break
                if force_faction:
                    break

        if force_faction:
            print(f"Detected faction: {force_faction.get('name', 'Unknown')}")
            result_faction.append(force_faction)
        else:
            print(f"Warning: Could not determine faction for force: {catalogueName_clean}")
            result_faction.append(None)

    return result_faction


def get_subfaction_from_units(units_id, subfaction_rename_dict):
    """
    Attempts to infer the subfaction based on unit keywords by matching them
    (after cleaning) against the keys of `subfaction_rename_dict`.

    Returns:
        str or None: The matched subfaction value if found, otherwise None.
    """
    # print("🔎 Starting subfaction detection...")
    subfaction_lookup = {
        key.lower(): value for key, value in subfaction_rename_dict.items()
    }
    # print(f"📚 subfaction_rename_dict keys: {list(subfaction_lookup.keys())}")

    for unit in units_id:
        keywords = unit.get("keywords", [])
        # print(f"🔍 Unit: {unit.get('name')}, Keywords: {keywords}")
        for keyword in keywords:
            keyword_clean = keyword.lower().replace("faction: ", "").strip()
            if keyword_clean in subfaction_lookup:
                # print(f"✅ Matched keyword '{keyword}' to subfaction '{subfaction_lookup[keyword_clean]}'")
                return subfaction_lookup[keyword_clean]

    # print("❌ No subfaction match found.")
    return None


def find_detachment_from_roster(roster_list, detachment_abilities_dict):
    """
    Attempts to find the detachment used in each force of the roster by inspecting unit keywords.
    
    Returns:
        list of str: List of detected detachments for each force, or None if not found.
    """
    result = []

    # Build a mapping from normalized detachment name to canonical CSV name
    detachment_map = {}
    for entry in detachment_abilities_dict:
        if entry.get("detachment"):
            norm = entry["detachment"].strip().lower().replace(" ", "")
            detachment_map[norm] = entry["detachment"].strip()

    for force in roster_list:
        force_detachment = None
        # 10th ed: force may be a dict, not a list
        if isinstance(force, dict):
            wrappers = force.get("selections", {}).get("selection", [])
            if isinstance(wrappers, dict):
                wrappers = [wrappers]
        elif isinstance(force, list):
            wrappers = force
        else:
            wrappers = []

        for unit in wrappers:
            keywords = unit.get("keywords", [])
            for keyword in keywords:
                # Normalize keyword
                keyword_norm = keyword.strip().lower().replace(" ", "")
                if keyword_norm in detachment_map:
                    force_detachment = detachment_map[keyword_norm]
                    break
            if force_detachment:
                break

        if force_detachment:
            print(f"Detected detachment: {force_detachment}")
        else:
            print("Warning: Could not determine detachment")
        
        result.append(force_detachment)

    return result


# Add more helpers for faction/detachment/subfaction logic as needed.
