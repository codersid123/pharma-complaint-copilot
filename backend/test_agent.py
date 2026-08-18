import json
from app.extract import extract_text
from app.agent import run_agent

print("=" * 60)
print("TEST 1 — extraction from PDF")
with open("../samples/sample1.pdf", "rb") as f:
    text = extract_text("sample1.pdf", f.read())
r1 = run_agent(raw_text=text)
print(json.dumps(r1, indent=2))

form = r1["patch"]["updates"]

print("=" * 60)
print("TEST 2 — modify via chat")
r2 = run_agent(user_message="change the severity to Critical, this is serious",
               current_form=form)
print(json.dumps(r2, indent=2))

print("=" * 60)
print("TEST 3 — append to description")
r3 = run_agent(user_message="add that two pharmacies returned the stock",
               current_form=form)
print(json.dumps(r3["patch"]["updates"], indent=2))

print("=" * 60)
print("TEST 4 — question, not a change")
r4 = run_agent(user_message="what is the expiry date on this batch?",
               current_form=form)
print(r4["assistant_message"])