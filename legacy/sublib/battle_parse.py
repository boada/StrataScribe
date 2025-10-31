import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any

from lxml import html

from sublib import wahapedia_db, wh40k_lists
from sublib.stratagems.stratagem_filters import (
    filter_core_stratagems,
    filter_out_core_stratagems,
    filter_empty_stratagems_by_faction,
    filter_core_stratagems_from_list,
)
from sublib.stratagems.stratagem_utils import clean_html, clean_full_stratagem, remove_symbol, get_bracket_text, get_first_letters
from sublib.faction_utils import (
    safe_lower, get_faction_name, compare_unit_names, 
    find_faction_from_roster, get_subfaction_from_units, find_detachment_from_roster
)
from sublib.file_utils import read_ros_file, get_dict_from_xml, delete_old_files

# File Extensions
FILE_EXT_ROSZ = ".rosz"

# CSV File Names
CSV_DATASHEETS = "Datasheets.csv"
CSV_DATASHEETS_STRATAGEMS = "Datasheets_stratagems.csv"
CSV_DETACHMENT_ABILITIES = "Detachment_abilities.csv"
CSV_FACTIONS = "Factions.csv"
CSV_STRATAGEMS = "Stratagems.csv"

# Request Option Keys
OPTION_SHOW_CORE = "show_core"
OPTION_SHOW_EMPTY = "show_empty"
OPTION_SHOW_UNITS = "show_units"
OPTION_DONT_SHOW_RENOWN = "dont_show_renown"
OPTION_DONT_SHOW_BEFORE = "dont_show_before"

# Common Values
OPTION_VALUE_ON = "on"
PHASE_BEFORE_BATTLE = "Before battle"
STRATAGEM_TYPE_CORE_LOWER = "core"

# Absolute path of the battlescribe folder
battlescribe_folder = os.path.abspath("./battlescribe")

# Global dictionaries to store the data read from csv files
_ros_dict = {}
_datasheets_dict = {}
_datasheets_stratagems_dict = {}
_factions_dict = {}
_stratagem_phases_dict = {}
_stratagems_dict = {}

# Global lists to store the data extracted from the battlescribe file
_roster_list = []
_empty_stratagems_list = []
_full_stratagems_list = []

# WebUI options dictionary
_request_options = {}


def init_parse() -> None:
    """
    Initialize the parse by reading all csv files to dictionary format and creating the battlescribe folder if it does not exist.
    """
    global _datasheets_dict, _datasheets_stratagems_dict, _factions_dict, _stratagem_phases_dict, _stratagems_dict, _detachment_abilities_dict
    # reading all csv file to dictionary format
    _datasheets_dict = wahapedia_db.get_dict_from_csv(CSV_DATASHEETS)
    _datasheets_stratagems_dict = wahapedia_db.get_dict_from_csv(CSV_DATASHEETS_STRATAGEMS)
    _detachment_abilities_dict = wahapedia_db.get_dict_from_csv(CSV_DETACHMENT_ABILITIES)
    _factions_dict = wahapedia_db.get_dict_from_csv(CSV_FACTIONS)
    # _stratagem_phases_dict = wahapedia_db.get_dict_from_csv("StratagemPhases.csv")
    _stratagem_phases_dict = wahapedia_db.get_dict_from_csv(CSV_STRATAGEMS)
    _stratagems_dict = wahapedia_db.get_dict_from_csv(CSV_STRATAGEMS)
    _fix_stratagem_dict()

    # folder for battlescribe files should exist
    if not os.path.exists(battlescribe_folder):
        os.mkdir(battlescribe_folder)

    # filtering all stratagems which doesn't have any unit requirements
    _find_empty_stratagems()


# request_options are coming from Web UI and has several options
def parse_battlescribe(battlescribe_file_name: str, request_options: Dict[str, str]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parse the battlescribe file and returns the result in the form of three lists:
    
    Args:
        battlescribe_file_name: Name of the .ros or .rosz file to parse
        request_options: Dictionary of options from the web UI (show_core, show_empty, etc.)
    
    Returns:
        Tuple containing:
        - List of phase dictionaries (stratagems organized by game phase)
        - List of unit dictionaries (stratagems organized by unit)
        - List of all stratagem dictionaries
    """
    _initialize_parsing(request_options)
    
    # Parse roster structure
    _read_ros_file_wrapper(battlescribe_file_name)
    _prepare_roster_list()
    
    # Extract basic roster data
    wh_faction = _find_faction()
    wh_detachment = _find_detachment()
    wh_units = _find_units(wh_faction)
    
    # Collect stratagems from various sources
    stratagems_data = _collect_all_stratagems(wh_faction, wh_units)
    
    # Process each force and generate results
    result_phase, result_units = _process_forces(wh_faction, wh_units, stratagems_data)
    
    # Clean up and finalize
    delete_old_files(battlescribe_folder)
    result_phase_sorted = _sort_phases_by_game_order(result_phase)
    
    total_stratagems = len(_get_full_stratagems_list())
    phase_count = sum(len(phases) for phases in result_phase_sorted)
    print(f"Report generated: {total_stratagems} stratagems across {phase_count} phases")

    return result_phase_sorted, result_units, _get_full_stratagems_list()


def _initialize_parsing(request_options: Dict[str, str]) -> None:
    """Initialize parsing state and load data."""
    global _full_stratagems_list, _request_options

    if wahapedia_db.init_db() is True:
        init_parse()

    wh40k_lists.clean_list()
    _full_stratagems_list = []
    _request_options = request_options

    if _request_options.get(OPTION_DONT_SHOW_BEFORE) == OPTION_VALUE_ON:
        wh40k_lists.ignore_phases_list.append(PHASE_BEFORE_BATTLE)


def _collect_all_stratagems(wh_faction, wh_units):
    """Collect stratagems from all sources based on request options"""
    print("Processing roster configuration...")
    
    stratagems_data = {
        'empty': [],
        'core': [],
        'army_of_renown': [],
        'unit_specific': []
    }

    if _request_options.get(OPTION_DONT_SHOW_RENOWN) != OPTION_VALUE_ON:
        stratagems_data['army_of_renown'] = _find_army_of_renown()

    if _request_options.get(OPTION_SHOW_EMPTY) == OPTION_VALUE_ON:
        stratagems_data['empty'] = _filter_empty_stratagems(wh_faction)

    stratagems_data['core'] = filter_core_stratagems(
        _empty_stratagems_list, _request_options.get(OPTION_SHOW_CORE)
    )
    
    stratagems_data['unit_specific'] = _find_stratagems(wh_units)
    
    return stratagems_data


def _process_forces(wh_faction, wh_units, stratagems_data):
    """Process each force and generate phase/unit results"""
    result_phase = []
    result_units = []

    for id in range(0, len(wh_faction)):
        current_empty_stratagems = []
        if len(stratagems_data['empty']) != 0:
            current_empty_stratagems = stratagems_data['empty'][id]

        if len(stratagems_data['army_of_renown']) != 0:
            wh40k_lists.current_army_of_renown = stratagems_data['army_of_renown'][id]

        # Combine all sources
        all_selected_stratagems = (
            stratagems_data['unit_specific'][id] + 
            current_empty_stratagems + 
            stratagems_data['core']
        )
        
        # Filter out core stratagems if not requested
        if _request_options.get(OPTION_SHOW_CORE) != OPTION_VALUE_ON:
            all_selected_stratagems = filter_out_core_stratagems(
                all_selected_stratagems, _get_stratagem_from_id
            )

        print(f"Processing {len(all_selected_stratagems)} stratagems for force {id + 1}")

        current_id_phase = _prepare_stratagems_phase(
            all_selected_stratagems, wh_units[id], wh_faction[id]
        )
        currend_id_units = _prepare_stratagems_units(
            all_selected_stratagems, wh_units[id], wh_faction[id]
        )
        result_phase.append(current_id_phase)
        result_units.append(currend_id_units)
    
    return result_phase, result_units


def _sort_phases_by_game_order(result_phase):
    """Sort phase results according to game phase order"""
    result_phase_sorted = []
    for phase_elem in result_phase:
        phase_elem_sorted = {
            i: phase_elem[i]
            for i in sorted(phase_elem, key=lambda j: wh40k_lists.phases_list.index(j))
        }
        result_phase_sorted.append(phase_elem_sorted)
    return result_phase_sorted


def _get_full_stratagems_list():
    global _full_stratagems_list
    sorted_stratagems_list = list(_full_stratagems_list)
    sorted_stratagems_list.sort()

    full_list = []
    for stratagem_id in sorted_stratagems_list:
        clean_stratagem = clean_full_stratagem(
            _get_stratagem_from_id(stratagem_id, clean_stratagem=True)
        )
        full_list.append(clean_stratagem)

    return full_list





def _read_ros_file_wrapper(file_name: str) -> None:
    """Wrapper to maintain global state while using new file utilities."""
    global _ros_dict
    _ros_dict = read_ros_file(file_name, battlescribe_folder)


# if roster has several forces, that it is multidetachment army and _roster_list has more elements
def _prepare_roster_list() -> None:
    """Extract forces from roster data into the global roster list."""
    global _ros_dict, _roster_list
    _roster_list = []
    if isinstance(_ros_dict["roster"]["forces"]["force"], list):
        for roster_force in _ros_dict["roster"]["forces"]["force"]:
            _roster_list.append(roster_force)
    else:
        _roster_list.append(_ros_dict["roster"]["forces"]["force"])


def _find_faction() -> List[Optional[Dict[str, Any]]]:
    """Find faction information for each force in the roster."""
    return find_faction_from_roster(
        _roster_list, 
        _factions_dict, 
        wh40k_lists.subfaction_types,
        wh40k_lists.subfaction_rename_dict,
        get_faction_name
    )


def _find_detachment() -> List[Optional[str]]:
    """
    Attempts to find the detachment used in each force of the roster by inspecting unit keywords.
    Detachment names are loaded from Detachment_abilities.csv.

    Returns:
        List of detected detachments for each force, or None if not found.
    """

    result = []

    # Build a mapping from normalized detachment name to canonical CSV name
    detachment_map = {}
    for entry in _detachment_abilities_dict:
        if entry.get("detachment"):
            norm = entry["detachment"].strip().lower().replace(" ", "")
            detachment_map[norm] = entry["detachment"].strip()

    for force in _roster_list:
        force_detachment = None
        # 10th ed: force may be a dict, not a list
        if isinstance(force, dict):
            wrappers = force.get("selections", {}).get("selection", [])
            if isinstance(wrappers, dict):
                wrappers = [wrappers]
        elif isinstance(force, list):
            wrappers = force
        else:
            print(f"Warning: Unrecognized army structure in roster file")
            wrappers = []

        # Look for a selection with name 'Detachment'
        for wrapper in wrappers:
            if not isinstance(wrapper, dict):
                continue
            # Check both 'name' and '@name' keys for robustness
            wrapper_name = wrapper.get("name") or wrapper.get("@name") or ""
            if wrapper_name.lower() == "detachment":
                detachment_selections = wrapper.get("selections", {}).get(
                    "selection", []
                )
                if isinstance(detachment_selections, dict):
                    detachment_selections = [detachment_selections]
                for det_sel in detachment_selections:
                    # Check both 'name' and '@name' for the detachment name
                    det_name_raw = det_sel.get("name") or det_sel.get("@name") or ""
                    det_name_raw = det_name_raw.strip()
                    det_name_norm = det_name_raw.lower().replace(" ", "")
                    if det_name_norm in detachment_map:
                        force_detachment = detachment_map[det_name_norm]
                        break
                if force_detachment:
                    break
        # Fallback: legacy logic (if above fails)
        if not force_detachment:
            for wrapper in wrappers:
                unit = None
                if isinstance(wrapper, dict):
                    for key in ("selection", "rule", "category", "selections"):
                        if key in wrapper:
                            unit = wrapper[key]
                            break
                    if unit is None:
                        unit = wrapper
                else:
                    continue
                if not isinstance(unit, dict):
                    continue
                for category in unit.get("categories", []):
                    if isinstance(category, dict) and "name" in category:
                        cat_name_norm = (
                            category["name"].strip().lower().replace(" ", "")
                        )
                        if cat_name_norm in detachment_map:
                            force_detachment = detachment_map[cat_name_norm]
                            break
                if force_detachment:
                    break
        if force_detachment:
            print(f"Using detachment: {force_detachment}")
        result.append(force_detachment)

    return result


def _find_army_of_renown() -> List[Optional[str]]:
    """Find army of renown information for each force in the roster."""
    result_army_of_renown = []
    army_of_renown_name = None
    for roster_elem in _roster_list:
        for selection in roster_elem["selections"]["selection"]:
            if "Army of Renown" == selection["@name"]:
                army_of_renown_name = selection["selections"]["selection"][
                    "@name"
                ].replace("'", "")
                break
            elif "Army of Renown" in selection["@name"]:
                army_of_renown_name = selection["@name"].replace("'", "")[17:]
                break

        result_army_of_renown.append(army_of_renown_name)
    return result_army_of_renown


def _find_units(faction_ids):
    total_units = []

    for id in range(0, len(faction_ids)):
        result_units = []
        faction_id = faction_ids[id]
        roster_force = _roster_list[id]

        # ✅ Skip if faction_id is None (from _find_faction fallback)
        if faction_id is None:
            total_units.append(result_units)
            continue

        if roster_force.get("selections") is not None:
            for unit in roster_force["selections"]["selection"]:
                if unit["@name"] not in wh40k_lists.selection_non_unit_types:
                    for datasheet in _datasheets_dict:
                        if (
                            faction_id["id"] == datasheet["faction_id"]
                            or faction_id.get("parent_id") == datasheet["faction_id"]
                        ):
                            if _compare_unit_names(datasheet["name"], unit["@name"]):
                                if datasheet not in result_units:
                                    result_units.append(datasheet)

        total_units.append(result_units)

    return total_units


def _find_empty_stratagems():
    global _empty_stratagems_list
    empty_stratagems_full_list = []
    for stratagem in _stratagems_dict:
        stratagem_found = False
        stratagem_id = stratagem["id"]
        if _stratagem_is_valid(stratagem_id):
            for datasheet_stratagem in _datasheets_stratagems_dict:
                if stratagem_id == datasheet_stratagem["stratagem_id"]:
                    stratagem_found = True
                    break

            if not stratagem_found:
                empty_stratagems_full_list.append(stratagem)

    _empty_stratagems_list = empty_stratagems_full_list


def _filter_empty_stratagems(faction_ids: List[Optional[Dict[str, Any]]]) -> List[List[Dict[str, str]]]:
    """Filter empty stratagems by faction IDs."""
    return filter_empty_stratagems_by_faction(faction_ids, _empty_stratagems_list)


def _filter_core_stratagems() -> List[Dict[str, str]]:
    """Filter core stratagems based on request options."""
    return filter_core_stratagems_from_list(_empty_stratagems_list, _request_options.get(OPTION_SHOW_CORE))


def _find_stratagems(units_ids):
    stratagems_list = []
    for units_id in units_ids:
        result_stratagems = []
        for unit_id in units_id:
            for datasheets_stratagem in _datasheets_stratagems_dict:
                if datasheets_stratagem["datasheet_id"] == unit_id["id"]:
                    result_stratagems.append(datasheets_stratagem)
        stratagems_list.append(result_stratagems)

    return stratagems_list


def _normalize_phases(phases):
    """
    Normalizes a list of stratagem phase names by splitting combined phases
    (e.g., "Shooting or Fight phase") into individual valid phase names
    present in `phases_list`.

    Args:
        phases (List[str]): List of raw phase strings from stratagem data.

    Returns:
        List[str]: Flattened list of individual, valid phase names.
    """
    if isinstance(phases, str):
        phases = [phases]
    normalized = []
    for phase in phases:
        parts = phase.split(" or ")
        for part in parts:
            part = part.strip()
            if part in wh40k_lists.phases_list:
                normalized.append(part)
    return normalized


def _prepare_stratagems_phase(stratagems_id, units_id, faction_id):
    """
    Organizes stratagems by their associated game phases for a given subfaction.

    Filters out stratagems that are not linked to any of the provided units based on
    the Datasheets_stratagems.csv mapping.

    Args:
        stratagems_id (list): List of dictionaries with `stratagem_id` and `datasheet_id`.
        units_id (list): List of unit dictionaries containing `id` and `name`.
        faction_id (dict): Dictionary representing the selected faction with at least an `id`.

    Returns:
        dict: A mapping of phase names to lists of stratagem names that are valid for that phase.
    """
    global _full_stratagems_list
    result_stratagems_phase = {}

    # Get the user's detachment(s) as a set of lowercased names and IDs
    user_detachments = set()
    if hasattr(_find_detachment, "__call__"):
        detected = _find_detachment()
        if isinstance(detected, list):
            for d in detected:
                if d:
                    user_detachments.add(str(d).lower().strip())
    # Also collect detachment IDs from Detachment_abilities.csv
    detachment_name_to_id = {
        entry["detachment"].lower().strip(): entry["detachment_id"]
        for entry in _detachment_abilities_dict
        if entry.get("detachment") and entry.get("detachment_id")
    }
    user_detachment_ids = set()
    for d in user_detachments:
        if d in detachment_name_to_id:
            user_detachment_ids.add(detachment_name_to_id[d])

    for strat_entry in stratagems_id:
        strat_id = strat_entry["stratagem_id"]
        datasheet_id = strat_entry["datasheet_id"]

        # ❌ Skip if this stratagem isn't linked to this datasheet
        found = False
        for entry in _datasheets_stratagems_dict:
            if (
                entry.get("datasheet_id") == datasheet_id
                and entry.get("stratagem_id") == strat_id
            ):
                found = True
                break
        if not found:
            continue

        if not _stratagem_is_valid(strat_id):
            continue

        for stratagem_phase in _stratagem_phases_dict:
            if stratagem_phase["id"] != strat_id:
                continue

            # print(f"[DEBUG] stratagem_phase dict for id={strat_id}: {stratagem_phase}")
            full_stratagem = _get_stratagem_from_id(strat_id, stratagems_id, units_id)
            if full_stratagem is None:
                continue

            # ✅ Detachment filtering
            strat_detachment = (full_stratagem.get("detachment") or "").lower().strip()
            strat_detachment_id = (full_stratagem.get("detachment_id") or "").strip()
            # Only include if detachment matches or is empty (generic stratagem)
            if strat_detachment or strat_detachment_id:
                if not (
                    (strat_detachment and strat_detachment in user_detachments)
                    or (
                        strat_detachment_id
                        and strat_detachment_id in user_detachment_ids
                    )
                ):
                    continue

            # Subfaction filtering (legacy)
            subfaction_id = full_stratagem.get("subfaction_id", "")
            current_subfaction_id = _get_subfaction_from_units(units_id)
            if subfaction_id and subfaction_id != current_subfaction_id:
                continue

            phases = _normalize_phases(stratagem_phase["phase"])
            for phase in phases:
                if phase not in result_stratagems_phase:
                    result_stratagems_phase[phase] = [full_stratagem["name"]]
                else:
                    if full_stratagem["name"] not in result_stratagems_phase[phase]:
                        result_stratagems_phase[phase].append(full_stratagem["name"])

            if full_stratagem["id"] not in _full_stratagems_list:
                _full_stratagems_list.append(full_stratagem["id"])

    return result_stratagems_phase


def _prepare_stratagems_units(stratagems_id, units_id, faction_id):
    """
    Organizes stratagems by the units they apply to, based on datasheet IDs.

    Only includes stratagems that are either generic (no subfaction_id) or explicitly match
    the current user's subfaction.

    Args:
        stratagems_id (list): List of dictionaries with `stratagem_id` and `datasheet_id`.
        units_id (list): List of unit dictionaries containing `id` and `name`.
        faction_id (dict): Dictionary representing the selected subfaction with at least an `id`.

    Returns:
        dict: A mapping of unit names to lists of stratagem names that apply to them.
    """
    global _full_stratagems_list
    results_stratagems_units = {}

    for unit_id in units_id:
        unit_id_name = unit_id["name"]
        if _request_options.get("show_units") == "on":
            unit_id_name = f"[{units_id.index(unit_id) + 1}] {unit_id_name}"
        results_stratagems_units[unit_id_name] = []

    # Get the user's detachment(s) as a set of lowercased names and IDs
    user_detachments = set()
    if hasattr(_find_detachment, "__call__"):
        detected = _find_detachment()
        if isinstance(detected, list):
            for d in detected:
                if d:
                    user_detachments.add(str(d).lower().strip())
    detachment_name_to_id = {
        entry["detachment"].lower().strip(): entry["detachment_id"]
        for entry in _detachment_abilities_dict
        if entry.get("detachment") and entry.get("detachment_id")
    }
    user_detachment_ids = set()
    for d in user_detachments:
        if d in detachment_name_to_id:
            user_detachment_ids.add(detachment_name_to_id[d])

    for stratagem_id in stratagems_id:
        if _stratagem_is_valid(stratagem_id["stratagem_id"]):
            for unit_id in units_id:
                if stratagem_id["datasheet_id"] == unit_id["id"]:
                    full_stratagem = _get_stratagem_from_id(
                        stratagem_id["stratagem_id"]
                    )
                    if full_stratagem is None:
                        continue

                    # Detachment filtering
                    strat_detachment = (
                        (full_stratagem.get("detachment") or "").lower().strip()
                    )
                    strat_detachment_id = (
                        full_stratagem.get("detachment_id") or ""
                    ).strip()
                    if strat_detachment or strat_detachment_id:
                        if not (
                            (strat_detachment and strat_detachment in user_detachments)
                            or (
                                strat_detachment_id
                                and strat_detachment_id in user_detachment_ids
                            )
                        ):
                            continue

                    subfaction_id = full_stratagem.get("subfaction_id", "")
                    current_subfaction_id = _get_subfaction_from_units(units_id)
                    # Only accept stratagems that are either generic or match subfaction
                    if subfaction_id == "" or subfaction_id == current_subfaction_id:
                        unit_id_name = unit_id["name"]
                        if _request_options.get("show_units") == "on":
                            unit_id_name = (
                                f"[{units_id.index(unit_id) + 1}] {unit_id_name}"
                            )

                        results_stratagems_units[unit_id_name].append(
                            full_stratagem["name"]
                        )

                        if full_stratagem["id"] not in _full_stratagems_list:
                            _full_stratagems_list.append(full_stratagem["id"])

    return results_stratagems_units


def _get_stratagem_from_id(
    stratagem_id, stratagems_list=None, units_list=None, clean_stratagem=None
):
    for stratagem in _stratagems_dict:
        if stratagem["id"] == stratagem_id:
            if _request_options is not None and clean_stratagem is not True:
                if (
                    _request_options.get("show_units") == "on"
                    and units_list is not None
                ):
                    result_stratagem = dict(stratagem)
                    if stratagems_list is not None:
                        for stratagem_elem in stratagems_list:
                            if stratagem_elem["stratagem_id"] == stratagem_id:
                                for unit_elem in units_list:
                                    if (
                                        unit_elem["id"]
                                        == stratagem_elem["datasheet_id"]
                                    ):
                                        result_stratagem["name"] += (
                                            "["
                                            + str(units_list.index(unit_elem) + 1)
                                            + "]"
                                        )
                    return result_stratagem
                elif _request_options.get("show_phases") == "on" and units_list is None:
                    result_stratagem = dict(stratagem)
                    for stratagem_phase in _stratagem_phases_dict:
                        # if stratagem_phase["stratagem_id"] == stratagem_id:
                        if stratagem_phase["id"] == stratagem_id:

                            result_stratagem["name"] += (
                                " ["
                                + get_first_letters(stratagem_phase["phase"])
                                + "]"
                            )
                    return result_stratagem

            return stratagem
    return None


def _stratagem_is_valid(stratagem_id):
    full_stratagem = _get_stratagem_from_id(stratagem_id)
    if full_stratagem is None:
        return False
    stratagem_type = full_stratagem["type"]
    # filtering by invalid stratagem type
    for invalid_stratagem_type in wh40k_lists.invalid_stratagems_type:
        if invalid_stratagem_type in stratagem_type:
            return False

    # filtering army of renown stratagems (including current army of renown)
    if _request_options.get("dont_show_renown") != "on":
        if (
            wh40k_lists.current_army_of_renown != ""
            and wh40k_lists.current_army_of_renown is not None
        ):
            if wh40k_lists.current_army_of_renown in stratagem_type:
                return True
        for army_of_renown_name in wh40k_lists.army_of_renown_list:
            if army_of_renown_name in stratagem_type:
                return False

    # if some phases are ignored
    if _get_stratagem_phase(stratagem_id) in wh40k_lists.ignore_phases_list:
        return False

    # filtering by valid stratagem types
    if stratagem_type != "Stratagem":
        for valid_stratagem_type in wh40k_lists.valid_stratagems_type:
            if valid_stratagem_type in stratagem_type:
                return True

    return False


def _get_stratagem_phase(stratagem_id):
    for stratagem_phase in _stratagem_phases_dict:
        # if stratagem_phase["stratagem_id"] == stratagem_id:
        if stratagem_phase["id"] == stratagem_id:
            return stratagem_phase["phase"]


def _get_faction_name(catalogue_name: str) -> Optional[str]:
    """Extract faction name from catalogue name."""
    return get_faction_name(catalogue_name, wh40k_lists.subfaction_rename_dict, remove_symbol)


def _get_subfaction_from_units(units_id: List[Dict[str, Any]]) -> Optional[str]:
    """Get subfaction from unit keywords."""
    return get_subfaction_from_units(units_id, wh40k_lists.subfaction_rename_dict)


# some fix for current (february 2023) csv
def _fix_stratagem_dict():
    global _stratagems_dict
    for stratagem_csv in _stratagems_dict:
        # fix for Aeldari
        if stratagem_csv["faction_id"] == "AE":
            stratagem_type_brackets = get_bracket_text(stratagem_csv["type"])
            if stratagem_type_brackets == "Alaitoc":
                stratagem_csv["subfaction_id"] = "CWAL"
            elif stratagem_type_brackets == "Altansar":
                stratagem_csv["subfaction_id"] = "CWAR"
            elif stratagem_type_brackets == "Biel-Tan":
                stratagem_csv["subfaction_id"] = "CWBT"
            elif stratagem_type_brackets == "Harlequins":
                stratagem_csv["subfaction_id"] = "CWHA"
            elif stratagem_type_brackets == "Iyanden":
                stratagem_csv["subfaction_id"] = "CWIY"
            elif stratagem_type_brackets == "Saim-Hann":
                stratagem_csv["subfaction_id"] = "CWSH"
            elif stratagem_type_brackets == "Ulthw":
                stratagem_csv["subfaction_id"] = "CWUL"
        # fix for Orks
        if stratagem_csv["faction_id"] == "ORK":
            if stratagem_csv["name"] == "UNBRIDLED CARNAGE":
                stratagem_csv["subfaction_id"] = "CLGF"
            elif stratagem_csv["name"] == "DED SNEAKY":
                stratagem_csv["subfaction_id"] = "CLBA"
        # fix for SM
        if stratagem_csv["faction_id"] == "SM":
            if stratagem_csv["name"] == "HONOURED BY MACRAGGE":
                stratagem_csv["subfaction_id"] = "CHUL"
            elif stratagem_csv["name"] == "GIFT OF THE KHANS":
                stratagem_csv["subfaction_id"] = "CHWS"
            elif stratagem_csv["name"] == "BEQUEATHED BY THE IRON COUNCIL":
                stratagem_csv["subfaction_id"] = "CHIH"


# compares battlescribe and wahapedia names according to rename dictionary
def _compare_unit_names(wahapedia_name: str, battlescribe_name: str) -> bool:
    """Compare unit names using the rename dictionary."""
    return compare_unit_names(wahapedia_name, battlescribe_name, wh40k_lists.unit_rename_dict)

