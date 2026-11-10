"""Build samples/complaints_bulk.xlsx: 40 rows, 5 of them deliberately bad.

    python scripts/make_bulk_sample.py

Headers use real-world spellings ("Batch No", "Mfg Date", "Qty") on purpose,
to exercise the importer's header mapping.
"""
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parents[2] / "samples" / "complaints_bulk.xlsx"

PRODUCTS = [("Paracetamol IP Tablets", "500 mg", "PCM"), ("Amoxicillin Capsules", "250 mg", "AMX"),
            ("Cetirizine Tablets", "10 mg", "CTZ"), ("Pantoprazole Tablets", "40 mg", "PAN"),
            ("Ondansetron Injection", "2 mg/ml", "OND")]
CUSTOMERS = ["Noble Chemists, Nagpur", "Lifeline Hospital, Indore", "Shree Medicals, Surat",
             "Metro Pharmacy, Kolkata", "CareWell Distributors, Jaipur"]
ISSUES = [("Product Quality", "Major", "Tablets crumbling when pressed out of blister."),
          ("Packaging", "Minor", "Carton label peeling; strips intact."),
          ("Labelling", "Major", "Strength on strip differs from carton."),
          ("Contamination", "Critical", "Visible particulate matter in ampoules."),
          ("Product Quality", "Minor", "Faint odour noticed on opening bottle.")]
DATE_STYLES = ["%Y-%m-%d", "%d/%m/%Y", "%d %b %Y"]  # mixed on purpose

rnd = random.Random(7)
rows = []
for i in range(35):
    name, strength, code = rnd.choice(PRODUCTS)
    ctype, sev, desc = rnd.choice(ISSUES)
    mfg = date(2025, 1, 1) + timedelta(days=rnd.randint(0, 400))
    style = rnd.choice(DATE_STYLES)
    rows.append({
        "Source": rnd.choice(["Email", "Phone", "Distributor Portal"]),
        "Customer": rnd.choice(CUSTOMERS),
        "Product": name,
        "Strength": strength,
        "Batch No": f"{code}-{5000 + i}",
        "Mfg Date": mfg.strftime(style),
        "Exp. Date": (mfg + timedelta(days=730)).strftime(style),
        "Qty": f"{rnd.randint(1, 30) * 10} units",
        "Complaint Type": ctype,
        "Complaint Date": (date(2026, 8, 1) + timedelta(days=rnd.randint(0, 90))).strftime(style),
        "Description": desc,
        "Severity": sev.lower() if i % 4 == 0 else sev,  # some lowercase: importer fixes casing
        "Priority": {"Critical": "High", "Major": "Medium", "Minor": "Low"}[sev],
    })

good = rows[0]
bad = [
    {**good, "Batch No": "", "Description": "Row with no batch number."},           # required
    {**good, "Batch No": "PCM-9001", "Exp. Date": "sometime next year"},             # bad date
    {**good, "Batch No": "PCM-9002", "Severity": "Severe"},                          # bad enum
    {**good, "Batch No": "PCM-9003", "Product": ""},                                 # required
    dict(good),                                                                      # duplicate of row 2
]
rows.extend(bad)

pd.DataFrame(rows).to_excel(OUT, index=False)
print(f"Wrote {len(rows)} rows to {OUT}")
