import pytest
import urllib.error

pytestmark = [pytest.mark.costs]


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


@pytest.mark.costs
def test_edge_empty_state(jev_call):
    result = jev_call("", _simple_q())
    # The API should still return a structured answer, even if low-confidence.
    assert "answers" in result
    assert result["answers"]["refund"]["type"] == "noul"
    assert isinstance(result["answers"]["refund"]["noul"], float)


@pytest.mark.costs
def test_edge_long_state(jev_call):
    long_state = "word " * 6000  # ~30k characters
    result = jev_call(long_state, _simple_q(), timeout=30)
    assert "answers" in result
    assert result["answers"]["refund"]["type"] == "noul"


@pytest.mark.costs
def test_edge_bad_model_returns_error(call_with_status):
    payload, status = call_with_status("hello", _simple_q(), model="typesafe/nonexistent")
    assert status >= 400
    assert "error" in payload or "message" in payload


@pytest.mark.costs
def test_edge_missing_question_type(call_with_status):
    questions = {
        "refund": {
            "instructions": "Is the user asking for a refund?",
        }
    }
    payload, status = call_with_status("hello", questions)
    assert status >= 400


@pytest.mark.costs
def test_edge_empty_questions(call_with_status):
    payload, status = call_with_status("hello", {})
    # Empty questions is a malformed request; API should reject it.
    assert status >= 400 or ("answers" in payload and payload["answers"] == {})
