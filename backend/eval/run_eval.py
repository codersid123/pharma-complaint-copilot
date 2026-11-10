"""Measure how accurately the agent extracts complaint fields.

    cd backend
    python -m eval.run_eval                    # both extractors, real Groq models
    python -m eval.run_eval --mode structured  # just one

Calls the real LLM (about 40 calls), so it is NOT part of pytest or CI.
Writes eval/results/<mode>.json and eval/results/summary.md.
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from app.agent import EXTRACTORS, assess_risk
from app.extract import extract_text
from app.llm import get_llms

from .scoring import SCORED_FIELDS, compare, summarise

HERE = Path(__file__).resolve().parent
DATASET = HERE / "dataset"
RESULTS = HERE / "results"


def load_dataset() -> list:
    docs = json.loads((DATASET / "expected.json").read_text(encoding="utf-8"))["documents"]
    for d in docs:
        path = (DATASET / d["file"]).resolve()
        d["name"] = path.name
        d["text"] = extract_text(path.name, path.read_bytes())
    return docs


def call_with_retry(fn, *args, tries: int = 4):
    """Groq's free tier limits tokens per minute; wait and retry when we hit it."""
    for attempt in range(tries):
        try:
            return fn(*args)
        except Exception as e:  # noqa: BLE001
            if attempt == tries - 1 or "rate" not in str(e).lower():
                raise
            wait = 20 * (attempt + 1)
            print(f"    rate limited, waiting {wait}s...")
            time.sleep(wait)


def evaluate(mode: str, docs: list, llms, delay: float) -> dict:
    extractor = EXTRACTORS[mode]
    per_doc = []
    for d in docs:
        print(f"  [{mode}] {d['name']}")
        row = {"file": d["name"], "why": d["why"], "error": None}
        try:
            out = call_with_retry(extractor, {"raw_text": d["text"]}, llms)
            got = out["form_patch"]["updates"]
            risk = call_with_retry(assess_risk, {"current_form": {}, "form_patch":
                                                 {"updates": got, "clear": []}}, llms)["risk"]
        except Exception as e:  # noqa: BLE001  one bad document must not stop the run
            got, risk = {}, None
            row["error"] = f"{type(e).__name__}: {e}"[:300]
        row["got"] = {f: got.get(f) for f in SCORED_FIELDS}
        row["outcomes"] = {f: compare(f, d["expected"][f], got.get(f)) for f in SCORED_FIELDS}
        row["risk_level"] = risk["level"] if risk else None
        row["risk_agrees"] = bool(risk) and risk["level"].lower() == d["expected"]["initial_severity"].lower()
        per_doc.append(row)
        time.sleep(delay)
    return {"mode": mode, "model": llms.reasoning_model,
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "summary": summarise(per_doc), "documents": per_doc}


def pct(x: float) -> str:
    return f"{round(x * 100)}%"


def markdown(results: list) -> str:
    modes = [r["mode"] for r in results]
    lines = [f"# Extraction evaluation ({results[0]['run_at'][:10]}, model `{results[0]['model']}`)",
             "", f"{len(results[0]['documents'])} documents, {len(SCORED_FIELDS)} fields each.", "",
             "| Field | " + " | ".join(modes) + " |", "|---|" + "---|" * len(modes)]
    for f in SCORED_FIELDS:
        lines.append(f"| {f} | " + " | ".join(pct(r["summary"]["fields"][f]["accuracy"]) for r in results) + " |")
    for label, key in [("**Overall accuracy**", "overall_accuracy"),
                       ("**Hallucination rate**", "hallucination_rate"),
                       ("**Risk level agrees**", "risk_agreement")]:
        lines.append(f"| {label} | " + " | ".join(f"**{pct(r['summary'][key])}**" for r in results) + " |")
    lines += ["", "Hallucination rate = of the fields NOT in the document, how often the model filled one in.",
              "", "## Every miss", ""]
    for r in results:
        lines.append(f"### {r['mode']}")
        for d in r["documents"]:
            if d["error"]:
                lines.append(f"- `{d['file']}`: **error** {d['error']}")
            for f, o in d["outcomes"].items():
                if o in ("wrong", "missed", "invented"):
                    lines.append(f"- `{d['file']}` {f}: **{o}** (got `{d['got'][f]}`)")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["json", "structured", "both"], default="both")
    ap.add_argument("--delay", type=float, default=3.0, help="seconds between documents")
    args = ap.parse_args()

    modes = ["json", "structured"] if args.mode == "both" else [args.mode]
    docs, llms = load_dataset(), get_llms()
    RESULTS.mkdir(exist_ok=True)
    results = []
    for mode in modes:
        r = evaluate(mode, docs, llms, args.delay)
        (RESULTS / f"{mode}.json").write_text(json.dumps(r, indent=2, default=str), encoding="utf-8")
        results.append(r)
    md = markdown(results)
    (RESULTS / "summary.md").write_text(md, encoding="utf-8")
    print("\n" + md)


if __name__ == "__main__":
    main()
