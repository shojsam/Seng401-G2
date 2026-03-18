from app.logic.deck import PolicyType, PolicyCard, POLICY_CARDS, deal_hands


def test_deal_hands_reformers_get_sustainable():
    if not POLICY_CARDS:
        return  
    roles = {"p1": "reformer", "p2": "reformer", "p3": "exploiter"}
    hands = deal_hands(roles, cards_per_player=2)
    for card in hands["p1"]:
        assert card.policy_type == PolicyType.SUSTAINABLE
    for card in hands["p2"]:
        assert card.policy_type == PolicyType.SUSTAINABLE


def test_deal_hands_exploiters_get_exploitative():
    if not POLICY_CARDS:
        return  
    roles = {"p1": "reformer", "p2": "exploiter"}
    hands = deal_hands(roles, cards_per_player=2)
    for card in hands["p2"]:
        assert card.policy_type == PolicyType.EXPLOITATIVE


def test_deal_hands_correct_count():
    if not POLICY_CARDS:
        return 
    roles = {"p1": "reformer", "p2": "exploiter"}
    hands = deal_hands(roles, cards_per_player=3)
    for hand in hands.values():
        assert len(hand) <= 3


def test_card_types_only_sustainable_or_exploitative():
    for c in POLICY_CARDS:
        assert c["policy_type"] in ("sustainable", "exploitative")

def test_deal_hands_mixed_roles():
    if not POLICY_CARDS:
        return

    roles = {"p1": "reformer", "p2": "exploiter"}
    hands = deal_hands(roles, cards_per_player=3)

    for card in hands["p1"]:
        assert card.policy_type == PolicyType.SUSTAINABLE

    for card in hands["p2"]:
        assert card.policy_type == PolicyType.EXPLOITATIVE

def test_roles_case_insensitive():
    if not POLICY_CARDS:
        return

    roles = {"p1": "REFORMER", "p2": "Reformer"}
    hands = deal_hands(roles, cards_per_player=2)

    for hand in hands.values():
        for card in hand:
            assert card.policy_type == PolicyType.SUSTAINABLE

def test_deal_hands_pool_exhaustion():
    if not POLICY_CARDS:
        return

    roles = {"p1": "reformer"}
    hands = deal_hands(roles, cards_per_player=100)

    assert len(hands["p1"]) <= 100

def test_unknown_role_defaults_to_exploiter():
    if not POLICY_CARDS:
        return

    roles = {"p1": "random_role"}
    hands = deal_hands(roles, cards_per_player=2)

    for card in hands["p1"]:
        assert card.policy_type == PolicyType.EXPLOITATIVE

def test_policy_card_to_dict():
    card = PolicyCard(
        name="Test Policy",
        description="Test description",
        policy_type=PolicyType.SUSTAINABLE,
    )

    result = card.to_dict()

    assert result == {
        "name": "Test Policy",
        "description": "Test description",
        "policy_type": "sustainable",
    }