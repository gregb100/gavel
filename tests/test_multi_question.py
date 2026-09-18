import pytest

pytestmark = [pytest.mark.costs]


def _mixed_questions():
    return {
        "refund": {
            "type": "noul",
            "instructions": "Is the user asking for a refund?",
            "criteria": {
                "true": "The user explicitly asks for a refund or their money back.",
                "false": "The user does not ask for a refund.",
            },
        },
        "intent": {
            "type": "choice",
            "instructions": "Classify the primary support intent.",
            "criteria": {
                "billing": "Payment, charge, invoice, refund",
                "technical": "Crash, bug, error",
                "account": "Login, password",
                "other": "None of the above",
            },
        },
        "anger": {
            "type": "score",
            "instructions": "Rate anger from Calm to Very angry.",
            "criteria": ["Calm", "Frustrated", "Very angry"],
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
            "criteria": {
                "urgent": "Demands immediate action",
                "normal": "Routine request",
                "other": "Unclear",
            },
        },
    }


@pytest.mark.costs
def test_multi_question_all_answered(jev_call):
    state = "I'm furious. I want a refund because your app crashed and double charged me."
    result = jev_call(state, _mixed_questions())
    answers = result["answers"]
    assert set(answers.keys()) == set(_mixed_questions().keys())
    for answer in answers.values():
        assert answer["type"] in ("noul", "choice", "score")


@pytest.mark.costs
def test_multi_question_no_cross_contamination(jev_call):
    result = jev_call(
        "I'm furious. I want a refund because your app crashed and double charged me.",
        _mixed_questions(),
    )
    answers = result["answers"]
    assert answers["refund"]["type"] == "noul"
    assert answers["intent"]["type"] == "choice"
    assert answers["anger"]["type"] == "score"

    # Changing one question should not flip unrelated answers unexpectedly.
    modified = _mixed_questions().copy()
    modified["refund"]["instructions"] = "Is the user asking to be contacted by phone?"
    modified["refund"]["criteria"] = {
        "true": "The user asks for a phone call.",
        "false": "The user does not ask for a phone call.",
    }


    result2 = jev_call(
        "I'm furious. I want a refund because your app crashed and double charged me.",
        modified,
    )
    answers2 = result2["answers"]
    # Other answers should stay in a sensible range despite the refund question being replaced.
    assert answers2["intent"]["choice"] in ("billing", "technical")
    assert answers2["anger"]["score"] >= 1


@pytest.mark.costs
def test_multi_question_latency_scaling(time_call):
    state = "I need help with my account."
    single_q = {
        "refund": {
            "type": "noul",
            "instructions": "Is the user asking for a refund?",
        }
    }
    _, single_elapsed = time_call(state, single_q)
    _, multi_elapsed = time_call(state, _mixed_questions())
    assert multi_elapsed < 4 * single_elapsed, (
        f"5-question call ({multi_elapsed:.2f}s) should be less than 4x single-question ({single_elapsed:.2f}s)"
    )
