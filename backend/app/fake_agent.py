import time
from .schemas import AgentResponse, FormPatch, RiskAssessment

REQUIRED = ["customer_name", "product_name", "batch_number",
            "complaint_type", "complaint_description", "initial_severity"]

FAKE_EXTRACTION = {
    "complaint_source": "Email",
    "customer_name": "MedLife Distributors Pvt Ltd",
    "product_name": "Paracetamol IP Tablets",
    "product_strength": "500 mg",
    "batch_number": "APX-2451",
    "manufacturing_date": "2025-03-01",
    "expiry_date": "2027-02-28",
    "quantity_affected": "240 strips",
    "complaint_type": "Product Quality",
    "complaint_date": "2026-08-12",
    "complaint_description": "Brown discolouration and chalky surface deposit "
                             "observed on tablets. Stock returned by two pharmacies.",
    "initial_severity": "Major",
    "priority": "High",
}

def missing(form: dict):
    return [f for f in REQUIRED if not form.get(f)]

def fake_extract() -> AgentResponse:
    time.sleep(1.5)
    return AgentResponse(
        patch=FormPatch(updates=FAKE_EXTRACTION),
        assistant_message="I extracted 13 fields from the document. Please review.",
        missing_fields=[],
        risk=RiskAssessment(
            level="Major",
            score=62,
            rationale="Visual defect affecting a marketed oral solid dosage form; "
                      "no immediate patient safety signal reported.",
            recommended_action="Initiate investigation within 5 working days. "
                               "Retain samples from batch APX-2451."))

def fake_modify(msg: str, form: dict) -> AgentResponse:
    updates = {}
    low = msg.lower()
    if "critical" in low:
        updates = {"initial_severity": "Critical", "priority": "High"}
    elif "batch" in low:
        updates = {"batch_number": "APX-2451"}
    merged = {**form, **updates}
    return AgentResponse(
        patch=FormPatch(updates=updates),
        assistant_message=f"Updated: {', '.join(updates) or 'nothing yet — this is a stub'}.",
        missing_fields=missing(merged))