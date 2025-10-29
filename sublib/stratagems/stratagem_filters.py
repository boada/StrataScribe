"""
Stratagem filtering and validation utilities for BattleScribe parser.
"""


def filter_core_stratagems(empty_stratagems_list, show_core_option):
    """
    Returns a list of core stratagems (type contains 'core', case-insensitive) if show_core_option is 'on', else returns an empty list.
    """
    if show_core_option != "on":
        return []
    result_list = []
    for empty_stratagem in empty_stratagems_list:
        strat_type = empty_stratagem.get("type", "").lower()
        if "core" in strat_type:
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
        if not (strat_type and "core" in strat_type):
            filtered.append(s)
    return filtered
