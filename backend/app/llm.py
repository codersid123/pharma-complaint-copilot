"""LLM setup. Nothing here talks to Groq at import time."""
import logging
import os
from dataclasses import dataclass
from functools import lru_cache

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

MODELS_URL = "https://api.groq.com/openai/v1/models"


@dataclass(frozen=True)
class LLMs:
    fast: object        # anything with .invoke(prompt) -> result with .content
    reasoning: object
    fast_model: str
    reasoning_model: str


def active_models(api_key: str) -> set:
    r = requests.get(MODELS_URL, headers={"Authorization": f"Bearer {api_key}"},
                     timeout=15)
    r.raise_for_status()
    return {m["id"] for m in r.json().get("data", [])}


def pick_model(available: set, *candidates) -> str:
    """Return the first candidate the account has. Skips None/empty."""
    for c in candidates:
        if c and c in available:
            return c
    raise RuntimeError(
        f"None of {candidates} are available. Account has: {sorted(available)}")


@lru_cache(maxsize=1)
def get_llms() -> LLMs:
    from langchain_groq import ChatGroq

    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")
    available = active_models(key)

    wanted = os.getenv("GROQ_MODEL")
    fast_model = pick_model(available, wanted,
                            os.getenv("GROQ_FALLBACK_MODEL"), "openai/gpt-oss-20b")
    reasoning_model = pick_model(available, os.getenv("GROQ_REASONING_MODEL"),
                                 "openai/gpt-oss-120b")
    if wanted and fast_model != wanted:
        log.warning("'%s' unavailable on GroqCloud - using '%s'", wanted, fast_model)

    def make(model):
        return ChatGroq(model=model, temperature=0, api_key=key,
                        reasoning_format="hidden")

    return LLMs(fast=make(fast_model), reasoning=make(reasoning_model),
                fast_model=fast_model, reasoning_model=reasoning_model)