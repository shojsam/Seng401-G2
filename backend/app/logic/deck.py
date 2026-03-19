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


# Default card definitions used by the game engine.
# The runtime can re-deal from these templates as needed so larger lobbies
# still receive full hands.
POLICY_CARDS: list[dict] = [
    {
        "name": "Renewable Grid Expansion",
        "description": "Fund a rapid build-out of public renewable energy and transmission infrastructure.",
        "policy_type": "sustainable",
    },
    {
        "name": "Clean Transit Upgrade",
        "description": "Electrify public transit fleets and expand affordable bus and rail access.",
        "policy_type": "sustainable",
    },
    {
        "name": "Wetland Restoration Program",
        "description": "Protect biodiversity and absorb flood risk by restoring damaged wetlands.",
        "policy_type": "sustainable",
    },
    {
        "name": "Industrial Efficiency Standard",
        "description": "Require major industrial emitters to adopt proven efficiency upgrades.",
        "policy_type": "sustainable",
    },
    {
        "name": "Community Solar Grants",
        "description": "Help local communities install shared solar for homes and public buildings.",
        "policy_type": "sustainable",
    },
    {
        "name": "Forest Protection Act",
        "description": "Ban destructive logging in critical carbon sinks and wildlife corridors.",
        "policy_type": "sustainable",
    },
    {
        "name": "Waterway Cleanup Fund",
        "description": "Invest in river restoration and industrial runoff enforcement.",
        "policy_type": "sustainable",
    },
    {
        "name": "Circular Manufacturing Incentive",
        "description": "Reward manufacturers that reuse materials and reduce landfill waste.",
        "policy_type": "sustainable",
    },
    {
        "name": "Offshore Drilling Expansion",
        "description": "Open new offshore reserves to speed up fossil fuel extraction.",
        "policy_type": "exploitative",
    },
    {
        "name": "Coal Plant Lifetime Extension",
        "description": "Subsidize aging coal plants to delay retirement and preserve output.",
        "policy_type": "exploitative",
    },
    {
        "name": "Protected Land Deregulation",
        "description": "Remove environmental safeguards to accelerate commercial land use.",
        "policy_type": "exploitative",
    },
    {
        "name": "Pipeline Fast-Track Law",
        "description": "Bypass review timelines for major fossil fuel pipeline projects.",
        "policy_type": "exploitative",
    },
    {
        "name": "Single-Use Plastics Exemption",
        "description": "Exempt major producers from plastic reduction requirements.",
        "policy_type": "exploitative",
    },
    {
        "name": "Industrial Dumping Amnesty",
        "description": "Reduce penalties for companies dumping pollutants near waterways.",
        "policy_type": "exploitative",
    },
    {
        "name": "Open-Pit Mining Subsidy",
        "description": "Offer tax relief for large-scale extraction in sensitive ecosystems.",
        "policy_type": "exploitative",
    },
    {
        "name": "Air Quality Rollback",
        "description": "Relax emission thresholds for high-polluting industrial facilities.",
        "policy_type": "exploitative",
    },
]


def _build_pool(policy_type: PolicyType) -> list[PolicyCard]:
    cards = [
        PolicyCard(name=c["name"], description=c["description"], policy_type=policy_type)
        for c in POLICY_CARDS
        if c["policy_type"] == policy_type.value
    ]
    random.shuffle(cards)
    return cards


def _clone_cards(cards: list[PolicyCard]) -> list[PolicyCard]:
    return [
        PolicyCard(name=card.name, description=card.description, policy_type=card.policy_type)
        for card in cards
    ]


def deal_hands(
    roles: dict[str, str],
    cards_per_player: int = 5,
) -> dict[str, list[PolicyCard]]:
    """Deal cards to each player based on role.

    Reformers receive sustainable cards, Exploiters receive exploitative cards.
    Returns a mapping of player_id -> list of PolicyCard.
    """
    sustainable_templates = _build_pool(PolicyType.SUSTAINABLE)
    exploitative_templates = _build_pool(PolicyType.EXPLOITATIVE)
    sustainable_pool = _clone_cards(sustainable_templates)
    exploitative_pool = _clone_cards(exploitative_templates)

    hands: dict[str, list[PolicyCard]] = {}
    for player_id, role in roles.items():
        if role in ("reformer", "REFORMER", "Reformer"):
            pool = sustainable_pool
            templates = sustainable_templates
        else:
            pool = exploitative_pool
            templates = exploitative_templates

        hand: list[PolicyCard] = []
        for _ in range(cards_per_player):
            if not templates:
                break
            if not pool:
                pool.extend(_clone_cards(templates))
                random.shuffle(pool)
            hand.append(pool.pop())
        hands[player_id] = hand

    return hands
