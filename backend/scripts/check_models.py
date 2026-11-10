import os

import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GROQ_API_KEY")
print("Key loaded:", bool(key), "| starts with:", (key or "")[:7])

r = requests.get("https://api.groq.com/openai/v1/models",
                 headers={"Authorization": f"Bearer {key}"}, timeout=15)
print("Status:", r.status_code)

if r.status_code == 200:
    for m in sorted(m["id"] for m in r.json().get("data", [])):
        print(" -", m)
else:
    print(r.text)
