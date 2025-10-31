"""
Stratagem utility functions for BattleScribe parser.
"""
from bs4 import BeautifulSoup, Tag


def get_stratagem_type(stratagem, default=""):
    """Safely get the type of a stratagem as lowercase string."""
    return stratagem.get("type", default).lower() if stratagem else default.lower()


def is_core_stratagem(stratagem):
    """Return True if stratagem type contains 'core' (case-insensitive)."""
    return "core" in get_stratagem_type(stratagem)


def clean_html(html_str):
    """Remove unwanted HTML tags while preserving content."""
    ignore_tags = ["a", "span"]
    soup = BeautifulSoup(html_str, "html.parser")

    for tag in ignore_tags:
        for el in soup.find_all(tag):
            if isinstance(el, Tag):
                el.unwrap()

    return str(soup)


def clean_full_stratagem(stratagem_dict):
    """Clean and format a stratagem dictionary by removing unwanted fields and cleaning HTML."""
    result_stratagem = dict(stratagem_dict)
    result_stratagem.pop("source_id", None)
    result_stratagem.pop("", None)
    result_stratagem["description"] = clean_html(result_stratagem["description"])

    return result_stratagem


def remove_symbol(arr, symbol):
    """Remove a specific symbol from all strings in an array."""
    return [word.replace(symbol, "") for word in arr]


def get_bracket_text(string):
    """Extract text between parentheses from a string. Returns None if no parentheses found."""
    start_index = string.find("(")
    end_index = string.find(")")
    if start_index == -1 or end_index == -1:
        return None
    return string[start_index + 1 : end_index]


def get_first_letters(line):
    """Extract the first letter from each word in a string and join them."""
    words = line.split()
    letters = [word[0] for word in words]
    return "".join(letters)


# Add more stratagem-related helpers here as needed.
