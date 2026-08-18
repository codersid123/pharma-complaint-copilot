import json, re
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from .llm import fast_llm, reasoning_llm
from .schemas import ComplaintForm

FIELD_KEYS = list(ComplaintForm.model_fields.keys())
REQUIRED = ["customer_name", "product_name", "batch_number",
            "complaint_type", "complaint_description", "initial_severity"]


class AgentState(TypedDict, total=False):
    raw_text: str
    user_message: str
    current_form: dict
    intent: str
    form_patch: dict
    missing_fields: List[str]
    risk: Optional[dict]
    assistant_message: str


def safe_json(raw: str) -> dict:
    """Pull the first JSON object out of a model response, tolerating
    markdown fences and reasoning preambles."""
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return {}


# ---------------- node 1: router ----------------
ROUTER_PROMPT = """Classify the user's chat message into exactly one word.

modify   - they are supplying or changing a field value. This includes plain
           statements of fact: "the batch number is X", "it was manufactured in
           June 2025", "customer is Acme", "make this critical", "add that ...".
           Any message that provides information belongs here.
clarify  - they want a change but it is impossible to tell which field they mean,
           e.g. "change the date" when several date fields exist.
query    - they are ASKING a question and expect an answer, not a change,
           e.g. "what is the expiry date?", "is this critical?".

Never answer "extract" — documents are handled elsewhere.

USER MESSAGE: "{msg}"

Answer with one word only."""


def route_intent(state: AgentState):
    if state.get("raw_text"):
        return {"intent": "extract"}
    out = fast_llm.invoke(ROUTER_PROMPT.format(msg=state.get("user_message", "")))
    word = out.content.strip().lower()
    intent = next((i for i in ["modify", "clarify", "query"] if i in word), "modify")
    return {"intent": intent}


# ---------------- node 2: extract ----------------
EXTRACT_PROMPT = """You are a pharmaceutical QMS complaint intake assistant.
Extract complaint details from the document into JSON.

Return ONLY a JSON object with exactly these keys:
{keys}

Rules:
- Use null for anything not stated. NEVER invent a batch number, date, or name.
- Dates as YYYY-MM-DD. If only month and year are given, use the first of that month.
- complaint_type: Product Quality | Packaging | Labelling | Adverse Event | Contamination | Documentation
- initial_severity: Critical (patient safety, contamination, sterility failure, wrong product),
  Major (significant quality defect with no immediate safety risk), Minor (cosmetic).
- priority: High | Medium | Low, consistent with severity.
- complaint_description: a concise factual summary of the defect reported.
- No markdown, no explanation, JSON only.

DOCUMENT:
{text}"""


def extract_fields(state: AgentState):
    out = reasoning_llm.invoke(EXTRACT_PROMPT.format(
        keys=", ".join(FIELD_KEYS), text=state["raw_text"][:6000]))
    data = safe_json(out.content)
    updates = {k: v for k, v in data.items()
               if k in FIELD_KEYS and v not in (None, "", "null", "N/A")}
    return {"form_patch": {"updates": updates, "clear": []},
            "assistant_message": f"I extracted {len(updates)} fields from the document. Please review."}


# ---------------- node 3: modify ----------------
MODIFY_PROMPT = """You edit a pharmaceutical complaint form. The user cannot type into
the form directly, so translate their instruction into field changes.

CURRENT FORM:
{form}

VALID FIELDS: {keys}
Enums:
  initial_severity: Critical | Major | Minor
  priority: High | Medium | Low
  complaint_type: Product Quality | Packaging | Labelling | Adverse Event | Contamination | Documentation

USER INSTRUCTION: "{msg}"

Return ONLY JSON in this shape:
{{"updates": {{"field_name": "new value"}}, "clear": ["field_to_empty"], "note": "one short sentence for the user"}}

Rules:
- Include ONLY fields the instruction actually changes.
- For "add to" or "append to" complaint_description, return the FULL merged text.
- Normalise dates to YYYY-MM-DD and enums to the exact casing above.
- If severity changes, update priority to stay consistent."""


def modify_fields(state: AgentState):
    out = reasoning_llm.invoke(MODIFY_PROMPT.format(
        form=json.dumps(state.get("current_form", {}), indent=2),
        keys=", ".join(FIELD_KEYS), msg=state.get("user_message", "")))
    d = safe_json(out.content)
    updates = {k: v for k, v in d.get("updates", {}).items() if k in FIELD_KEYS}
    clear = [k for k in d.get("clear", []) if k in FIELD_KEYS]
    note = d.get("note") or (f"Updated: {', '.join(updates)}" if updates
                             else "I couldn't work out what to change — could you rephrase?")
    return {"form_patch": {"updates": updates, "clear": clear},
            "assistant_message": note}


# ---------------- node 4: clarify ----------------
def clarify(state: AgentState):
    out = fast_llm.invoke(
        f'The user said: "{state.get("user_message", "")}". A complaint form has these '
        f'fields: {", ".join(FIELD_KEYS)}. Ask one short question to identify which '
        f'field they mean. Reply with the question only.')
    return {"form_patch": {"updates": {}, "clear": []},
            "assistant_message": out.content.strip()}


# ---------------- node 5: query ----------------
def answer_question(state: AgentState):
    out = reasoning_llm.invoke(
        f"You are a pharmaceutical QMS assistant. Current complaint record:\n"
        f"{json.dumps(state.get('current_form', {}), indent=2)}\n\n"
        f"Question: {state.get('user_message', '')}\n\n"
        f"Answer in two sentences or fewer.")
    return {"form_patch": {"updates": {}, "clear": []},
            "assistant_message": out.content.strip()}


# ---------------- node 6: validate ----------------
def check_completeness(state: AgentState):
    merged = {**state.get("current_form", {}), **state["form_patch"]["updates"]}
    for k in state["form_patch"]["clear"]:
        merged[k] = ""
    missing = [f for f in REQUIRED if not merged.get(f)]
    msg = state["assistant_message"]
    if missing:
        pretty = ", ".join(f.replace("_", " ") for f in missing)
        msg += f" Still needed: {pretty}. You can tell me these directly."
    return {"missing_fields": missing, "assistant_message": msg}


# ---------------- node 7: risk ----------------
RISK_PROMPT = """You are a pharmaceutical QMS risk assessor. Assess this complaint.

COMPLAINT:
{form}

Return ONLY JSON:
{{"level": "Critical", "score": 85,
  "rationale": "one or two sentences citing the specific defect",
  "recommended_action": "one concrete next step with a timeframe"}}

Guidance: contamination, sterility failure, wrong product, or any adverse-event signal
is Critical and must be escalated to Pharmacovigilance within 24 hours. Significant
quality defects without immediate safety risk are Major. Cosmetic issues are Minor."""


def assess_risk(state: AgentState):
    merged = {**state.get("current_form", {}), **state["form_patch"]["updates"]}
    if not merged.get("complaint_description"):
        return {"risk": None}
    out = reasoning_llm.invoke(RISK_PROMPT.format(form=json.dumps(merged, indent=2)))
    d = safe_json(out.content)
    if not d.get("level"):
        return {"risk": None}
    try:
        score = int(d.get("score", 50))
    except (TypeError, ValueError):
        score = 50
    return {"risk": {"level": d["level"], "score": score,
                     "rationale": d.get("rationale", ""),
                     "recommended_action": d.get("recommended_action", "")}}


# ---------------- graph ----------------
def build_graph():
    g = StateGraph(AgentState)
    g.add_node("router", route_intent)
    g.add_node("extract", extract_fields)
    g.add_node("modify", modify_fields)
    g.add_node("clarify", clarify)
    g.add_node("query", answer_question)
    g.add_node("validate", check_completeness)
    g.add_node("risk", assess_risk)

    g.set_entry_point("router")
    g.add_conditional_edges("router", lambda s: s["intent"],
                            {"extract": "extract", "modify": "modify",
                             "clarify": "clarify", "query": "query"})
    g.add_edge("extract", "validate")
    g.add_edge("modify", "validate")
    g.add_edge("clarify", END)
    g.add_edge("query", END)
    g.add_edge("validate", "risk")
    g.add_edge("risk", END)
    return g.compile()


graph = build_graph()


def run_agent(raw_text: str = "", user_message: str = "", current_form: dict = None) -> dict:
    result = graph.invoke({
        "raw_text": raw_text,
        "user_message": user_message,
        "current_form": current_form or {},
    })
    return {
        "patch": result.get("form_patch", {"updates": {}, "clear": []}),
        "assistant_message": result.get("assistant_message", ""),
        "missing_fields": result.get("missing_fields", []),
        "risk": result.get("risk"),
    }