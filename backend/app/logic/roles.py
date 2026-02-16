import random
from enum import Enum


class Role(str, Enum):
    REFORMER = "reformer"
    EXPLOITER = "exploiter"


# Maps player count to number of exploiters
ROLE_DISTRIBUTION = {
    5: 2,
    6: 2,
    7: 3,
    8: 3,
    9: 4,
    10: 4,
}


def assign_roles(player_ids: list[str]) -> dict[str, Role]:
    """Assign secret roles to players. Reformers always outnumber Exploiters."""
    count = len(player_ids)
    if count < 5:
        raise ValueError("Need at least 5 players")

    num_exploiters = ROLE_DISTRIBUTION.get(count, count // 3)
    shuffled = player_ids.copy()
    random.shuffle(shuffled)

    assignments = {}
    for i, pid in enumerate(shuffled):
        if i < num_exploiters:
            assignments[pid] = Role.EXPLOITER
        else:
            assignments[pid] = Role.REFORMER

    return assignments


def get_exploiter_ids(assignments: dict[str, Role]) -> list[str]:
    """Return the player IDs of all Exploiters."""
    return [pid for pid, role in assignments.items() if role == Role.EXPLOITER]
