import os, requests
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()
KEY = os.getenv("GROQ_API_KEY")

def _active_models() -> set:
    r = requests.get("https://api.groq.com/openai/v1/models",
                     headers={"Authorization": f"Bearer {KEY}"}, timeout=15)
    r.raise_for_status()
    return {m["id"] for m in r.json().get("data", [])}

_available = _active_models()

def _pick(*candidates) -> str:
    for c in candidates:
        if c and c in _available:
            return c
    raise RuntimeError(
        f"None of {candidates} are available. Account has: {sorted(_available)}")

FAST_MODEL = _pick(os.getenv("GROQ_MODEL"),
                   os.getenv("GROQ_FALLBACK_MODEL"),
                   "openai/gpt-oss-20b")

REASONING_MODEL = _pick(os.getenv("GROQ_REASONING_MODEL"),
                        "openai/gpt-oss-120b")

if FAST_MODEL != os.getenv("GROQ_MODEL"):
    print(f"[llm] '{os.getenv('GROQ_MODEL')}' unavailable on GroqCloud "
          f"(deprecated) — using '{FAST_MODEL}'")
print(f"[llm] fast={FAST_MODEL}  reasoning={REASONING_MODEL}")

fast_llm = ChatGroq(model=FAST_MODEL, temperature=0, api_key=KEY,
                    model_kwargs={"reasoning_format": "hidden"})
reasoning_llm = ChatGroq(model=REASONING_MODEL, temperature=0, api_key=KEY,
                         model_kwargs={"reasoning_format": "hidden"})