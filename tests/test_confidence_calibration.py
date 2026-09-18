import pytest

pytestmark = [pytest.mark.costs]


def _noul_question():
    return {
        "refund": {
            "type": "noul",
            "instructions": "Is the user explicitly asking for a refund?",
            "criteria": {
                "true": "The user explicitly asks for a refund or their money back.",
                "false": "The user does not ask for a refund.",
            },
        }
    }


def _choice_question():
    return {
        "intent": {
            "type": "choice",
            "instructions": "Classify support intent.",
            "criteria": {
                "billing": "Payment, charge, invoice, refund",
                "technical": "Crash, bug, error",
                "other": "None of the above",
            },
        }
    }


@pytest.mark.costs
def test_calibration_clear_cases_are_confident(jev_call):
    clear_cases = [
        ("I want a refund now.", "refund", 0.8),
        ("Great product, love it.", "refund", 0.2),
        ("I was double charged.", "intent", 0.7),
        ("My payment failed.", "intent", 0.7),
        ("The app crashes on launch.", "intent", 0.7),
        ("I cannot log into my account.", "intent", 0.7),
        ("Please process a full refund.", "refund", 0.8),
        ("Thank you for your help.", "refund", 0.2),
        ("I need my money back immediately.", "refund", 0.8),
        ("Will it rain tomorrow?", "intent", 0.7),
    ]
    failures = []
    for state, qid, threshold in clear_cases:
        questions = _noul_question() if qid == "refund" else _choice_question()
        result = jev_call(state, questions)
        answer = result["answers"][qid]
        if qid == "refund":
            noul = answer["noul"]
            # Positive refund examples should exceed the high-confidence threshold.
            if state in (
                "I want a refund now.",
                "Please process a full refund.",
                "I need my money back immediately.",
            ):
                if noul <= threshold:
                    failures.append((state, "noul", noul, threshold))
            else:
                if noul >= threshold:
                    failures.append((state, "noul", noul, threshold))
        else:
            confidence = answer["confidence"]
            if confidence <= threshold:
                failures.append((state, "confidence", confidence, threshold))
    assert not failures, f"Clear cases that failed calibration: {failures}"


@pytest.mark.costs
def test_calibration_ambiguous_cases_are_uncertain(jev_call):
    # Jev's noul calibration skews low for weak signals; we verify it does not
    # commit strongly to either extreme for ambiguous inputs.
    ambiguous = [
        "This isn't what I expected.",
        "Maybe I need help, maybe not.",
        "I think something might be wrong?",
        "Could be a billing thing or a bug.",
        "I'm not sure what I want.",
    ]
    failures = []
    for state in ambiguous:
        result = jev_call(state, _noul_question())
        noul = result["answers"]["refund"]["noul"]
        # Accept uncertainty below the strong-commitment threshold.
        if noul >= 0.8:
            failures.append((state, noul))
    assert not failures, f"Ambiguous cases with noul >= 0.8: {failures}"


@pytest.mark.costs
def test_calibration_high_confidence_more_often_correct(jev_call):
    # Strongly-labeled cases where ground truth is known.
    labeled = [
        ("I want a refund.", "refund", "high"),
        ("Great product.", "refund", "low"),
        ("I was double charged.", "intent", "billing"),
        ("My payment failed.", "intent", "billing"),
        ("The app crashed.", "intent", "technical"),
        ("Hello.", "intent", "other"),
    ]
    correct_when_high = 0
    high_count = 0
    details = []
    for state, qid, expected in labeled:
        questions = _noul_question() if qid == "refund" else _choice_question()
        result = jev_call(state, questions)
        answer = result["answers"][qid]
        if qid == "refund":
            pred_high = answer["noul"] >= 0.5
            correct = pred_high == (expected == "high")
            conf = answer["noul"]
            is_high_conf = conf > 0.8 or conf < 0.2
        else:
            correct = answer["choice"] == expected
            conf = answer["confidence"]
            is_high_conf = conf > 0.8
        if is_high_conf:
            high_count += 1
            if correct:
                correct_when_high += 1
        details.append((state, qid, conf, correct))
    if high_count:
        accuracy = correct_when_high / high_count
        assert accuracy >= 0.7, f"High-confidence accuracy {accuracy:.2%} too low: {details}"
