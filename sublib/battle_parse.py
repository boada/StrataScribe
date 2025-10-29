import os
import pathlib
import zipfile

from bs4 import BeautifulSoup, Tag
from datetime import datetime, timedelta

import xmltodict
from lxml import html

from sublib import wahapedia_db, wh40k_lists
from sublib.stratagems.stratagem_filters import (
    filter_core_stratagems,
    filter_out_core_stratagems,
)
from sublib.faction_utils import safe_lower

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


def init_parse():
    """
    Initialize the parse by reading all csv files to dictionary format and creating the battlescribe folder if it does not exist
    """
    global _datasheets_dict, _datasheets_stratagems_dict, _factions_dict, _stratagem_phases_dict, _stratagems_dict, _detachment_abilities_dict
    # reading all csv file to dictionary format
    _datasheets_dict = wahapedia_db.get_dict_from_csv("Datasheets.csv")
    _datasheets_stratagems_dict = wahapedia_db.get_dict_from_csv(
        "Datasheets_stratagems.csv"
    )
    _detachment_abilities_dict = wahapedia_db.get_dict_from_csv(
        "Detachment_abilities.csv"
    )
    _factions_dict = wahapedia_db.get_dict_from_csv("Factions.csv")
    # _stratagem_phases_dict = wahapedia_db.get_dict_from_csv("StratagemPhases.csv")
    _stratagem_phases_dict = wahapedia_db.get_dict_from_csv("Stratagems.csv")
    _stratagems_dict = wahapedia_db.get_dict_from_csv("Stratagems.csv")
    _fix_stratagem_dict()

    # folder for battlescribe files should exist
    if not os.path.exists(battlescribe_folder):
        os.mkdir(battlescribe_folder)

    # filtering all stratagems which doesn't have any unit requirements
    _find_empty_stratagems()


# request_options are coming from Web UI and has several options
def parse_battlescribe(battlescribe_file_name, request_options):
    """
    Parse the battlescribe file and returns the result in the form of a list of dictionaries and a list of lists
    """
    global _full_stratagems_list, _request_options

    if wahapedia_db.init_db() is True:
        init_parse()

    wh40k_lists.clean_list()
    _full_stratagems_list = []
    wh_empty_stratagems = []
    wh_core_stratagems = []
    wh_army_of_renown = []

    _request_options = request_options

    _read_ros_file(battlescribe_file_name)
    _prepare_roster_list()

    wh_faction = _find_faction()
    wh_detachment = _find_detachment()
    wh_units = _find_units(wh_faction)

    if _request_options.get("dont_show_renown") != "on":
        wh_army_of_renown = _find_army_of_renown()

    if _request_options.get("show_empty") == "on":
        wh_empty_stratagems = _filter_empty_stratagems(wh_faction)

    print(f"[DEBUG] show_core option: {_request_options.get('show_core')}")
    print("[DEBUG] About to call filter_core_stratagems")
    wh_core_stratagems = filter_core_stratagems(
        _empty_stratagems_list, _request_options.get("show_core")
    )

    if _request_options.get("dont_show_before") == "on":
        wh40k_lists.ignore_phases_list.append("Before battle")

    wh_stratagems = _find_stratagems(wh_units)

    result_phase = []
    result_units = []

    for id in range(0, len(wh_faction)):
        current_empty_stratagems = []
        if len(wh_empty_stratagems) != 0:
            current_empty_stratagems = wh_empty_stratagems[id]

        if len(wh_army_of_renown) != 0:
            wh40k_lists.current_army_of_renown = wh_army_of_renown[id]

        # Combine all sources
        all_selected_stratagems = (
            wh_stratagems[id] + current_empty_stratagems + wh_core_stratagems
        )
        # If show_core is not on, filter out any stratagem whose type contains 'core' (case-insensitive)
        if _request_options.get("show_core") != "on":
            all_selected_stratagems = filter_out_core_stratagems(
                all_selected_stratagems, _get_stratagem_from_id
            )

        print(f"[DEBUG] all_selected_stratagems[{id}]:")
        for s in all_selected_stratagems:
            print(
                f"  - stratagem_id: {s.get('stratagem_id', '?')}, datasheet_id: {s.get('datasheet_id', '?')}"
            )

        current_id_phase = _prepare_stratagems_phase(
            all_selected_stratagems, wh_units[id], wh_faction[id]
        )
        currend_id_units = _prepare_stratagems_units(
            all_selected_stratagems, wh_units[id], wh_faction[id]
        )
        result_phase.append(current_id_phase)
        result_units.append(currend_id_units)

    _delete_old_files()

    result_phase_sorted = []
    for phase_elem in result_phase:
        phase_elem_sorted = {
            i: phase_elem[i]
            for i in sorted(phase_elem, key=lambda j: wh40k_lists.phases_list.index(j))
        }
        result_phase_sorted.append(phase_elem_sorted)

    return result_phase_sorted, result_units, _get_full_stratagems_list()


def _get_full_stratagems_list():
    global _full_stratagems_list
    sorted_stratagems_list = list(_full_stratagems_list)
    sorted_stratagems_list.sort()

    full_list = []
    for stratagem_id in sorted_stratagems_list:
        clean_stratagem = _clean_full_stratagem(
            _get_stratagem_from_id(stratagem_id, clean_stratagem=True)
        )
        full_list.append(clean_stratagem)

    return full_list


def _clean_full_stratagem(stratagem_dict):
    result_stratagem = dict(stratagem_dict)
    result_stratagem.pop("source_id", None)
    result_stratagem.pop("", None)
    result_stratagem["description"] = _clean_html(result_stratagem["description"])

    return result_stratagem


def _read_ros_file(file_name):
    global _ros_dict
    ros_file_name = file_name
    file_path = os.path.join(battlescribe_folder, file_name)
    if pathlib.Path(file_path).suffix == ".rosz":
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            rosz_packed_filename = zip_ref.infolist()[0].filename
            battlescribe_tmp = os.path.join(battlescribe_folder, "tmp")
            ros_file_name = file_name[:-1]

            zip_ref.extractall(battlescribe_tmp)
            ros_file_path = os.path.join(battlescribe_folder, ros_file_name)
            if os.path.exists(ros_file_path):
                os.remove(ros_file_path)
            os.rename(
                os.path.join(battlescribe_tmp, rosz_packed_filename), ros_file_path
            )

    _ros_dict = _get_dict_from_xml(ros_file_name)


# if roster has several forces, that it is multidetachment army and _roster_list has more elements
def _prepare_roster_list():
    global _ros_dict, _roster_list
    _roster_list = []
    if isinstance(_ros_dict["roster"]["forces"]["force"], list):
        for roster_force in _ros_dict["roster"]["forces"]["force"]:
            _roster_list.append(roster_force)
    else:
        _roster_list.append(_ros_dict["roster"]["forces"]["force"])


def _find_faction():
    result_faction = []

    for roster_elem in _roster_list:
        force_faction = None
        catalogueName = roster_elem["@catalogueName"]
        catalogueName_clean = _get_faction_name(catalogueName)

        print("[DEBUG] Cleaned Faction Name:", catalogueName_clean)

        # Try to match catalogue name directly to faction name
        for faction in _factions_dict:
            faction_name = safe_lower(faction.get("name", ""))
            cat_name_clean_lower = safe_lower(catalogueName_clean)
            if (
                faction_name in cat_name_clean_lower
                or cat_name_clean_lower in faction_name
            ):
                print("[DEBUG] Matched main faction:", faction)
                force_faction = faction
                break

        # If no match yet, try using subfaction logic
        if not force_faction and "selections" in roster_elem:
            from sublib.faction_utils import (
                extract_subfaction_names,
                match_faction_name,
            )

            subfaction_names = extract_subfaction_names(
                roster_elem, wh40k_lists.subfaction_types
            )

            # Try to match subfaction names to known faction names
            for subfaction_name in subfaction_names:
                subfaction_lookup = wh40k_lists.subfaction_rename_dict.get(
                    subfaction_name, subfaction_name
                )
                for faction in _factions_dict:
                    if match_faction_name(faction.get("name", ""), subfaction_lookup):
                        print("[DEBUG] Matched subfaction:", faction)
                        force_faction = faction
                        break
                if force_faction:
                    break

        if force_faction:
            result_faction.append(force_faction)
        else:
            print(
                f"[WARNING] Could not determine faction for force: {catalogueName_clean}"
            )
            result_faction.append(None)

    return result_faction


def _find_detachment():
    """
    Attempts to find the detachment used in each force of the roster by inspecting unit keywords.
    Detachment names are loaded from Detachment_abilities.csv.

    Returns:
        list of str: List of detected detachments for each force, or None if not found.
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
            print(f"[ERROR] Unexpected force type: {type(force)} value: {force}")
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
                    print(
                        f"[DETECT] Found detachment candidate: '{det_name_raw}' (norm: '{det_name_norm}')"
                    )
                    if det_name_norm in detachment_map:
                        print(
                            f"[MATCH] Detachment matched: {detachment_map[det_name_norm]}"
                        )
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
        result.append(force_detachment)

    print(f"🧭 Detachments found: {result}")
    return result


def _find_army_of_renown():
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


def _filter_empty_stratagems(faction_ids):
    global _empty_stratagems_list
    stratagems_list = []

    for faction_id in faction_ids:
        result_list = []

        if faction_id is None:
            stratagems_list.append(result_list)
            continue

        for empty_stratagem in _empty_stratagems_list:
            empty_subfaction_id = empty_stratagem.get("subfaction_id", "")
            empty_faction_id = empty_stratagem.get("faction_id", "")

            if (
                faction_id["id"] == empty_subfaction_id
                or faction_id["id"] == empty_faction_id
                or faction_id.get("parent_id") == empty_faction_id
            ):
                result_list.append(
                    {"datasheet_id": "", "stratagem_id": empty_stratagem["id"]}
                )

        stratagems_list.append(result_list)

    return stratagems_list


def _filter_core_stratagems():
    print("[DEBUG] _filter_core_stratagems called")
    if not _request_options.get("show_core") == "on":
        return []
    result_list = []
    for empty_stratagem in _empty_stratagems_list:
        strat_type = empty_stratagem["type"].lower()
        if "core" in strat_type:
            result_list.append(
                {"datasheet_id": "", "stratagem_id": empty_stratagem["id"]}
            )
    return result_list


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
    print(f"[DEBUG] wh40k_lists.phases_list: {wh40k_lists.phases_list}")
    if isinstance(phases, str):
        phases = [phases]
    normalized = []
    for phase in phases:
        print(f"[DEBUG] _normalize_phases input: '{phase}'")
        parts = phase.split(" or ")
        for part in parts:
            part = part.strip()
            if part in wh40k_lists.phases_list:
                print(f"[DEBUG] Phase '{part}' matched in phases_list")
                normalized.append(part)
            else:
                print(f"[DEBUG] Phase '{part}' NOT matched in phases_list")
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
            print(
                f"[DEBUG] Stratagem {full_stratagem['name']} (id={strat_id}) phases extracted: {phases}"
            )
            for phase in phases:
                if phase not in result_stratagems_phase:
                    result_stratagems_phase[phase] = [full_stratagem["name"]]
                else:
                    if full_stratagem["name"] not in result_stratagems_phase[phase]:
                        result_stratagems_phase[phase].append(full_stratagem["name"])

            if full_stratagem["id"] not in _full_stratagems_list:
                _full_stratagems_list.append(full_stratagem["id"])

    print(f"[DEBUG] result_stratagems_phase: {result_stratagems_phase}")

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
                                + _get_first_letters(stratagem_phase["phase"])
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


def _get_faction_name(catalogue_name):
    catalogue_array = _remove_symbol(catalogue_name.split(" - "), "'")
    faction_name = catalogue_array[-1]

    if catalogue_array[-1] == "Craftworlds":
        faction_name = catalogue_array[0]

    if faction_name in wh40k_lists.subfaction_rename_dict:
        faction_name = wh40k_lists.subfaction_rename_dict.get(faction_name)

    return faction_name


def _get_subfaction_from_units(units_id):
    """
    Attempts to infer the subfaction based on unit keywords by matching them
    (after cleaning) against the keys of `subfaction_rename_dict`.

    Returns:
        str or None: The matched subfaction value if found, otherwise None.
    """
    # print("🔎 Starting subfaction detection...")
    subfaction_lookup = {
        key.lower(): value for key, value in wh40k_lists.subfaction_rename_dict.items()
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


# some fix for current (february 2023) csv
def _fix_stratagem_dict():
    global _stratagems_dict
    for stratagem_csv in _stratagems_dict:
        # fix for Aeldari
        if stratagem_csv["faction_id"] == "AE":
            stratagem_type_brackets = _get_bracket_text(stratagem_csv["type"])
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
def _compare_unit_names(wahapedia_name, battlescribe_name):
    clean_battlescribe_name = battlescribe_name.replace("'", "")
    if clean_battlescribe_name in wh40k_lists.unit_rename_dict:
        if wh40k_lists.unit_rename_dict[clean_battlescribe_name] == wahapedia_name:
            return True

    if wahapedia_name == clean_battlescribe_name:
        return True

    return False


# --- NON-Stratagem stuff ---
def _get_first_letters(line):
    words = line.split()
    letters = [word[0] for word in words]
    return "".join(letters)


def _clean_html(html_str):
    ignore_tags = ["a", "span"]
    soup = BeautifulSoup(html_str, "html.parser")

    for tag in ignore_tags:
        for el in soup.find_all(tag):
            if isinstance(el, Tag):
                el.unwrap()

    return str(soup)


def _delete_old_files():
    file_list = os.listdir(battlescribe_folder)
    for single_file in file_list:
        single_file_path = os.path.join(battlescribe_folder, single_file)
        creation_time = datetime.fromtimestamp(os.path.getctime(single_file_path))
        file_time_delta = datetime.now() - creation_time
        if file_time_delta > timedelta(hours=1):
            try:
                os.remove(single_file_path)
                print(single_file + " deleted")
            except:
                print("Can't delete " + single_file)


def _get_dict_from_xml(xml_file_name):
    xml_file_path = os.path.join(battlescribe_folder, xml_file_name)
    with open(xml_file_path, errors="ignore") as xml_file:
        data_dict = xmltodict.parse(xml_file.read())
        return data_dict


def _remove_symbol(arr, symbol):
    return [word.replace(symbol, "") for word in arr]


def _get_bracket_text(string):
    start_index = string.find("(")
    end_index = string.find(")")
    if start_index == -1 or end_index == -1:
        return None
    return string[start_index + 1 : end_index]
