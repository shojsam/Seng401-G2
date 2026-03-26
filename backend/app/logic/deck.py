"""
deck.py — Shared policy deck for GREENWASHED.
The deck is a shared draw pile (not personal hands).
Cards are loaded from the database (cards table) at deck creation.
Falls back to placeholder cards if the database is unavailable.
"""
import random
from enum import Enum


class PolicyType(str, Enum):
    SUSTAINABLE = "sustainable"
    EXPLOITATIVE = "exploitative"


class PolicyCard:
    def __init__(self, policy_type: PolicyType, title: str = "", description: str = "", hover: str = ""):
        self.policy_type = policy_type
        self.title = title
        self.description = description
        self.hover = hover

    def to_dict(self) -> dict:
        return {
            "policy_type": self.policy_type.value,
            "title": self.title,
            "description": self.description,
            "hover": self.hover,
        }


# --- Deck creation ---
# Fallback counts if DB is unavailable
EXPLOITATIVE_COUNT = 11
SUSTAINABLE_COUNT = 6


def _load_cards_from_db() -> list[PolicyCard] | None:
    """Try to load cards from the database. Returns None on failure."""
    try:
        from ..data.repository import get_all_cards

        rows = get_all_cards()
        if not rows:
            return None

        deck: list[PolicyCard] = []
        for row in rows:
            card_type_str = str(row.get("card_type", "")).lower().strip()
            if card_type_str == "sustainable":
                policy_type = PolicyType.SUSTAINABLE
            elif card_type_str == "exploitative":
                policy_type = PolicyType.EXPLOITATIVE
            else:
                # Skip unknown card types
                continue

            title = str(row.get("card_name", "Policy"))
            description = str(row.get("card_detail", "") or "")
            hover = str(row.get("hover", "") or "")

            deck.append(PolicyCard(policy_type, title=title, description=description, hover=hover))

        if deck:
            return deck
        return None
    except Exception as exc:
        print(f"Could not load cards from database, using fallback: {exc}")
        return None


def _create_fallback_deck() -> list[PolicyCard]:
    """Create a fallback deck with placeholder names."""
    deck: list[PolicyCard] = []
    for i in range(EXPLOITATIVE_COUNT):
        deck.append(PolicyCard(PolicyType.EXPLOITATIVE, title=f"Exploit #{i+1}"))
    for i in range(SUSTAINABLE_COUNT):
        deck.append(PolicyCard(PolicyType.SUSTAINABLE, title=f"Sustain #{i+1}"))
    return deck


def create_deck() -> list[PolicyCard]:
    """Create a fresh policy deck, loading from the database if available."""
    deck = _load_cards_from_db()
    if deck is None:
        deck = _create_fallback_deck()
    return deck


def shuffle_deck(deck: list[PolicyCard]) -> None:
    """Shuffle a deck in-place."""
    random.shuffle(deck)