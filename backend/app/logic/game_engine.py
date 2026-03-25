"""
game_engine.py — Core game state for GREENWASHED (Leader/Vice variant).

Flow per round:
  1. NOMINATION  — Leader (rotating) picks a Vice from other players
  2. ELECTION    — All players vote to approve/reject the Leader/Vice pair
  3. LEADER_DISCARD — Leader draws 3 cards, discards 1 (secretly)
  4. VICE_ENACT  — Vice picks 1 of the remaining 2 to enact
  5. RESOLUTION  — Policy is applied, win condition checked, turn advances

Strategic dynamics:
  • Exploiter as leader can nominate fellow exploiter → easy exploitative policies
  • Reformer leader accidentally picks exploiter as vice → exploiter can play along
    (enact sustainable) to hide, or push exploitative
  • Reformer leader draws EEE, picks reformer vice → vice is forced to enact
    exploitative, making leader look suspicious
"""
from enum import Enum
from typing import Optional

from .roles import Role, assign_roles, get_exploiter_ids
from .deck import PolicyCard, PolicyType, create_deck, shuffle_deck
from .voting import Vote, resolve_votes


class Phase(str, Enum):
    LOBBY = "lobby"
    ROLE_REVEAL = "role_reveal"
    NOMINATION = "nomination"
    ELECTION = "election"
    LEADER_DISCARD = "leader_discard"
    VICE_ENACT = "vice_enact"
    RESOLUTION = "resolution"
    GAME_OVER = "game_over"


# Win conditions
SUSTAINABLE_WIN_COUNT = 5
EXPLOITER_WIN_COUNT = 3

# Card counts
LEADER_DRAW_COUNT = 3
VICE_CHOICE_COUNT = 2


class GameState:
    """Holds all mutable state for a single game session."""

    def __init__(self, player_ids: list[str]):
        self.player_ids = player_ids
        self.roles: dict[str, Role] = {}
        self.phase = Phase.LOBBY
        self.turn_index = 0

        # Shared policy deck
        self.draw_pile: list[PolicyCard] = []
        self.discard_pile: list[PolicyCard] = []

        # Round state
        self.nominated_vice: Optional[str] = None
        self.votes: dict[str, Vote] = {}
        self.leader_hand: list[PolicyCard] = []
        self.vice_hand: list[PolicyCard] = []
        self.enacted_policy: Optional[PolicyCard] = None
        self.election_tracker = 0

        # Scoring
        self.enacted_sustainable = 0
        self.enacted_exploiter = 0
        self.enacted_policies: list[dict] = []
        self.winner: Optional[str] = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def leader(self) -> str:
        """The current round's leader (rotates each turn)."""
        return self.player_ids[self.turn_index % len(self.player_ids)]

    # ------------------------------------------------------------------
    # Game start
    # ------------------------------------------------------------------

    def start_game(self) -> dict:
        """Assign roles and create the shared policy deck."""
        self.roles = assign_roles(self.player_ids)
        self.draw_pile = create_deck()
        shuffle_deck(self.draw_pile)
        self.phase = Phase.ROLE_REVEAL
        return {
            "roles": {pid: role.value for pid, role in self.roles.items()},
            "exploiter_ids": get_exploiter_ids(self.roles),
            "leader": self.leader,
        }

    # ------------------------------------------------------------------
    # Phase 1 — Nomination: Leader picks a Vice
    # ------------------------------------------------------------------

    def nominate_vice(self, leader_id: str, vice_id: str) -> dict:
        """Leader nominates another player as Vice for this round."""
        if leader_id != self.leader:
            raise ValueError("Only the current leader can nominate a vice")
        if vice_id == leader_id:
            raise ValueError("Leader cannot nominate themselves")
        if vice_id not in self.player_ids:
            raise ValueError("Vice must be a valid player")

        self.nominated_vice = vice_id
        self.votes.clear()
        self.phase = Phase.ELECTION
        return {
            "leader": leader_id,
            "nominated_vice": vice_id,
        }

    # ------------------------------------------------------------------
    # Phase 2 — Election: All players vote on the Leader/Vice pair
    # ------------------------------------------------------------------

    def cast_vote(self, player_id: str, vote: Vote) -> bool:
        """Record a vote. Returns True when all votes are in."""
        if self.phase != Phase.ELECTION:
            raise ValueError("Not in the election phase")
        self.votes[player_id] = vote
        return len(self.votes) == len(self.player_ids)

    def resolve_election(self) -> dict:
        """Tally votes. If approved → leader draws cards.
        If rejected → advance turn (failed election)."""
        approved = resolve_votes(self.votes)
        result: dict = {
            "approved": approved,
            "votes": {pid: v.value for pid, v in self.votes.items()},
            "leader": self.leader,
            "nominated_vice": self.nominated_vice,
        }

        if approved:
            self._refill_if_needed(LEADER_DRAW_COUNT)
            self.leader_hand = [self.draw_pile.pop() for _ in range(LEADER_DRAW_COUNT)]
            self.phase = Phase.LEADER_DISCARD
            result["leader_hand"] = [c.to_dict() for c in self.leader_hand]
        else:
            self.election_tracker += 1
            self._advance_turn()
            self.phase = Phase.NOMINATION
            result["election_tracker"] = self.election_tracker

            if self.election_tracker >= 3:
                forced = self._force_enact_top_card()
                result["forced_policy"] = forced

        return result

    # ------------------------------------------------------------------
    # Phase 3 — Leader discards one card, passes 2 to Vice
    # ------------------------------------------------------------------

    def leader_discard(self, leader_id: str, discard_index: int) -> dict:
        """Leader discards 1 of 3 drawn cards. Remaining 2 go to Vice."""
        if self.phase != Phase.LEADER_DISCARD:
            raise ValueError("Not in the leader discard phase")
        if leader_id != self.leader:
            raise ValueError("Only the leader can discard")
        if discard_index < 0 or discard_index >= len(self.leader_hand):
            raise ValueError("Invalid discard index")

        discarded = self.leader_hand.pop(discard_index)
        self.discard_pile.append(discarded)

        self.vice_hand = list(self.leader_hand)
        self.leader_hand.clear()
        self.phase = Phase.VICE_ENACT

        return {
            "vice_id": self.nominated_vice,
            "vice_hand": [c.to_dict() for c in self.vice_hand],
        }

    # ------------------------------------------------------------------
    # Phase 4 — Vice enacts one of the two remaining cards
    # ------------------------------------------------------------------

    def vice_enact(self, vice_id: str, enact_index: int) -> dict:
        """Vice picks which of the 2 cards to enact."""
        if self.phase != Phase.VICE_ENACT:
            raise ValueError("Not in the vice enact phase")
        if vice_id != self.nominated_vice:
            raise ValueError("Only the nominated vice can enact a policy")
        if enact_index < 0 or enact_index >= len(self.vice_hand):
            raise ValueError("Invalid enact index")

        enacted = self.vice_hand.pop(enact_index)
        self.discard_pile.extend(self.vice_hand)
        self.vice_hand.clear()

        self.enacted_policy = enacted
        self.phase = Phase.RESOLUTION
        return self._resolve_enacted(enacted)

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    def _resolve_enacted(self, policy: PolicyCard) -> dict:
        """Apply the enacted policy and check win conditions."""
        if policy.policy_type == PolicyType.SUSTAINABLE:
            self.enacted_sustainable += 1
        else:
            self.enacted_exploiter += 1

        self.enacted_policies.append(policy.to_dict())
        self.election_tracker = 0

        result: dict = {
            "enacted_policy": policy.to_dict(),
            "sustainable_count": self.enacted_sustainable,
            "exploiter_count": self.enacted_exploiter,
        }

        winner = self.check_winner()
        if winner:
            self.phase = Phase.GAME_OVER
            self.winner = winner
            result["winner"] = winner
        else:
            self._advance_turn()
            self.phase = Phase.NOMINATION
            result["next_leader"] = self.leader

        return result

    def _force_enact_top_card(self) -> dict:
        """After 3 failed elections, enact the top card of the draw pile."""
        self._refill_if_needed(1)
        forced = self.draw_pile.pop()
        self.election_tracker = 0
        return self._resolve_enacted(forced)

    def _advance_turn(self):
        self.turn_index += 1
        self.nominated_vice = None
        self.votes.clear()

    def _refill_if_needed(self, count: int):
        """Shuffle the discard pile back in if the draw pile is too small."""
        if len(self.draw_pile) < count:
            self.draw_pile.extend(self.discard_pile)
            self.discard_pile.clear()
            shuffle_deck(self.draw_pile)

    # ------------------------------------------------------------------
    # Win condition
    # ------------------------------------------------------------------

    def check_winner(self) -> Optional[str]:
        if self.enacted_sustainable >= SUSTAINABLE_WIN_COUNT:
            return "reformers"
        if self.enacted_exploiter >= EXPLOITER_WIN_COUNT:
            return "exploiters"
        return None

    # ------------------------------------------------------------------
    # Summary / state queries
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        return {
            "winner": self.winner,
            "enacted_policies": self.enacted_policies,
            "sustainable_count": self.enacted_sustainable,
            "exploiter_count": self.enacted_exploiter,
            "roles": {pid: role.value for pid, role in self.roles.items()},
        }

    def get_round_info(self) -> dict:
        """Current round state for the frontend."""
        return {
            "phase": self.phase.value,
            "leader": self.leader,
            "nominated_vice": self.nominated_vice,
            "turn_index": self.turn_index,
            "sustainable_count": self.enacted_sustainable,
            "exploiter_count": self.enacted_exploiter,
            "election_tracker": self.election_tracker,
        }