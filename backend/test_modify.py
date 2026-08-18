import json
from app.agent import run_agent, route_intent

form = {
    "customer_name": "Wellness Chemists",
    "product_name": "Metformin",
    "product_strength": "500 mg",
    "batch_number": "",
    "manufacturing_date": "",
    "complaint_description": "Cracked and broken tablets in strips.",
}

msg = "the batch number is MET-9012 and it was manufactured in June 2025"

print("INTENT:", route_intent({"user_message": msg}))
print("---")
print(json.dumps(run_agent(user_message=msg, current_form=form), indent=2))