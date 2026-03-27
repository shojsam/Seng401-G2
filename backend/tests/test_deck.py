import pytest
from unittest.mock import patch
from app.logic.deck import create_deck, PolicyType, EXPLOITATIVE_COUNT, SUSTAINABLE_COUNT


@patch("app.logic.deck._load_cards_from_db")
def test_create_deck_uses_db_when_available(mock_load):
    from app.logic.deck import PolicyCard
    mock_load.return_value = [PolicyCard(PolicyType.SUSTAINABLE, title="Green Energy")]
    
    deck = create_deck()
    
    assert len(deck) == 1
    assert deck[0].title == "Green Energy"
    assert deck[0].policy_type == PolicyType.SUSTAINABLE

@patch("app.logic.deck._load_cards_from_db")
def test_create_deck_uses_fallback_on_failure(mock_load):
    mock_load.return_value = None
    
    deck = create_deck()
    
    assert len(deck) == EXPLOITATIVE_COUNT + SUSTAINABLE_COUNT
    
    exploitative = [c for c in deck if c.policy_type == PolicyType.EXPLOITATIVE]
    sustainable = [c for c in deck if c.policy_type == PolicyType.SUSTAINABLE]
    
    assert len(exploitative) == EXPLOITATIVE_COUNT
    assert len(sustainable) == SUSTAINABLE_COUNT


def test_load_from_db_mapping_logic():
    """
    Directly test the logic that converts DB rows to objects.
    Note: You may need to expose _load_cards_from_db for testing 
    or test it via create_deck.
    """
    with patch("app.data.repository.get_all_cards") as mock_repo:
        mock_repo.return_value = [
            {"card_type": "SUSTAINABLE", "card_name": "Wind Farm"},
            {"card_type": "exploitative", "card_name": "Coal"},
            {"card_type": "invalid_type", "card_name": "Ghost"}
        ]
        
        deck = create_deck()
        
        assert len(deck) == 2
        assert deck[0].title == "Wind Farm"
        assert deck[1].title == "Coal"

def test_policy_card_to_dict():
    from app.logic.deck import PolicyCard
    card = PolicyCard(PolicyType.SUSTAINABLE, "Title", "Desc", "Hint")
    data = card.to_dict()
    
    assert data["policy_type"] == "sustainable"
    assert data["title"] == "Title"
    assert "description" in data