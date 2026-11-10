"""Compare what the model extracted with the correct answer, field by field.

Each comparison gives one outcome:
  correct        expected a value, got the same value
  correct_empty  expected nothing (not in the document), got nothing
  wrong          expected a value, got a different one
  missed         expected a value, got nothing
  invented       expected nothing, but the model filled something in (hallucination)
"""
import re

from app.dates import parse_date

SCORED_FIELDS = [
    "customer_name", "product_name", "product_strength", "batch_number",
    "manufacturing_date", "expiry_date", "quantity_affected", "complaint_date",
    "complaint_type", "initial_severity",
]
DATE_FIELDS = {"manufacturing_date", "expiry_date", "complaint_date"}
EXACT_FIELDS = {"complaint_type", "initial_severity"}
# Words that don't change who/what is meant: "MedLife Distributors Pvt Ltd" == "MedLife Distributors".
FILLER = {"pvt", "ltd", "limited", "private", "the", "inc", "llp", "co", "and", "of"}


def _empty(v) -> bool:
    return v is None or str(v).strip().lower() in ("", "null", "none", "n/a", "na")


def _tokens(v) -> set:
    words = re.sub(r"[^a-z0-9]+", " ", str(v).lower()).split()
    return {w for w in words if w not in FILLER}


def _same_batch(a, b) -> bool:
    norm = lambda s: re.sub(r"[^A-Z0-9]", "", str(s).upper())  # noqa: E731
    return norm(a) == norm(b)


def _same_date(a, b) -> bool:
    try:
        return parse_date(a) == parse_date(b)
    except ValueError:
        return False


def _same_text(expected, got) -> bool:
    """Lenient match for names and amounts: one side's words all appear in the other."""
    e, g = _tokens(expected), _tokens(got)
    return bool(e) and bool(g) and (e <= g or g <= e)


def compare(field: str, expected, got) -> str:
    if _empty(expected):
        return "correct_empty" if _empty(got) else "invented"
    if _empty(got):
        return "missed"
    if field == "batch_number":
        same = _same_batch(expected, got)
    elif field in DATE_FIELDS:
        same = _same_date(expected, got)
    elif field in EXACT_FIELDS:
        same = str(expected).strip().lower() == str(got).strip().lower()
    else:
        same = _same_text(expected, got)
    return "correct" if same else "wrong"


def summarise(per_doc: list) -> dict:
    """per_doc: [{"outcomes": {field: outcome}, ...}] -> accuracy per field + totals."""
    fields = {}
    for f in SCORED_FIELDS:
        outs = [d["outcomes"][f] for d in per_doc]
        right = sum(o in ("correct", "correct_empty") for o in outs)
        fields[f] = {"accuracy": right / len(outs),
                     **{k: outs.count(k) for k in
                        ("correct", "correct_empty", "wrong", "missed", "invented")}}
    all_outs = [o for d in per_doc for o in d["outcomes"].values()]
    should_be_empty = sum(o in ("correct_empty", "invented") for o in all_outs)
    return {
        "fields": fields,
        "overall_accuracy": sum(o in ("correct", "correct_empty") for o in all_outs) / len(all_outs),
        "invented": all_outs.count("invented"),
        "hallucination_rate": (all_outs.count("invented") / should_be_empty) if should_be_empty else 0.0,
        "risk_agreement": (sum(d["risk_agrees"] for d in per_doc) / len(per_doc)),
        "errors": sum(bool(d.get("error")) for d in per_doc),
    }
