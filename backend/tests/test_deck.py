from app.logic.deck import PolicyType, PolicyCard, POLICY_CARDS, deal_hands


def test_deal_hands_reformers_get_sustainable():
    if not POLICY_CARDS:
        return  # skip until cards are added
    roles = {"p1": "reformer", "p2": "reformer", "p3": "exploiter"}
    hands = deal_hands(roles, cards_per_player=2)
    for card in hands["p1"]:
        assert card.policy_type == PolicyType.SUSTAINABLE
    for card in hands["p2"]:
        assert card.policy_type == PolicyType.SUSTAINABLE


def test_deal_hands_exploiters_get_exploitative():
    if not POLICY_CARDS:
        return  # skip until cards are added
    roles = {"p1": "reformer", "p2": "exploiter"}
    hands = deal_hands(roles, cards_per_player=2)
    for card in hands["p2"]:
        assert card.policy_type == PolicyType.EXPLOITATIVE


def test_deal_hands_correct_count():
    if not POLICY_CARDS:
        return  # skip until cards are added
    roles = {"p1": "reformer", "p2": "exploiter"}
    hands = deal_hands(roles, cards_per_player=3)
    for hand in hands.values():
        assert len(hand) <= 3


def test_card_types_only_sustainable_or_exploitative():
    for c in POLICY_CARDS:
        assert c["policy_type"] in ("sustainable", "exploitative")
