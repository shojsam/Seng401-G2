import pytest
from app.logic.game_engine import GameState, Phase
from app.logic.voting import Vote
from app.logic.deck import PolicyCard, PolicyType


PLAYERS = ["alice", "bob", "charlie", "dave", "eve"]


def _make_game() -> GameState:
    """Create a GameState with a started game."""
    gs = GameState(PLAYERS)
    gs.start_game()
    return gs


def _inject_draw_pile(gs: GameState, cards: list[PolicyCard]):
    """Replace the draw pile with specific cards for deterministic tests."""
    gs.draw_pile = list(cards)


class TestGameStart:
    def test_game_starts_in_role_reveal(self):
        gs = _make_game()
        assert gs.phase == Phase.ROLE_REVEAL

    def test_all_players_get_roles(self):
        gs = _make_game()
        for pid in PLAYERS:
            assert pid in gs.roles

    def test_leader_is_first_player(self):
        gs = _make_game()
        assert gs.leader == PLAYERS[0]

    def test_draw_pile_created(self):
        gs = _make_game()
        assert len(gs.draw_pile) > 0

    def test_summary_contains_all_fields(self):
        gs = _make_game()
        summary = gs.get_summary()
        assert "winner" in summary
        assert "enacted_policies" in summary
        assert "sustainable_count" in summary
        assert "exploiter_count" in summary
        assert "roles" in summary


class TestNomination:
    def test_leader_can_nominate_vice(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        result = gs.nominate_vice(gs.leader, PLAYERS[1])
        assert result["nominated_vice"] == PLAYERS[1]
        assert gs.phase == Phase.ELECTION

    def test_non_leader_cannot_nominate(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        with pytest.raises(ValueError):
            gs.nominate_vice(PLAYERS[1], PLAYERS[2])

    def test_leader_cannot_nominate_self(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        with pytest.raises(ValueError):
            gs.nominate_vice(gs.leader, gs.leader)

    def test_cannot_nominate_invalid_player(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        with pytest.raises(ValueError):
            gs.nominate_vice(gs.leader, "nobody")


class TestElection:
    def test_cast_vote_records_vote(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        gs.nominate_vice(gs.leader, PLAYERS[1])
        gs.cast_vote("alice", Vote.APPROVE)
        assert "alice" in gs.votes

    def test_all_votes_returns_true(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS[:-1]:
            assert gs.cast_vote(pid, Vote.APPROVE) is False
        assert gs.cast_vote(PLAYERS[-1], Vote.APPROVE) is True

    def test_approved_election_goes_to_leader_discard(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        result = gs.resolve_election()
        assert result["approved"] is True
        assert gs.phase == Phase.LEADER_DISCARD

    def test_rejected_election_advances_turn(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.REJECT)
        old_turn = gs.turn_index
        result = gs.resolve_election()
        assert result["approved"] is False
        assert gs.turn_index == old_turn + 1
        assert gs.phase == Phase.NOMINATION

    def test_election_tracker_increments_on_reject(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.REJECT)
        gs.resolve_election()
        assert gs.election_tracker == 1


class TestLeaderDiscard:
    def _setup_approved(self) -> GameState:
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        _inject_draw_pile(gs, [
            PolicyCard(PolicyType.SUSTAINABLE, "S1", "desc"),
            PolicyCard(PolicyType.SUSTAINABLE, "S2", "desc"),
            PolicyCard(PolicyType.EXPLOITATIVE, "E1", "desc"),
        ])
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        gs.resolve_election()
        return gs

    def test_leader_discards_one_card(self):
        gs = self._setup_approved()
        assert len(gs.leader_hand) == 3
        result = gs.leader_discard(gs.leader, 0)
        assert gs.phase == Phase.VICE_ENACT
        assert len(gs.vice_hand) == 2

    def test_non_leader_cannot_discard(self):
        gs = self._setup_approved()
        with pytest.raises(ValueError):
            gs.leader_discard(PLAYERS[1], 0)

    def test_invalid_discard_index_raises(self):
        gs = self._setup_approved()
        with pytest.raises(ValueError):
            gs.leader_discard(gs.leader, 99)


class TestViceEnact:
    def _setup_vice_phase(self) -> GameState:
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        _inject_draw_pile(gs, [
            PolicyCard(PolicyType.SUSTAINABLE, "S1", "desc"),
            PolicyCard(PolicyType.SUSTAINABLE, "S2", "desc"),
            PolicyCard(PolicyType.EXPLOITATIVE, "E1", "desc"),
        ])
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        gs.resolve_election()
        gs.leader_discard(gs.leader, 0)
        return gs

    def test_vice_enacts_policy(self):
        gs = self._setup_vice_phase()
        vice = gs.nominated_vice
        result = gs.vice_enact(vice, 0)
        assert "enacted_policy" in result
        assert "sustainable_count" in result

    def test_non_vice_cannot_enact(self):
        gs = self._setup_vice_phase()
        with pytest.raises(ValueError):
            gs.vice_enact(PLAYERS[2], 0)

    def test_enacting_sustainable_increments_counter(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        _inject_draw_pile(gs, [
            PolicyCard(PolicyType.SUSTAINABLE, "S1", "desc"),
            PolicyCard(PolicyType.SUSTAINABLE, "S2", "desc"),
            PolicyCard(PolicyType.SUSTAINABLE, "S3", "desc"),
        ])
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        gs.resolve_election()
        gs.leader_discard(gs.leader, 0)
        gs.vice_enact(gs.nominated_vice, 0)
        assert gs.enacted_sustainable == 1
        assert gs.enacted_exploiter == 0

    def test_enacting_exploitative_increments_counter(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        _inject_draw_pile(gs, [
            PolicyCard(PolicyType.EXPLOITATIVE, "E1", "desc"),
            PolicyCard(PolicyType.EXPLOITATIVE, "E2", "desc"),
            PolicyCard(PolicyType.EXPLOITATIVE, "E3", "desc"),
        ])
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        gs.resolve_election()
        gs.leader_discard(gs.leader, 0)
        gs.vice_enact(gs.nominated_vice, 0)
        assert gs.enacted_exploiter == 1
        assert gs.enacted_sustainable == 0


class TestWinConditions:
    def test_reformers_win_at_5_sustainable(self):
        gs = _make_game()
        gs.enacted_sustainable = 5
        assert gs.check_winner() == "reformers"

    def test_exploiters_win_at_3_exploitative(self):
        gs = _make_game()
        gs.enacted_exploiter = 3
        assert gs.check_winner() == "exploiters"

    def test_no_winner_below_threshold(self):
        gs = _make_game()
        gs.enacted_sustainable = 3
        gs.enacted_exploiter = 2
        assert gs.check_winner() is None

    def test_game_over_phase_on_win(self):
        gs = _make_game()
        gs.enacted_sustainable = 4
        gs.phase = Phase.NOMINATION
        _inject_draw_pile(gs, [
            PolicyCard(PolicyType.SUSTAINABLE, "Win", "desc"),
            PolicyCard(PolicyType.SUSTAINABLE, "S2", "desc"),
            PolicyCard(PolicyType.SUSTAINABLE, "S3", "desc"),
        ])
        gs.nominate_vice(gs.leader, PLAYERS[1])
        for pid in PLAYERS:
            gs.cast_vote(pid, Vote.APPROVE)
        gs.resolve_election()
        gs.leader_discard(gs.leader, 2)
        result = gs.vice_enact(gs.nominated_vice, 0)
        assert result["winner"] == "reformers"
        assert gs.phase == Phase.GAME_OVER


class TestTermLimits:
    def test_ineligible_includes_leader(self):
        gs = _make_game()
        assert gs.leader in gs.ineligible_for_vice

    def test_prev_leader_ineligible(self):
        gs = _make_game()
        gs.prev_leader = PLAYERS[2]
        assert PLAYERS[2] in gs.ineligible_for_vice

    def test_prev_vice_ineligible(self):
        gs = _make_game()
        gs.prev_vice = PLAYERS[3]
        assert PLAYERS[3] in gs.ineligible_for_vice

    def test_cannot_nominate_prev_leader(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        gs.prev_leader = PLAYERS[1]
        with pytest.raises(ValueError):
            gs.nominate_vice(gs.leader, PLAYERS[1])

    def test_cannot_nominate_prev_vice(self):
        gs = _make_game()
        gs.phase = Phase.NOMINATION
        gs.prev_vice = PLAYERS[1]
        with pytest.raises(ValueError):
            gs.nominate_vice(gs.leader, PLAYERS[1])


class TestRoundInfo:
    def test_round_info_contains_all_fields(self):
        gs = _make_game()
        info = gs.get_round_info()
        assert "phase" in info
        assert "leader" in info
        assert "nominated_vice" in info
        assert "turn_index" in info
        assert "sustainable_count" in info
        assert "exploiter_count" in info
        assert "election_tracker" in info
        assert "ineligible_ids" in info
