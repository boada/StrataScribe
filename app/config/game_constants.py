"""
Warhammer 40k game constants and mappings.

Contains faction mappings, unit renaming dictionaries, phase lists, 
and other game-specific configuration that rarely changes.
"""
from typing import Dict, List

# Subfaction Types
SUBFACTION_TYPES = [
    "Order Convictions",
    "Forge World Choice", 
    "Brotherhood",
    "Noble Household",
    "Chapter",
    "Chaos Allegiance",
    "Dread Household",
    "Legion",
    "Plague Company",
    "Cult of the Legion",
    "Craftworld Selection",
    "Kabal",
    "Wych Cult",
    "Haemonculus Coven",
    "Cult Creed",
    "League",
    "Dynasty Choice",
    "Clan Kultur",
    "Sept Choice",
    "Hive Fleet",
]

# Non-unit selection types (to be filtered out)
SELECTION_NON_UNIT_TYPES = [
    "**Chapter Selector**",
    "Game Type",
    "Detachment Command Cost", 
    "Battle Size",
    "Arks of Omen Compulsory Type",
]

# Game Phase Order
GAME_PHASES = [
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
    "Shooting or Fight phase",
    "Being targeted",
    "Charge phase",
    "Start of the Charge phase",
    "Enemy Charge phase",
    "Fight phase",
    "Start of the Fight phase",
    "Enemy Fight phase",
    "Morale phase",
    "Enemy Morale phase",
    "Taking casualties",
    "Enemy taking casualties",
    "End of your turn",
    "End of enemy turn",
    "End of the turn",
    "End of the phase",
    "End of the battle round",
    "End of the Battle",
    "After enemy unit ends Normal, Advance or Fall Back move",
    "End of any phase",
]

# Valid Stratagem Types
VALID_STRATAGEM_TYPES = [
    "Battle Tactic Stratagem",
    "Strategic Ploy Stratagem", 
    "Epic Deed Stratagem",
    "Requisition Stratagem",
    "Wargear Stratagem",
    "Core Stratagem",
]

# Invalid Stratagem Types (to be filtered out)
INVALID_STRATAGEM_TYPES = [
    "(Supplement)",
    "Crusher Stampede",
    "Crusade", 
    "Fallen Angels",
    "Boarding Actions",
]

# Army of Renown List
ARMY_OF_RENOWN_LIST = [
    "Kill Team Strike Force",
    "Vanguard Spearhead",
    "Mechanicus Defence Cohort",
    "Skitarii Veteran Cohort", 
    "Freeblade Lance",
    "Disciples of Belakor",
    "Terminus Est Assault Force",
    "Warpmeld Pact",
    "Coteries of the Haemonculi",
    "Cult of the Cryptek",
    "Annihilation Legion", 
    "Speed Freeks Speed Mob",
    "Cogs of Vashtorr",
]

# Unit Name Mappings (BattleScribe -> Wahapedia)
UNIT_RENAME_MAPPINGS: Dict[str, str] = {
    # Imperial Knights / Chaos Knights
    "War Dog Brigand Squadron": "War Dog Brigand",
    "War Dog Executioner Squadron": "War Dog Executioner", 
    "War Dog Huntsman Squadron": "War Dog Huntsman",
    "War Dog Karnivore Squadron": "War Dog Karnivore",
    "War Dog Stalker Squadron": "War Dog Stalker",
    "Armiger Helverins": "Armiger Helverin",
    "Armiger Warglaives": "Armiger Warglaive",
    "Knight Moiraxes": "Knight Moirax",
    
    # Leagues of Votann (character encoding issues)
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
    
    # Space Marines
    "Chapter Master": "Captain",
    "Chapter Master in Phobos Armour": "Captain in Phobos Armour",
    "Chapter Master in Terminator Armour": "Captain in Terminator Armour",
    "Chapter Master on Bike": "Captain on Bike", 
    "Chapter Master with Master-crafted Heavy Bolt Rifle": "Captain with Master-crafted Heavy Bolt Rifle",
    "Primaris Chapter Master": "Primaris Captain",
    "Chapter Master in Gravis Armour": "Captain in Gravis Armour",
}

# Subfaction Name Mappings (BattleScribe -> Standard)
SUBFACTION_RENAME_MAPPINGS: Dict[str, str] = {
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
    
    # Other factions
    "World Eaters": "World Eaters",
    "Emperor's Children": "Emperors Children",
    "Death Guard": "Death Guard",
    "Thousand Sons": "Thousand Sons",
    "Genestealer Cults": "Genestealer Cults",
    "Adeptus Mechanicus": "Adeptus Mechanicus",
    "Adeptus Custodes": "Adeptus Custodes",
    "Imperial Knights": "Imperial Knights",
    "Chaos Knights": "Chaos Knights", 
    "T'au Empire": "Tau Empire",
    "T'au": "Tau Empire",
    "Leagues of Votann": "Leagues of Votann",
    "Tyranids": "Tyranids",
    "Necrons": "Necrons",
    "Orks": "Orks",
    "Drukhari": "Drukhari",
    "Aeldari": "Aeldari",
    "Harlequins": "Aeldari", 
    "Ynnari": "Aeldari",
    "Grey Knights": "Grey Knights",
    
    # Special/Misc
    "Inquisition": "Imperial Agents",
    "Officio Assassinorum": "Imperial Agents",
    "Agents of the Imperium": "Imperial Agents",
    "Unaligned": "Unaligned Forces",
    "Adeptus Titanicus": "Adeptus Titanicus",
}