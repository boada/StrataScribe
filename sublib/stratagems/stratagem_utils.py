"""
Stratagem utility functions for BattleScribe parser.
"""


def get_stratagem_type(stratagem, default=""):
    """Safely get the type of a stratagem as lowercase string."""
    return stratagem.get("type", default).lower() if stratagem else default.lower()


def is_core_stratagem(stratagem):
    """Return True if stratagem type contains 'core' (case-insensitive)."""
    return "core" in get_stratagem_type(stratagem)


# Add more stratagem-related helpers here as needed.
