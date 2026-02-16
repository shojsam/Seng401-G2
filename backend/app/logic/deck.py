import random
from enum import Enum


class PolicyType(str, Enum):
    SUSTAINABLE = "sustainable"
    EXPLOITATIVE = "exploitative"


class PolicyCard:
    def __init__(self, name: str, description: str, policy_type: PolicyType):
        self.name = name
        self.description = description
        self.policy_type = policy_type

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type.value,
        }


# ---------------------------------------------------------------------------
# Card definitions — environment, economics, human rights, democratic freedoms
# ---------------------------------------------------------------------------
POLICY_CARDS: list[dict] = [
    # TODO: add your card content here. Each entry should be a dict with:
    #   "name": str,
    #   "description": str,
    #   "policy_type": "sustainable" or "exploitative"
    #
    # Example:
    # {"name": "Fair Wage Act", "description": "Establish a living wage indexed to cost of living", "policy_type": "sustainable"},
    # {"name": "Austerity for Recovery", "description": "Cut social spending to reduce national debt", "policy_type": "exploitative"},
]


def _build_pool(policy_type: PolicyType) -> list[PolicyCard]:
    """Build a shuffled list of cards for one policy type."""
    cards = [
        PolicyCard(name=c["name"], description=c["description"], policy_type=policy_type)
        for c in POLICY_CARDS
        if c["policy_type"] == policy_type.value
    ]
    random.shuffle(cards)
    return cards


def deal_hands(
    roles: dict[str, str],
    cards_per_player: int = 5,
) -> dict[str, list[PolicyCard]]:
    """Deal cards to each player based on their role.

    Reformers receive sustainable cards, Exploiters receive exploitative cards.
    Returns a mapping of player_id -> list of PolicyCard.
    """
    sustainable_pool = _build_pool(PolicyType.SUSTAINABLE)
    exploitative_pool = _build_pool(PolicyType.EXPLOITATIVE)

    hands: dict[str, list[PolicyCard]] = {}
    for player_id, role in roles.items():
        if role in ("reformer", "REFORMER", "Reformer"):
            pool = sustainable_pool
        else:
            pool = exploitative_pool

        hand: list[PolicyCard] = []
        for _ in range(cards_per_player):
            if pool:
                hand.append(pool.pop())
        hands[player_id] = hand

    return hands
