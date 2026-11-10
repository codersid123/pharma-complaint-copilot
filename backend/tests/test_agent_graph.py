"""Whole-graph runs with a fake LLM: proves the nodes are wired correctly."""
import json

from app.agent import run_agent

from .conftest import FakeLLM, make_llms


def test_document_goes_extract_validate_risk():
    reasoning = FakeLLM({
        "Extract complaint details": json.dumps(
            {"customer_name": "Acme", "complaint_description": "Cracked tablets"}),
        "risk assessor": json.dumps({"level": "Major", "score": 60, "rationale": "r"}),
    })
    out = run_agent(raw_text="a document", llms=make_llms(reasoning=reasoning))
    assert out["patch"]["updates"]["customer_name"] == "Acme"
    assert "batch_number" in out["missing_fields"]
    assert out["risk"]["level"] == "Major"


def test_query_does_not_change_the_form():
    fast = FakeLLM({}, default="query")
    reasoning = FakeLLM({}, default="The batch is B-1.")
    out = run_agent(user_message="what is the batch?", current_form={"batch_number": "B-1"},
                    llms=make_llms(fast=fast, reasoning=reasoning))
    assert out["patch"] == {"updates": {}, "clear": []}
    assert out["assistant_message"] == "The batch is B-1."
    assert out["risk"] is None


def test_clarify_asks_a_question():
    fast = FakeLLM({"Classify": "clarify"}, default="Which date do you mean?")
    out = run_agent(user_message="change the date", llms=make_llms(fast=fast))
    assert out["assistant_message"] == "Which date do you mean?"
