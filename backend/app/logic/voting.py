from enum import Enum


class Vote(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


def resolve_votes(votes: dict[str, Vote]) -> bool:
    """Return True if the policy is approved (strict majority)."""
    approve_count = sum(1 for v in votes.values() if v == Vote.APPROVE)
    reject_count = sum(1 for v in votes.values() if v == Vote.REJECT)
    return approve_count > reject_count
