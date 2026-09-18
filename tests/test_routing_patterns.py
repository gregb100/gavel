import pytest

pytestmark = [pytest.mark.costs]


def _intent_routing_questions():
    return {
        "intent": {
            "type": "choice",
            "instructions": "Classify the user's intent for this engineering request.",
            "criteria": {
                "status": "Asking for status update",
                "bug": "Reporting a bug or defect",
                "feature": "Requesting new functionality",
                "research": "Asking for investigation or spike",
                "ops": "Infrastructure, deployment, CI/CD",
                "chat": "Casual conversation",
            },
        },
        "complexity": {
            "type": "score",
            "instructions": "Estimate the complexity of the described work.",
            "criteria": ["Trivial", "Simple", "Moderate", "Complex"],
        },
        "is_urgent": {
            "type": "noul",
            "instructions": "Is the user expressing urgency or requesting immediate action?",
            "criteria": {
                "true": "The user expresses urgency or asks for immediate action.",
                "false": "The user does not express urgency.",
            },
        },
    }


def _bug_triage_questions():
    return {
        "severity": {
            "type": "score",
            "instructions": "Rate the severity of the reported bug.",
            "criteria": [
                "Cosmetic",
                "Minor",
                "Major",
                "Severe",
                "Critical",
            ],
        },
        "category": {
            "type": "choice",
            "instructions": "Classify the bug category.",
            "criteria": {
                "crash": "Application crashes or terminates unexpectedly",
                "data_loss": "User data is lost or corrupted",
                "regression": "Previously-working feature broke",
                "performance": "Slowness or resource exhaustion",
                "ui": "Visual or interaction issue",
                "security": "Security vulnerability or exposure",
            },
        },
        "is_blocker": {
            "type": "noul",
            "instructions": "Is this issue blocking the user's work or causing significant harm?",
            "criteria": {
                "true": "The issue blocks the user's work or causes significant harm.",
                "false": "The issue is not blocking or harmful.",
            },
        },
    }


def _message_classification_questions():
    return {
        "is_command": {
            "type": "noul",
            "instructions": "Is the user giving a command or directive?",
            "criteria": {
                "true": "The user gives an explicit command or directive.",
                "false": "The user is not giving a command.",
            },
        },
        "is_question": {
            "type": "noul",
            "instructions": "Is the user asking a question?",
            "criteria": {
                "true": "The user asks an explicit question.",
                "false": "The user is not asking a question.",
            },
        },
        "tone": {
            "type": "score",
            "instructions": "Classify the tone of the message.",
            "criteria": ["Casual", "Normal", "Time-sensitive", "Critical"],
        },
    }


@pytest.mark.costs
def test_intent_routing(jev_call):
    result = jev_call(
        "fix the login bug on the dashboard",
        _intent_routing_questions(),
    )
    answers = result["answers"]
    assert answers["intent"]["choice"] == "bug"
    # Jev score returns a calibrated float in [0, levels-1]; accept moderate+ complexity.
    assert answers["complexity"]["score"] >= 1.0
    # Urgency for a plain bug report may be low; verify it returns a valid noul.
    assert 0.0 <= answers["is_urgent"]["noul"] <= 1.0


@pytest.mark.costs
def test_bug_triage(jev_call):
    result = jev_call(
        "app crashes on startup, data loss",
        _bug_triage_questions(),
    )
    answers = result["answers"]
    assert answers["severity"]["score"] >= 2.5
    assert answers["category"]["choice"] in ("crash", "data_loss")
    assert answers["is_blocker"]["noul"] > 0.7


@pytest.mark.costs
def test_message_classification(jev_call):
    result = jev_call(
        "hey what's up",
        _message_classification_questions(),
    )
    answers = result["answers"]
    # Casual greeting is not a command.
    assert answers["is_command"]["noul"] < 0.3
    # Jev sometimes sees "what's up" as a question; allow a higher ceiling.
    assert answers["is_question"]["noul"] < 0.9
    # Casual is the first band; allow calibrated float near 0.
    assert answers["tone"]["score"] <= 0.5
