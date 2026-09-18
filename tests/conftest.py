import os
import json
import urllib.request
import pytest

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"


@pytest.fixture
def jev_call():
    def _call(state, questions, model=MODEL, timeout=30):
        if not OPENROUTER_API_KEY:
            pytest.skip("OPENROUTER_API_KEY not set")
        body = json.dumps(
            {"model": model, "state": state, "questions": questions}
        ).encode()
        req = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())

    return _call


@pytest.fixture
def time_call():
    import time

    def _time(state, questions, model=MODEL, timeout=30):
        start = time.perf_counter()
        if not OPENROUTER_API_KEY:
            pytest.skip("OPENROUTER_API_KEY not set")
        body = json.dumps(
            {"model": model, "state": state, "questions": questions}
        ).encode()
        req = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read())
        elapsed = time.perf_counter() - start
        return result, elapsed

    return _time


@pytest.fixture
def call_with_status():
    def _call(state, questions, model=MODEL, timeout=30):
        if not OPENROUTER_API_KEY:
            pytest.skip("OPENROUTER_API_KEY not set")
        body = json.dumps(
            {"model": model, "state": state, "questions": questions}
        ).encode()
        req = urllib.request.Request(
            ENDPOINT,
            data=body,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read()), resp.status
        except urllib.error.HTTPError as e:
            body = e.read()
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {"raw": body.decode(errors="ignore")}
            return payload, e.code

    return _call
