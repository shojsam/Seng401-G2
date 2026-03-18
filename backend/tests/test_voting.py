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

def test_no_votes_returns_false():
    votes = {}
    assert resolve_votes(votes) is False

def test_unanimous_reject():
    votes = {"p1": Vote.REJECT, "p2": Vote.REJECT}
    assert resolve_votes(votes) is False

def test_large_group_majority():
    votes = {
        "p1": Vote.APPROVE,
        "p2": Vote.APPROVE,
        "p3": Vote.APPROVE,
        "p4": Vote.REJECT,
        "p5": Vote.REJECT,
    }
    assert resolve_votes(votes) is True

def test_single_vote_approve():
    votes = {"p1": Vote.APPROVE}
    assert resolve_votes(votes) is True


def test_single_vote_reject():
    votes = {"p1": Vote.REJECT}
    assert resolve_votes(votes) is False

    