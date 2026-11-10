from app.agent import REQUIRED, check_completeness

FULL = {k: "x" for k in REQUIRED}


def state(form, updates=None, clear=None):
    return {"current_form": form, "assistant_message": "Done.",
            "form_patch": {"updates": updates or {}, "clear": clear or []}}


def test_complete_form_has_no_missing_fields():
    out = check_completeness(state(FULL))
    assert out["missing_fields"] == []
    assert out["assistant_message"] == "Done."


def test_missing_fields_listed_and_mentioned():
    out = check_completeness(state({"customer_name": "Acme"}))
    assert "batch_number" in out["missing_fields"]
    assert "batch number" in out["assistant_message"]


def test_update_fills_a_missing_field():
    form = {**FULL, "batch_number": ""}
    out = check_completeness(state(form, updates={"batch_number": "B-1"}))
    assert out["missing_fields"] == []


def test_clear_makes_a_field_missing():
    out = check_completeness(state(FULL, clear=["batch_number"]))
    assert out["missing_fields"] == ["batch_number"]
