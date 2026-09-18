import pytest

pytestmark = [pytest.mark.costs, pytest.mark.slow]


def _simple_q():
    return {
        "refund": {
            "type": "noul",
            "instructions": "Is the user asking for a refund?",
            "criteria": {
                "true": "The user explicitly asks for a refund.",
                "false": "The user does not ask for a refund.",
            },
        }
    }


def _five_q():
    return {
        "refund": {"type": "noul", "instructions": "Is the user asking for a refund?"},
        "intent": {
            "type": "choice",
            "instructions": "Classify intent.",
            "criteria": {
                "billing": "billing issue",
                "technical": "technical issue",
                "other": "other",
            },
        },
        "anger": {
            "type": "score",
            "instructions": "Rate anger.",
            "criteria": ["Calm", "Frustrated", "Angry"],
        },
        "satisfied": {
            "type": "noul",
            "instructions": "Is the user satisfied?",
            "criteria": {
                "true": "The user expresses clear satisfaction.",
                "false": "The user is not clearly satisfied.",
            },
        },
        "urgent": {
            "type": "choice",
            "instructions": "Is the tone urgent?",
            "criteria": {"urgent": "urgent", "normal": "normal", "other": "other"},
        },
    }


@pytest.mark.costs
@pytest.mark.slow
def test_perf_single_question(time_call):
    _, elapsed = time_call("I want a refund.", _simple_q())
    assert elapsed < 1.0, f"Single-question call took {elapsed:.2f}s"


@pytest.mark.costs
@pytest.mark.slow
def test_perf_five_questions(time_call):
    _, elapsed = time_call(
        "I'm furious. I want a refund because the app crashed and double charged me.",
        _five_q(),
    )
    assert elapsed < 2.0, f"Five-question call took {elapsed:.2f}s"
