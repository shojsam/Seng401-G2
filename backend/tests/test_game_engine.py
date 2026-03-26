import pytest
from app.logic.game_engine import GameState, Phase, PolicyType, PolicyCard

@pytest.fixture
def game():
    """Starts a game with 5 players."""
    players = ["p1", "p2", "p3", "p4", "p5"]
    gs = GameState(players)
    gs.start_game()
    return gs

def test_initial_leader_rotation(game):
    assert game.leader == "p1"
    game._advance_turn()
    assert game.leader == "p2"

def test_term_limits_enforced(game):
    game.nominate_vice("p1", "p2")
    
    game.prev_leader = "p1"
    game.prev_vice = "p2"
    game._advance_turn()
    
    with pytest.raises(ValueError, match="restricted"):
        game.nominate_vice("p2", "p1")

def test_deck_refill_logic(game):
    game.draw_pile = []
    game.discard_pile = [PolicyCard(PolicyType.SUSTAINABLE)]
    
    game._refill_if_needed(1)
    
    assert len(game.draw_pile) == 1
    assert len(game.discard_pile) == 0

def test_election_tracker_reset_on_success(game):
    game.election_tracker = 2
    policy = PolicyCard(PolicyType.SUSTAINABLE)
    game._resolve_enacted(policy)
    
    assert game.election_tracker == 0