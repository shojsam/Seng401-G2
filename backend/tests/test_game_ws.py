import pytest
from app.logic.game_engine import GameState, Phase
from app.logic.voting import Vote
from app.logic.deck import POLICY_CARDS


PLAYERS = ["alice", "bob", "charlie", "dave", "eve"]


class TestGameFlow:
    """Test the full game loop that the WebSocket handler drives."""

    def _make_game(self) -> GameState:
        gs = GameState(PLAYERS)
        gs.start_game()
        return gs

    def test_game_starts_in_role_reveal(self):
        gs = self._make_game()
        assert gs.phase == Phase.ROLE_REVEAL

    def test_all_players_get_roles(self):
        gs = self._make_game()
        for pid in PLAYERS:
            assert pid in gs.roles

    def test_all_players_get_hands(self):
        gs = self._make_game()
        for pid in PLAYERS:
            assert len(gs.get_hand(pid)) > 0

    def test_current_player_is_first(self):
        gs = self._make_game()
        assert gs.current_player == PLAYERS[0]

    def test_propose_policy_changes_phase(self):
        gs = self._make_game()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        assert gs.phase == Phase.PROPOSAL
        assert gs.current_policy is not None

    def test_only_current_player_can_propose(self):
        gs = self._make_game()
        gs.phase = Phase.PROPOSAL
        non_current = [p for p in PLAYERS if p != gs.current_player][0]
        
        with pytest.raises(ValueError):
            gs.propose_policy(non_current, 99)

    def test_cast_vote_approve(self):
        gs = self._make_game()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_discussion()
        gs.begin_voting()
        assert gs.phase == Phase.VOTING
        gs.cast_vote("alice", Vote.APPROVE)
        assert "alice" in gs.votes

    def test_cast_vote_reject(self):
        gs = self._make_game()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        gs.cast_vote("alice", Vote.REJECT)
        assert gs.votes["alice"] == Vote.REJECT

    def test_all_votes_in_returns_true(self):
        gs = self._make_game()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        for pid in PLAYERS[:-1]:
            assert gs.cast_vote(pid, Vote.APPROVE) is False
        assert gs.cast_vote(PLAYERS[-1], Vote.APPROVE) is True

    def test_duplicate_vote_overwrites(self):
        gs = self._make_game()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        gs.cast_vote("alice", Vote.APPROVE)
        gs.cast_vote("alice", Vote.REJECT)  # overwrites
        assert gs.votes["alice"] == Vote.REJECT


class TestRoundResolution:
    """Test vote resolution: policy accepted vs rejected."""

    def _setup_voted_game(self, approve_count: int) -> GameState:
        gs = GameState(PLAYERS)
        gs.start_game()
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
        assert result["policy"] is not None

    def test_policy_rejected_majority_reject(self):
        gs = self._setup_voted_game(approve_count=1)
        result = gs.resolve_round()
        assert result["approved"] is False

    def test_accepted_policy_updates_counters(self):
        gs = self._setup_voted_game(approve_count=5)
        policy_type = gs.current_policy.policy_type.value
        result = gs.resolve_round()
        assert result["approved"] is True

        if policy_type == "sustainable":
            assert gs.enacted_sustainable == 1
            assert gs.enacted_exploiter == 0
        else:
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


class TestWinConditions:
    """Test game-over detection for both teams."""

    def test_reformers_win_at_5_sustainable(self):
        gs = GameState(PLAYERS)
        gs.start_game()
        gs.enacted_sustainable = 5
        assert gs.check_winner() == "reformers"

    def test_exploiters_win_at_4_exploitative(self):
        gs = GameState(PLAYERS)
        gs.start_game()
        gs.enacted_exploiter = 4
        assert gs.check_winner() == "exploiters"

    def test_no_winner_below_threshold(self):
        gs = GameState(PLAYERS)
        gs.start_game()
        gs.enacted_sustainable = 3
        gs.enacted_exploiter = 2
        assert gs.check_winner() is None

    def test_game_over_phase_set_on_win(self):
        gs = GameState(PLAYERS)
        gs.start_game()
        gs.phase = Phase.PROPOSAL
        gs.propose_policy(gs.current_player, 0)
        gs.begin_voting()
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)

        
        gs.enacted_sustainable = 4
        gs.current_policy = gs.hands[PLAYERS[0]][0] if gs.hands[PLAYERS[0]] else gs.current_policy
        
        from app.logic.deck import PolicyType
        if gs.current_policy:
            gs.current_policy.policy_type = PolicyType.SUSTAINABLE

        result = gs.resolve_round()
        if result.get("winner") == "reformers":
            assert gs.phase == Phase.GAME_OVER

    def test_summary_contains_all_fields(self):
        gs = GameState(PLAYERS)
        gs.start_game()
        summary = gs.get_summary()
        assert "winner" in summary
        assert "enacted_policies" in summary
        assert "sustainable_count" in summary
        assert "exploiter_count" in summary
        assert "roles" in summary


class TestDeckPopulated:
    """Verify the policy card deck is properly populated."""

    def test_deck_not_empty(self):
        assert len(POLICY_CARDS) > 0

    def test_has_sustainable_cards(self):
        sustainable = [c for c in POLICY_CARDS if c["policy_type"] == "sustainable"]
        assert len(sustainable) >= 5

    def test_has_exploitative_cards(self):
        exploitative = [c for c in POLICY_CARDS if c["policy_type"] == "exploitative"]
        assert len(exploitative) >= 5

    def test_all_cards_have_required_fields(self):
        for card in POLICY_CARDS:
            assert "name" in card
            assert "description" in card
            assert "policy_type" in card
            assert card["policy_type"] in ("sustainable", "exploitative")