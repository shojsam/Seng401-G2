import pytest
from app.logic.roles import assign_roles, get_exploiter_ids, Role


def test_assign_roles_minimum_players():
    players = ["p1", "p2", "p3", "p4", "p5"]
    roles = assign_roles(players)
    assert len(roles) == 5
    exploiters = [p for p, r in roles.items() if r == Role.EXPLOITER]
    reformers = [p for p, r in roles.items() if r == Role.REFORMER]
    assert len(exploiters) == 2
    assert len(reformers) == 3


def test_reformers_always_outnumber_exploiters():
    for count in range(5, 11):
        players = [f"p{i}" for i in range(count)]
        roles = assign_roles(players)
        exploiters = sum(1 for r in roles.values() if r == Role.EXPLOITER)
        reformers = sum(1 for r in roles.values() if r == Role.REFORMER)
        assert reformers > exploiters


def test_too_few_players_raises():
    with pytest.raises(ValueError):
        assign_roles(["p1", "p2", "p3"])


def test_get_exploiter_ids():
    roles = {"p1": Role.REFORMER, "p2": Role.EXPLOITER, "p3": Role.REFORMER, "p4": Role.EXPLOITER, "p5": Role.REFORMER}
    assert set(get_exploiter_ids(roles)) == {"p2", "p4"}
