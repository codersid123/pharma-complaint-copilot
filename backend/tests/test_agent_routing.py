import pytest

from app.agent import route_intent

from .conftest import FakeLLM, make_llms


def test_raw_text_routes_to_extract_without_calling_llm():
    fast = FakeLLM({}, default="query")
    out = route_intent({"raw_text": "a document"}, make_llms(fast=fast))
    assert out == {"intent": "extract"}
    assert fast.prompts == []  # decided in Python, not by the LLM


def test_router_prompt_never_offers_extract():
    fast = FakeLLM({}, default="modify")
    route_intent({"user_message": "the batch number is MET-9012"}, make_llms(fast=fast))
    prompt = fast.prompts[0]
    assert "Never answer \"extract\"" in prompt
    assert "MET-9012" in prompt


@pytest.mark.parametrize("reply, expected", [
    ("modify", "modify"),
    ("Clarify.", "clarify"),
    ("  QUERY\n", "query"),
    ("extract", "modify"),      # extract is not allowed from chat
    ("banana", "modify"),       # anything unknown falls back to modify
])
def test_llm_answer_mapping(reply, expected):
    out = route_intent({"user_message": "hi"}, make_llms(fast=FakeLLM({}, default=reply)))
    assert out["intent"] == expected