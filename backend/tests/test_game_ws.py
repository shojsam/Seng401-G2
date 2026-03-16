import pytest
from app.logic.game_engine import GameState, Phase
from app.logic.voting import Vote
from app.logic.deck import PolicyCard, PolicyType


PLAYERS = ["alice", "bob", "charlie", "dave", "eve"]


def _make_game_with_cards() -> GameState:
    """Create a GameState and manually inject cards (since POLICY_CARDS may be empty)."""
    gs = GameState(PLAYERS)
    gs.start_game()

    # Manually give every player some cards so we can test the flow
    for pid in PLAYERS:
        gs.hands[pid] = [
            PolicyCard("Test Sustainable", "A test policy", PolicyType.SUSTAINABLE),
            PolicyCard("Test Exploitative", "Another test policy", PolicyType.EXPLOITATIVE),
            PolicyCard("Test Policy 3", "Third test policy", PolicyType.SUSTAINABLE),
        ]
    return gs


class TestGameFlow:
    """Test the full game loop that the WebSocket handler drives."""

    def test_game_starts_in_role_reveal(self):
        gs = _make_game_with_cards()
        assert gs.phase == Phase.ROLE_REVEAL

    def test_all_players_get_roles(self):
        gs = _make_game_with_cards()
        for pid in PLAYERS:
            assert pid in gs.roles

    def test_current_player_is_first(self):
        gs = _make_game_with_cards()
        assert gs.current_player == PLAYERS[0]

    def test_propose_policy_sets_current_policy(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        policy = gs.propose_policy(gs.current_player, 0)
        assert gs.current_policy is not None
        assert policy.name == "Test Sustainable"

    def test_propose_policy_removes_card_from_hand(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        current = gs.current_player
        before = len(gs.hands[current])
        gs.propose_policy(current, 0)
        assert len(gs.hands[current]) == before - 1

    def test_invalid_card_index_raises(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        with pytest.raises(ValueError):
            gs.propose_policy(gs.current_player, 99)

    def test_cast_vote_approve(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        assert gs.phase == Phase.VOTING
        gs.cast_vote("alice", Vote.APPROVE)
        assert "alice" in gs.votes
        assert gs.votes["alice"] == Vote.APPROVE

    def test_cast_vote_reject(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        gs.cast_vote("bob", Vote.REJECT)
        assert gs.votes["bob"] == Vote.REJECT

    def test_all_votes_in_returns_true(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        for pid in PLAYERS[:-1]:
            assert gs.cast_vote(pid, Vote.APPROVE) is False
        assert gs.cast_vote(PLAYERS[-1], Vote.APPROVE) is True

    def test_duplicate_vote_overwrites(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        gs.cast_vote("alice", Vote.APPROVE)
        gs.cast_vote("alice", Vote.REJECT)  # overwrites
        assert gs.votes["alice"] == Vote.REJECT

    def test_discussion_phase_transition(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_discussion()
        assert gs.phase == Phase.DISCUSSION

    def test_voting_phase_transition(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_discussion()
        gs.begin_voting()
        assert gs.phase == Phase.VOTING


class TestRoundResolution:
    """Test vote resolution: policy accepted vs rejected."""

    def _setup_voted_game(self, approve_count: int) -> GameState:
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()

        for i, pid in enumerate(PLAYERS):
            vote = Vote.APPROVE if i < approve_count else Vote.REJECT
            gs.cast_vote(pid, vote)
        return gs

    def test_policy_accepted_majority_approve(self):
        gs = self._setup_voted_game(approve_count=4)
        result = gs.resolve_round()
        assert result["approved"] is True
        assert result["status"] if "status" in result else result["approved"]

    def test_policy_rejected_majority_reject(self):
        gs = self._setup_voted_game(approve_count=1)
        result = gs.resolve_round()
        assert result["approved"] is False

    def test_accepted_sustainable_increments_counter(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        # Card at index 0 is PolicyType.SUSTAINABLE
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        result = gs.resolve_round()
        assert result["approved"] is True
        assert gs.enacted_sustainable == 1
        assert gs.enacted_exploiter == 0

    def test_accepted_exploitative_increments_counter(self):
        gs = _make_game_with_cards()
        gs.phase = Phase.PROPOSAL
        # Card at index 1 is PolicyType.EXPLOITATIVE
        gs.propose_policy(gs.current_player, 1)
        gs.begin_voting()
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        result = gs.resolve_round()
        assert result["approved"] is True
        assert gs.enacted_exploiter == 1
        assert gs.enacted_sustainable == 0

    def test_rejected_policy_no_counter_change(self):
        gs = self._setup_voted_game(approve_count=0)
        gs.resolve_round()
        assert gs.enacted_sustainable == 0
        assert gs.enacted_exploiter == 0

    def test_turn_advances_after_resolution(self):
        gs = self._setup_voted_game(approve_count=3)
        old_index = gs.turn_index
        gs.resolve_round()
        assert gs.turn_index == old_index + 1

    def test_resolution_includes_all_votes(self):
        gs = self._setup_voted_game(approve_count=3)
        result = gs.resolve_round()
        assert len(result["votes"]) == len(PLAYERS)

    def test_tie_vote_rejects(self):
        """With 5 players, 2 approve and 3 reject → rejected."""
        gs = self._setup_voted_game(approve_count=2)
        result = gs.resolve_round()
        assert result["approved"] is False

    def test_policy_cleared_after_resolution(self):
        gs = self._setup_voted_game(approve_count=5)
        gs.resolve_round()
        assert gs.current_policy is None

    def test_enacted_policies_list_updated_on_accept(self):
        gs = self._setup_voted_game(approve_count=5)
        gs.resolve_round()
        assert len(gs.enacted_policies) == 1

    def test_enacted_policies_list_unchanged_on_reject(self):
        gs = self._setup_voted_game(approve_count=0)
        gs.resolve_round()
        assert len(gs.enacted_policies) == 0


class TestWinConditions:
    """Test game-over detection for both teams."""

    def test_reformers_win_at_5_sustainable(self):
        gs = _make_game_with_cards()
        gs.enacted_sustainable = 5
        assert gs.check_winner() == "reformers"

    def test_exploiters_win_at_4_exploitative(self):
        gs = _make_game_with_cards()
        gs.enacted_exploiter = 4
        assert gs.check_winner() == "exploiters"

    def test_no_winner_below_threshold(self):
        gs = _make_game_with_cards()
        gs.enacted_sustainable = 3
        gs.enacted_exploiter = 2
        assert gs.check_winner() is None

    def test_game_over_phase_on_win(self):
        gs = _make_game_with_cards()
        gs.enacted_sustainable = 4
        gs.phase = Phase.PROPOSAL
        # Give a sustainable card to trigger the win
        gs.hands[gs.current_player] = [
            PolicyCard("Winning Policy", "Wins the game", PolicyType.SUSTAINABLE),
        ]
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        result = gs.resolve_round()
        assert result["winner"] == "reformers"
        assert gs.phase == Phase.GAME_OVER

    def test_summary_contains_all_fields(self):
        gs = _make_game_with_cards()
        summary = gs.get_summary()
        assert "winner" in summary
        assert "enacted_policies" in summary
        assert "sustainable_count" in summary
        assert "exploiter_count" in summary
        assert "roles" in summary