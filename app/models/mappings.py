"""
BattleScribe to Wahapedia mapping dictionaries.

These mappings help standardize unit names and faction names between 
BattleScribe roster files and Wahapedia data.
"""

# Unit name mappings: BattleScribe → Wahapedia
UNIT_RENAME_MAPPINGS = {
    "War Dog Brigand Squadron": "War Dog Brigand",
    "War Dog Executioner Squadron": "War Dog Executioner",
    "War Dog Huntsman Squadron": "War Dog Huntsman",
    "War Dog Karnivore Squadron": "War Dog Karnivore",
    "War Dog Stalker Squadron": "War Dog Stalker",
    "Armiger Helverins": "Armiger Helverin",
    "Armiger Warglaives": "Armiger Warglaive",
    "Knight Moiraxes": "Knight Moirax",
    "Kâhl": "Khl",
    "KÃ¢hl": "Khl",
    "Brôkhyr Thunderkyn w/ bolt cannons": "Brkhyr Thunderkyn",
    "Brôkhyr Thunderkyn w/ graviton blast cannons": "Brkhyr Thunderkyn",
    "Brôkhyr Thunderkyn  w/ SP conversion beamers": "Brkhyr Thunderkyn",
    "BrÃ´khyr Thunderkyn w/ bolt cannons": "Brkhyr Thunderkyn",
    "BrÃ´khyr Thunderkyn w/ graviton blast cannons": "Brkhyr Thunderkyn",
    "BrÃ´khyr Thunderkyn  w/ SP conversion beamers": "Brkhyr Thunderkyn",
    "Hearthguard w/ disintegrators and plasma blade gauntlets": "Einhyr Hearthguard",
    "Hearthguard w/ disintegrators and concussion gauntlets": "Einhyr Hearthguard",
    "Hearthguard w/ plasma guns and concussion gauntlets": "Einhyr Hearthguard",
    "Hearthguard w/ plasma guns and plasma blade gauntlets": "Einhyr Hearthguard",
    "Cthonian Beserks w/ heavy plasma axes": "Cthonian Beserks",
    "Cthonian Beserks w/ concussion mauls": "Cthonian Beserks",
    "Hearthkyn Warriors w/ ion blasters": "Hearthkyn Warriors",
    "Hearthkyn Warriors w/ bolters": "Hearthkyn Warriors",
    "Ûthar the Destined": "thar the Destined",
    "Ã›thar the Destined": "thar the Destined",
    "Brôkhyr Iron-master": "Brkhyr Iron-master",
    "BrÃ´khyr Iron-master": "Brkhyr Iron-master",
    "Chapter Master": "Captain",
    "Chapter Master in Phobos Armour": "Captain in Phobos Armour",
    "Chapter Master in Terminator Armour": "Captain in Terminator Armour",
    "Chapter Master on Bike": "Captain on Bike",
    "Chapter Master with Master-crafted Heavy Bolt Rifle": "Captain with Master-crafted Heavy Bolt Rifle",
    "Primaris Chapter Master": "Primaris Captain",
    "Chapter Master in Gravis Armour": "Captain in Gravis Armour",
}

# Subfaction to main faction mappings: Subfaction → Main Faction
SUBFACTION_RENAME_MAPPINGS = {
    # Adepta Sororitas
    "Order: Our Martyred Lady": "Order of Our Martyred Lady",
    "Order: Argent Shroud": "Order of the Argent Shroud",
    "Order: Bloody Rose": "Order of the Bloody Rose",
    "Order: Ebon Chalice": "Order of the Ebon Chalice",
    "Order: Sacred Rose": "Order of the Sacred Rose",
    "Order: Valorous Heart": "Order of the Valorous Heart",
    # Astra Militarum
    "Death Korps of Krieg": "Astra Militarum",
    "Catachan": "Astra Militarum",
    "Cadian": "Astra Militarum",
    "Tallarn": "Astra Militarum",
    "Vostroyan": "Astra Militarum",
    "Mordian": "Astra Militarum",
    "Armageddon": "Astra Militarum",
    # Space Marines
    "Dark Angels": "Space Marines",
    "Blood Angels": "Space Marines",
    "Space Wolves": "Space Marines",
    "Ultramarines": "Space Marines",
    "Salamanders": "Space Marines",
    "Raven Guard": "Space Marines",
    "White Scars": "Space Marines",
    "Iron Hands": "Space Marines",
    "Imperial Fists": "Space Marines",
    "Black Templars": "Space Marines",
    "Crimson Fists": "Space Marines",
    "Deathwatch": "Space Marines",
    # Chaos Space Marines
    "Alpha Legion": "Chaos Space Marines",
    "Black Legion": "Chaos Space Marines",
    "Iron Warriors": "Chaos Space Marines",
    "Night Lords": "Chaos Space Marines",
    "Word Bearers": "Chaos Space Marines",
    "Red Corsairs": "Chaos Space Marines",
    # Other major factions
    "World Eaters": "World Eaters",
    "Emperor's Children": "Emperors Children",
    "Death Guard": "Death Guard",
    "Thousand Sons": "Thousand Sons",
    # Aeldari
    "Biel-Tan": "Aeldari",
    "Ulthwé": "Aeldari", 
    "Saim-Hann": "Aeldari",
    "Alaitoc": "Aeldari",
    # Drukhari
    "Kabal of the Black Heart": "Drukhari",
    "Wych Cult of Strife": "Drukhari",
    "Haemonculus Coven": "Drukhari",
    # T'au Empire
    "T'au Sept": "T'au Empire",
    "Farsight Enclaves": "T'au Empire",
    # Necrons  
    "Sautekh Dynasty": "Necrons",
    "Mephrit Dynasty": "Necrons",
    # Orks
    "Goffs": "Orks",
    "Evil Sunz": "Orks",
    "Bad Moons": "Orks",
    # Tyranids
    "Hive Fleet Leviathan": "Tyranids",
    "Hive Fleet Behemoth": "Tyranids",
    "Hive Fleet Kraken": "Tyranids",
}

# Non-unit selection types that should be ignored during unit extraction
SELECTION_NON_UNIT_TYPES = [
    "**Chapter Selector**",
    "Game Type", 
    "Detachment Command Cost",
    "Battle Size",
    "Arks of Omen Compulsory Type",
    "Detachment",
    "Show/Hide Options",
]

# Phase names for stratagem organization
PHASES_LIST = [
    "Any time",
    "Before battle", 
    "During deployment",
    "At the start of battle round",
    "Any phase",
    "Any of your phases",
    "At the start of your turn",
    "At the start of enemy turn",
    "Start of any phase",
    "Command phase",
    "Start of the Command phase", 
    "End of the Command phase",
    "Enemy Command phase",
    "Movement phase",
    "Enemy Movement phase",
    "Psychic phase",
    "Enemy Psychic phase", 
    "Shooting phase",
    "Enemy Shooting phase",
    "Charge phase",
    "Enemy Charge phase",
    "Fight phase",
    "Enemy Fight phase",
    "Morale phase",
    "Enemy Morale phase",
]


def standardize_unit_name(unit_name: str) -> str:
    """
    Standardize a BattleScribe unit name to Wahapedia format.
    
    Args:
        unit_name: Raw unit name from BattleScribe
        
    Returns:
        Standardized unit name for Wahapedia matching
    """
    if not unit_name or not isinstance(unit_name, str):
        return unit_name or ""
        
    return UNIT_RENAME_MAPPINGS.get(unit_name, unit_name)


def get_main_faction_name(subfaction_name: str) -> str:
    """
    Get the main faction name from a subfaction name.
    
    Args:
        subfaction_name: Subfaction name from BattleScribe
        
    Returns:
        Main faction name for Wahapedia matching, or original name if no mapping exists
    """
    if not subfaction_name or not isinstance(subfaction_name, str):
        return subfaction_name or ""
        
    return SUBFACTION_RENAME_MAPPINGS.get(subfaction_name, subfaction_name)


def is_unit_selection(selection_name: str) -> bool:
    """
    Check if a selection represents an actual unit (not configuration).
    
    Args:
        selection_name: Name of the BattleScribe selection
        
    Returns:
        True if this represents a unit, False if it's configuration/non-unit
    """
    if not selection_name:
        return False
        
    return selection_name not in SELECTION_NON_UNIT_TYPES