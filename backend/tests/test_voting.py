from app.logic.voting import Vote, resolve_votes


def test_majority_approve():
    votes = {"p1": Vote.APPROVE, "p2": Vote.APPROVE, "p3": Vote.REJECT}
    assert resolve_votes(votes) is True


def test_majority_reject():
    votes = {"p1": Vote.REJECT, "p2": Vote.REJECT, "p3": Vote.APPROVE}
    assert resolve_votes(votes) is False


def test_tie_rejects():
    votes = {"p1": Vote.APPROVE, "p2": Vote.REJECT}
    assert resolve_votes(votes) is False


def test_unanimous_approve():
    votes = {"p1": Vote.APPROVE, "p2": Vote.APPROVE, "p3": Vote.APPROVE}
    assert resolve_votes(votes) is True
