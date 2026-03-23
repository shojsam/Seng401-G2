"""
deck.py — Shared policy deck for GREENWASHED.
The deck is a shared draw pile (not personal hands).
Standard distribution: 11 Exploitative + 6 Sustainable = 17 cards.
Adjust counts to balance your game.
"""
import random
from enum import Enum


class PolicyType(str, Enum):
    SUSTAINABLE = "sustainable"
    EXPLOITATIVE = "exploitative"


class PolicyCard:
    def __init__(self, policy_type: PolicyType, title: str = "", description: str = ""):
        self.policy_type = policy_type
        self.title = title
        self.description = description

    def to_dict(self) -> dict:
        return {
            "policy_type": self.policy_type.value,
            "title": self.title,
            "description": self.description,
        }


# --- Deck creation ---
EXPLOITATIVE_COUNT = 11
SUSTAINABLE_COUNT = 6


def create_deck() -> list[PolicyCard]:
    """Create a fresh policy deck with the standard distribution."""
    deck: list[PolicyCard] = []
    for i in range(EXPLOITATIVE_COUNT):
        deck.append(PolicyCard(PolicyType.EXPLOITATIVE, title=f"Exploit #{i+1}"))
    for i in range(SUSTAINABLE_COUNT):
        deck.append(PolicyCard(PolicyType.SUSTAINABLE, title=f"Sustain #{i+1}"))
    return deck


def shuffle_deck(deck: list[PolicyCard]) -> None:
    """Shuffle a deck in-place."""
    random.shuffle(deck)