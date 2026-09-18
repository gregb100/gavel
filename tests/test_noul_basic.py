import pytest

pytestmark = [pytest.mark.costs]


def _noul_q():
    return {
        "refund_requested": {
            "type": "noul",
            "instructions": "Evaluate whether the user is clearly requesting a refund.",
            "criteria": {
                "true": "The user explicitly asks for a refund or their money back.",
                "false": "The user does not ask for a refund.",
            },
        }
    }


@pytest.mark.costs
def test_noul_clear_true(jev_call):
    result = jev_call("I want a refund.", _noul_q())
    answer = result["answers"]["refund_requested"]
    assert answer["type"] == "noul"
    assert answer["noul"] > 0.8


@pytest.mark.costs
def test_noul_clear_false(jev_call):
    result = jev_call("Great product! I love it.", _noul_q())
    answer = result["answers"]["refund_requested"]
    assert answer["type"] == "noul"
    assert answer["noul"] < 0.2


@pytest.mark.costs
def test_noul_ambiguous(jev_call):
    result = jev_call("This isn't what I expected.", _noul_q())
    answer = result["answers"]["refund_requested"]
    assert answer["type"] == "noul"
    # Jev tends strongly toward the negative class for ambiguous inputs.
    assert 0.0 <= answer["noul"] < 0.75


@pytest.mark.costs
def test_noul_missing_criteria(jev_call):
    questions = {
        "refund_requested": {
            "type": "noul",
            "instructions": "Is the user requesting a refund?",
            "criteria": {
                "true": "The user explicitly asks for a refund.",
                "false": "The user does not ask for a refund.",
            },
        }
    }
    result = jev_call("I want my money back.", questions)
    answer = result["answers"]["refund_requested"]
    assert answer["type"] == "noul"
    assert isinstance(answer["noul"], float)
    assert 0.0 <= answer["noul"] <= 1.0
