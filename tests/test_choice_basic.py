import pytest

pytestmark = [pytest.mark.costs]


def _routing_q():
    return {
        "intent": {
            "type": "choice",
            "instructions": "Classify the user's support intent.",
            "criteria": {
                "billing": "Issues with payments, charges, invoices, refunds",
                "technical": "Bugs, crashes, errors, app behavior",
                "account": "Login, password, profile, settings",
                "other": "Anything that does not match billing, technical, or account",
            },
        }
    }


@pytest.mark.costs
def test_choice_clear_match(jev_call):
    result = jev_call("I was double charged on my invoice.", _routing_q())
    answer = result["answers"]["intent"]
    assert answer["type"] == "choice"
    assert answer["choice"] == "billing"
    assert answer["confidence"] > 0.7


@pytest.mark.costs
def test_choice_multi_plausible(jev_call):
    result = jev_call(
        "my payment failed and the app crashed right after.", _routing_q()
    )
    answer = result["answers"]["intent"]
    assert answer["type"] == "choice"
    probs = answer["probabilities"]
    assert probs.get("billing", 0) > 0.15
    assert probs.get("technical", 0) > 0.15
    assert answer["confidence"] < 0.9


@pytest.mark.costs
def test_choice_no_match_goes_other(jev_call):
    result = jev_call("what's your favorite color?", _routing_q())
    answer = result["answers"]["intent"]
    assert answer["type"] == "choice"
    assert answer["choice"] == "other" or answer["confidence"] < 0.5


@pytest.mark.costs
def test_choice_other_can_win(jev_call):
    questions = {
        "intent": {
            "type": "choice",
            "instructions": "Classify the user's support intent.",
            "criteria": {
                "bug": "User reports a defect or bug",
                "feature": "User requests new capability",
                "other": "Anything not a bug or feature request",
            },
        }
    }
    result = jev_call("The weather is nice today.", questions)
    answer = result["answers"]["intent"]
    assert answer["type"] == "choice"
    assert "other" in answer["probabilities"]
    assert answer["choice"] == "other"
