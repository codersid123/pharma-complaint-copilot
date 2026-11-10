import json

from app.agent import extract_fields, modify_fields

from .conftest import FakeLLM, make_llms


def run_modify(llm_reply: dict, form=None):
    llm = FakeLLM({}, default=json.dumps(llm_reply))
    return modify_fields({"user_message": "x", "current_form": form or {}},
                         make_llms(reasoning=llm))


def test_updates_only_contain_mentioned_fields():
    out = run_modify({"updates": {"batch_number": "B-2"}, "clear": []},
                     form={"customer_name": "Acme", "batch_number": "B-1"})
    assert out["form_patch"] == {"updates": {"batch_number": "B-2"}, "clear": []}


def test_clear_is_separate_from_updates():
    out = run_modify({"updates": {}, "clear": ["expiry_date"]})
    assert out["form_patch"]["clear"] == ["expiry_date"]


def test_unknown_keys_dropped():
    out = run_modify({"updates": {"colour": "red", "priority": "High"},
                      "clear": ["not_a_field"]})
    assert out["form_patch"] == {"updates": {"priority": "High"}, "clear": []}


def test_field_cannot_be_both_updated_and_cleared():
    out = run_modify({"updates": {"priority": "Low"}, "clear": ["priority"]})
    assert out["form_patch"] == {"updates": {"priority": "Low"}, "clear": []}


def test_bad_llm_shapes_do_not_crash():
    out = run_modify({"updates": "none", "clear": "priority"})
    assert out["form_patch"] == {"updates": {}, "clear": []}
    assert "rephrase" in out["assistant_message"]


def test_extract_drops_nulls_and_unknown_keys():
    reply = json.dumps({"customer_name": "Acme", "batch_number": None,
                        "expiry_date": "N/A", "colour": "red"})
    out = extract_fields({"raw_text": "doc"},
                         make_llms(reasoning=FakeLLM({}, default=reply)))
    assert out["form_patch"]["updates"] == {"customer_name": "Acme"}