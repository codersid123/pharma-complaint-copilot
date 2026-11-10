"""The evaluation is only as good as its scoring rules, so the rules get tests too."""
import pytest

from app.agent import build_graph, extract_fields_structured
from app.schemas import ComplaintForm
from eval.scoring import compare, summarise

from .conftest import make_llms


@pytest.mark.parametrize("field, expected, got, outcome", [
    ("batch_number", "APX-2451", "apx 2451", "correct"),
    ("batch_number", "ATV-1244", "ATV-1180", "wrong"),
    ("batch_number", None, "MET-0001", "invented"),
    ("batch_number", None, "null", "correct_empty"),
    ("expiry_date", "2027-02-01", "February 2027", "correct"),
    ("complaint_date", "2026-09-05", "2026-05-09", "wrong"),     # US vs Indian order
    ("expiry_date", "2027-02-01", None, "missed"),
    ("customer_name", "MedLife Distributors Pvt Ltd", "MedLife Distributors", "correct"),
    ("customer_name", "City Hospital", "Ravi", "wrong"),
    ("initial_severity", "Critical", "critical", "correct"),
    ("initial_severity", "Critical", "Major", "wrong"),
])
def test_compare(field, expected, got, outcome):
    assert compare(field, expected, got) == outcome


def test_summary_counts_hallucinations_only_where_field_was_absent():
    docs = [{"outcomes": {**{f: "correct" for f in ["customer_name", "product_name",
             "product_strength", "manufacturing_date", "expiry_date", "quantity_affected",
             "complaint_date", "complaint_type", "initial_severity"]},
             "batch_number": "invented"}, "risk_agrees": True},
            {"outcomes": {**{f: "correct" for f in ["customer_name", "product_name",
             "product_strength", "manufacturing_date", "expiry_date", "quantity_affected",
             "complaint_date", "complaint_type", "initial_severity"]},
             "batch_number": "correct_empty"}, "risk_agrees": False}]
    s = summarise(docs)
    assert s["fields"]["batch_number"]["accuracy"] == 0.5
    assert s["hallucination_rate"] == 0.5       # 1 invented out of 2 absent fields
    assert s["risk_agreement"] == 0.5


class FakeStructured:
    """Mimics llm.with_structured_output(ComplaintForm): .invoke returns a model object."""

    def __init__(self, form):
        self.form = form
        self.schema = None

    def with_structured_output(self, schema):
        self.schema = schema
        return self

    def invoke(self, prompt):
        return self.form


def test_structured_extractor_uses_the_schema_and_drops_empties():
    fake = FakeStructured(ComplaintForm(customer_name="Acme", batch_number=None,
                                        initial_severity="Major"))
    out = extract_fields_structured({"raw_text": "doc"}, make_llms(reasoning=fake))
    assert fake.schema is ComplaintForm
    assert out["form_patch"]["updates"] == {"customer_name": "Acme", "initial_severity": "Major"}


def test_build_graph_rejects_unknown_mode():
    with pytest.raises(ValueError, match="EXTRACT_MODE"):
        build_graph(make_llms(), extract_mode="magic")
