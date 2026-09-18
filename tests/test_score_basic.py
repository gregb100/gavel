import pytest

pytestmark = [pytest.mark.costs]


def _anger_q():
    return {
        "anger": {
            "type": "score",
            "instructions": "Rate the user's emotional intensity from Calm to Very angry.",
            "criteria": ["Calm", "Frustrated", "Very angry"],
        }
    }


@pytest.mark.costs
def test_score_clear_high(jev_call):
    result = jev_call("I'm furious and want to cancel my subscription.", _anger_q())
    answer = result["answers"]["anger"]
    assert answer["type"] == "score"
    assert answer["score"] >= 0.66
    assert "Very angry" in answer["legend"].values()


@pytest.mark.costs
def test_score_boundary_mid(jev_call):
    result = jev_call("I'm a bit annoyed but it's not a big deal.", _anger_q())
    answer = result["answers"]["anger"]
    assert answer["type"] == "score"
    # Floating-point score on the anger scale; confidence stays moderate-to-low for soft boundary.
    assert 0.0 <= answer["score"] <= 2.0
    assert answer["confidence"] < 0.9


@pytest.mark.costs
def test_score_clear_low(jev_call):
    result = jev_call("thanks for the help, much appreciated!", _anger_q())
    answer = result["answers"]["anger"]
    assert answer["type"] == "score"
    assert answer["score"] <= 0.33
    assert "Calm" in answer["legend"].values()


@pytest.mark.costs
def test_score_two_levels(jev_call):
    questions = {
        "binary": {
            "type": "score",
            "instructions": "Is the statement positive or negative?",
            "criteria": ["Negative", "Positive"],
        }
    }
    result = jev_call("This is terrible.", questions)
    answer = result["answers"]["binary"]
    assert answer["type"] == "score"
    assert 0.0 <= answer["score"] <= 1.0
    assert set(answer["legend"].values()) == {"Negative", "Positive"}
