import pytest

pytestmark = [pytest.mark.costs]


def _make_questions():
    return {
        "refund": {
            "type": "noul",
            "instructions": "Is the user requesting a refund?",
            "criteria": {
                "true": "The user explicitly asks for a refund or their money back.",
                "false": "The user does not ask for a refund.",
            },
        }
    }


STRING_STATE = "I want a refund. This product is broken and I need my money back."
OBJECT_STATE = {
    "title": "Refund request",
    "body": "This product is broken and I need my money back.",
    "tags": ["refund", "broken"],
}
ARRAY_STATE = [
    {"role": "user", "content": "This product is broken."},
    {"role": "assistant", "content": "I'm sorry to hear that."},
    {"role": "user", "content": "I need a refund."},
]


@pytest.mark.costs
def test_state_format_string(jev_call):
    result = jev_call(STRING_STATE, _make_questions())
    answer = result["answers"]["refund"]
    assert answer["type"] == "noul"
    assert 0.0 <= answer["noul"] <= 1.0


@pytest.mark.costs
def test_state_format_object(jev_call):
    result = jev_call(OBJECT_STATE, _make_questions())
    answer = result["answers"]["refund"]
    assert answer["type"] == "noul"
    # Named fields should preserve enough context for a clear refund request.
    assert answer["noul"] > 0.7


@pytest.mark.costs
def test_state_format_array(jev_call):
    result = jev_call(ARRAY_STATE, _make_questions())
    answer = result["answers"]["refund"]
    assert answer["type"] == "noul"
    # Conversation sequence awareness should surface the final refund request.
    assert answer["noul"] > 0.7


@pytest.mark.costs
def test_all_formats_answer_same_question(jev_call):
    for state in (STRING_STATE, OBJECT_STATE, ARRAY_STATE):
        result = jev_call(state, _make_questions())
        assert "refund" in result["answers"]
        assert result["answers"]["refund"]["type"] == "noul"
