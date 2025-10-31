"""
Stratagem filtering and validation utilities for BattleScribe parser.
"""

# Constants
OPTION_VALUE_ON = "on"
STRATAGEM_TYPE_CORE_LOWER = "core"


def filter_core_stratagems(empty_stratagems_list, show_core_option):
    """
    Returns a list of core stratagems (type contains 'core', case-insensitive) if show_core_option is 'on', else returns an empty list.
    """
    if show_core_option != OPTION_VALUE_ON:
        return []
    result_list = []
    for empty_stratagem in empty_stratagems_list:
        strat_type = empty_stratagem.get("type", "").lower()
        if STRATAGEM_TYPE_CORE_LOWER in strat_type:
            result_list.append(
                {"datasheet_id": "", "stratagem_id": empty_stratagem["id"]}
            )
    return result_list


def filter_out_core_stratagems(stratagems, get_stratagem_from_id):
    """
    Filters out any stratagem whose type contains 'core' (case-insensitive).
    stratagems: list of dicts with 'stratagem_id' key
    get_stratagem_from_id: function to retrieve stratagem dict by id
    """
    filtered = []
    for s in stratagems:
        strat_id = s.get("stratagem_id")
        strat_type = None
        if strat_id:
            strat = get_stratagem_from_id(strat_id)
            if strat:
                strat_type = strat.get("type", "").lower()
        if not (strat_type and STRATAGEM_TYPE_CORE_LOWER in strat_type):
            filtered.append(s)
    return filtered


def filter_empty_stratagems_by_faction(faction_ids, empty_stratagems_list):
    """
    Filter empty stratagems by faction IDs, matching faction and subfaction IDs.
    
    Args:
        faction_ids: List of faction dictionaries with 'id' and optionally 'parent_id'
        empty_stratagems_list: List of stratagem dictionaries with faction and subfaction info
        
    Returns:
        List of lists: Each inner list contains stratagems for the corresponding faction
    """
    stratagems_list = []

    for faction_id in faction_ids:
        result_list = []

        if faction_id is None:
            stratagems_list.append(result_list)
            continue

        for empty_stratagem in empty_stratagems_list:
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


def filter_core_stratagems_from_list(empty_stratagems_list, show_core_option):
    """
    Extract core stratagems from empty stratagems list based on show_core option.
    
    Args:
        empty_stratagems_list: List of stratagem dictionaries
        show_core_option: String option to show core stratagems ("on" to show, anything else to hide)
        
    Returns:
        List of stratagem references if show_core is "on", empty list otherwise
    """
    if show_core_option != OPTION_VALUE_ON:
        return []
    
    result_list = []
    for empty_stratagem in empty_stratagems_list:
        strat_type = empty_stratagem.get("type", "").lower()
        if STRATAGEM_TYPE_CORE_LOWER in strat_type:
            result_list.append(
                {"datasheet_id": "", "stratagem_id": empty_stratagem["id"]}
            )
    return result_list
