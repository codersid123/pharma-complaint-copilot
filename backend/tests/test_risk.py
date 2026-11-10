import json

from app.agent import assess_risk

from .conftest import FakeLLM, make_llms

FORM = {"complaint_description": "Black particles found in vials"}


def run_risk(reply: str, form=FORM):
    llm = FakeLLM({}, default=reply)
    state = {"current_form": form, "form_patch": {"updates": {}, "clear": []}}
    return assess_risk(state, make_llms(reasoning=llm)), llm


def test_valid_risk():
    reply = json.dumps({"level": "Critical", "score": 92, "rationale": "r",
                        "recommended_action": "a"})
    out, _ = run_risk(reply)
    assert out["risk"] == {"level": "Critical", "score": 92, "rationale": "r",
                           "recommended_action": "a"}


def test_non_numeric_score_falls_back_to_50():
    out, _ = run_risk(json.dumps({"level": "Major", "score": "high"}))
    assert out["risk"]["score"] == 50


def test_no_description_means_no_risk_and_no_llm_call():
    out, llm = run_risk("{}", form={"customer_name": "Acme"})
    assert out == {"risk": None}
    assert llm.prompts == []


def test_missing_level_means_no_risk():
    out, _ = run_risk("not json at all")
    assert out == {"risk": None}
