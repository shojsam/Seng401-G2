from enum import Enum

from .roles import Role, assign_roles, get_exploiter_ids
from .deck import PolicyCard, PolicyType, deal_hands
from .voting import Vote, resolve_votes


class Phase(str, Enum):
    LOBBY = "lobby"
    ROLE_REVEAL = "role_reveal"
    PROPOSAL = "proposal"
    DISCUSSION = "discussion"
    VOTING = "voting"
    RESOLUTION = "resolution"
    GAME_OVER = "game_over"


# Win conditions: number of enacted policies needed to win
SUSTAINABLE_WIN_COUNT = 5
EXPLOITER_WIN_COUNT = 4


class GameState:
    """Holds all mutable state for a single game session."""

    def __init__(self, player_ids: list[str]):
        self.player_ids = player_ids
        self.roles: dict[str, Role] = {}
        self.hands: dict[str, list[PolicyCard]] = {}
        self.phase = Phase.LOBBY
        self.turn_index = 0
        self.current_policy: PolicyCard | None = None
        self.votes: dict[str, Vote] = {}
        self.enacted_sustainable = 0
        self.enacted_exploiter = 0
        self.enacted_policies: list[dict] = []
        self.winner: str | None = None

    @property
    def current_player(self) -> str:
        return self.player_ids[self.turn_index % len(self.player_ids)]

    def start_game(self) -> dict:
        """Assign roles and deal cards based on role."""
        self.roles = assign_roles(self.player_ids)
        self.hands = deal_hands(
            {pid: role.value for pid, role in self.roles.items()}
        )
        self.phase = Phase.ROLE_REVEAL
        return {
            "roles": {pid: role.value for pid, role in self.roles.items()},
            "exploiter_ids": get_exploiter_ids(self.roles),
        }

    def get_hand(self, player_id: str) -> list[dict]:
        """Return the card dicts for a player's current hand."""
        return [card.to_dict() for card in self.hands.get(player_id, [])]

    def propose_policy(self, player_id: str, card_index: int) -> PolicyCard:
        """Current player selects a card from their hand to propose."""
        hand = self.hands.get(player_id, [])
        if card_index < 0 or card_index >= len(hand):
            raise ValueError("Invalid card index")
        self.current_policy = hand.pop(card_index)
        self.votes.clear()
        self.phase = Phase.PROPOSAL
        return self.current_policy

    def begin_discussion(self):
        """Move to the discussion phase."""
        self.phase = Phase.DISCUSSION

    def begin_voting(self):
        """Move to the voting phase."""
        self.phase = Phase.VOTING

    def cast_vote(self, player_id: str, vote: Vote) -> bool:
        """Record a vote. Returns True if all votes are in."""
        self.votes[player_id] = vote
        return len(self.votes) == len(self.player_ids)

    def resolve_round(self) -> dict:
        """Resolve the vote and update the game state."""
        self.phase = Phase.RESOLUTION
        approved = resolve_votes(self.votes)

        result = {
            "approved": approved,
            "votes": {pid: v.value for pid, v in self.votes.items()},
            "policy": self.current_policy.to_dict() if self.current_policy else None,
        }

        if approved and self.current_policy:
            if self.current_policy.policy_type == PolicyType.SUSTAINABLE:
                self.enacted_sustainable += 1
            else:
                self.enacted_exploiter += 1
            self.enacted_policies.append(self.current_policy.to_dict())

        self.current_policy = None
        self.turn_index += 1

        # Check win conditions
        winner = self.check_winner()
        if winner:
            self.phase = Phase.GAME_OVER
            self.winner = winner
            result["winner"] = winner

        return result

    def check_winner(self) -> str | None:
        if self.enacted_sustainable >= SUSTAINABLE_WIN_COUNT:
            return "reformers"
        if self.enacted_exploiter >= EXPLOITER_WIN_COUNT:
            return "exploiters"
        return None

    def get_summary(self) -> dict:
        return {
            "winner": self.winner,
            "enacted_policies": self.enacted_policies,
            "sustainable_count": self.enacted_sustainable,
            "exploiter_count": self.enacted_exploiter,
            "roles": {pid: role.value for pid, role in self.roles.items()},
        }
