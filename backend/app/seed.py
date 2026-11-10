"""Fill an empty database with 50 realistic sample complaints.

    python -m app.seed           # only if the table is empty
    python -m app.seed --reset   # delete everything first, then seed

The same 50 rows every time (fixed random seed), so demos and screenshots
are repeatable.
"""
import random
import sys
from datetime import date, timedelta

from .db import get_sessionmaker
from .main import complaint_number
from .models import Complaint

PRODUCTS = [
    ("Paracetamol IP Tablets", "500 mg", "PCM"),
    ("Metformin Hydrochloride Tablets", "500 mg", "MET"),
    ("Amoxicillin Capsules", "250 mg", "AMX"),
    ("Atorvastatin Tablets", "10 mg", "ATV"),
    ("Ceftriaxone Injection", "1 g", "CFT"),
    ("Omeprazole Capsules", "20 mg", "OMZ"),
    ("Azithromycin Oral Suspension", "200 mg/5 ml", "AZT"),
    ("Insulin Glargine Injection", "100 IU/ml", "INS"),
]
CUSTOMERS = [
    "MedLife Distributors, Chennai", "Apollo Pharmacy, Hyderabad", "Wellness Chemists, Pune",
    "City Hospital, Bengaluru", "CarePlus Pharma, Mumbai", "Sunrise Clinic, Kochi",
    "HealthKart Retail, Delhi", "Green Cross Pharmacy, Vellore",
]
SOURCES = ["Email", "Phone", "Field Sales", "Distributor Portal", "Letter"]
# (type, severity, description)
ISSUES = [
    ("Product Quality", "Major", "Tablets found cracked and broken inside sealed blister strips."),
    ("Product Quality", "Major", "Brown discolouration and chalky deposit on tablet surface."),
    ("Product Quality", "Minor", "Slight variation in tablet colour between strips of the same batch."),
    ("Packaging", "Minor", "Outer carton crushed on arrival; primary packs intact."),
    ("Packaging", "Major", "Blister foil not sealed on several pockets; tablets exposed."),
    ("Labelling", "Major", "Expiry date on carton does not match expiry printed on strip."),
    ("Labelling", "Minor", "Batch number print smudged and hard to read on label."),
    ("Contamination", "Critical", "Black particles visible floating in reconstituted vial."),
    ("Contamination", "Critical", "Hair-like foreign fibre embedded in capsule shell."),
    ("Adverse Event", "Critical", "Patient reported rash and breathing difficulty after first dose."),
    ("Documentation", "Minor", "Certificate of analysis missing from consignment."),
]
PRIORITY = {"Critical": "High", "Major": "Medium", "Minor": "Low"}
RISK_SCORE = {"Critical": (85, 98), "Major": (55, 75), "Minor": (15, 35)}
STATUSES = ["Pending Triage"] * 6 + ["Under Investigation"] * 3 + ["Closed"]


def build_rows(n: int = 50, today: date = date(2026, 11, 10)) -> list:
    rnd = random.Random(42)
    rows = []
    for _ in range(n):
        product, strength, code = rnd.choice(PRODUCTS)
        ctype, severity, desc = rnd.choice(ISSUES)
        mfg = today - timedelta(days=rnd.randint(120, 700))
        lo, hi = RISK_SCORE[severity]
        rows.append(Complaint(
            complaint_source=rnd.choice(SOURCES),
            customer_name=rnd.choice(CUSTOMERS),
            product_name=product,
            product_strength=strength,
            batch_number=f"{code}-{rnd.randint(1000, 1030)}",  # narrow range -> some duplicates
            manufacturing_date=mfg,
            expiry_date=mfg + timedelta(days=730),
            quantity_affected=f"{rnd.randint(1, 50) * 10} units",
            complaint_type=ctype,
            complaint_date=today - timedelta(days=rnd.randint(0, 90)),
            complaint_description=desc,
            initial_severity=severity,
            priority=PRIORITY[severity],
            ai_risk_level=severity,
            ai_risk_score=rnd.randint(lo, hi),
            ai_risk_rationale=f"Seed data: {ctype.lower()} complaint classified {severity}.",
            status=rnd.choice(STATUSES),
        ))
    return rows


def seed(db, reset: bool = False) -> int:
    if reset:
        db.query(Complaint).delete()
    elif db.query(Complaint).count() > 0:
        return 0
    rows = build_rows()
    for c in rows:
        db.add(c)
        db.flush()
        c.complaint_number = complaint_number(c.id, c.complaint_date.year)
    db.commit()
    return len(rows)


if __name__ == "__main__":
    with get_sessionmaker()() as session:
        added = seed(session, reset="--reset" in sys.argv)
    print(f"Seeded {added} complaints." if added else "Table not empty; nothing seeded (use --reset).")
