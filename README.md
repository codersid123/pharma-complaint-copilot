# AI-Powered Customer Complaint Management System

[![CI](https://github.com/codersid123/pharma-complaint-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/codersid123/pharma-complaint-copilot/actions/workflows/ci.yml)

A customer complaint intake and triage module for a pharmaceutical Quality Management
System, covering both API (Active Pharmaceutical Ingredient) and FDF (Finished Dosage
Form) manufacturing.

**The form is entirely AI-driven.** Every field is read-only. Values are populated
either by extracting an uploaded complaint document or by natural-language instruction
to the copilot — there is no manual data entry path. Every value in the record therefore
traces back to a source document or an explicit instruction, which is a stronger audit
position than a free-text form where nobody knows where a batch number came from.

---

## Evaluation

How accurately does the agent turn a complaint document into form fields? Measured on
10 hand-labelled documents (formal letters, informal emails, a call log, an adverse-event
email) with deliberate traps: missing batch numbers, a retest date instead of an expiry
date, day-first dates, and a document mentioning two batches.

|                                                       | Before | After prompt fixes |
| ----------------------------------------------------- | ------ | ------------------ |
| Overall field accuracy (100 fields)                   | 89%    | **99%**            |
| Customer name                                         | 50%    | 100%               |
| Initial severity                                      | 80%    | 100%               |
| Invented values (19 fields absent from the documents) | **0**  | **0**              |
| Risk level agrees with expected severity              | 80%    | 80%                |

Model: `openai/gpt-oss-120b` on Groq. Run it: `cd backend; python -m eval.run_eval`.
Full results: `backend/eval/results/`.

**Findings**

1. **No hallucinations.** Across both runs the model never invented a value that wasn't in
   the document: it left missing batch numbers empty, did not copy a _retest_ date into
   _expiry_, read `05/09/2026` as 5 September, and picked the right batch when two were mentioned.
2. **Most errors were unclear definitions, not misreading.** The model put the contact
   person ("Priya", "Dr. Anjali Nair") as the customer in 5 of 10 documents, and rated 3
   defects one level too low. Defining _customer = the organisation_, _complaint date = the
   date it was reported_, and _when unsure, choose the higher severity_ fixed these.
3. **Structured output lost to plain JSON.** LangChain's `with_structured_output` (tool calling)
   failed on 6 of 10 documents with `tool_use_failed` (the model wrote JSON as text instead
   of calling the tool): 52% vs 89%. The JSON extractor stays the default (`EXTRACT_MODE=json`).
4. **The evaluation found a non-AI bug.** The email reader dropped the `Date:` header, so the
   model correctly left the complaint date empty. Fixed in `extract.py`.

**Limits.** 10 documents is small. The prompt was adjusted after seeing errors on this same set,
so these numbers are optimistic. The next step is a held-out set of new documents. Risk-level
agreement (80%) was not tuned. Scanned PDFs (images) are not supported.

## Stack

| Layer    | Technology                              |
| -------- | --------------------------------------- |
| Frontend | React 18, Redux Toolkit, Vite, Inter    |
| Backend  | Python 3.12, FastAPI                    |
| Agent    | LangGraph                               |
| LLM      | Groq (see Model Selection Note)         |
| Database | PostgreSQL 16 + SQLAlchemy              |
| Parsing  | pdfplumber, python-docx, stdlib `email` |

---

## Architecture

```
Browser (React + Redux)
   │  POST /api/intake/upload   (file)          ──┐
   │  POST /api/intake/text     {text}          ──┤
   │  POST /api/copilot/chat    {msg, form}     ──┤
   ↓                                              │
FastAPI                                           │
   ├─ extract.py  → pdfplumber / docx / eml  ─────┤
   └─ agent.py    → LangGraph  ←──────────────────┘
         router → extract | modify | clarify | query
                       ↓
                  validate → risk
                       ↓
   { patch: {updates, clear}, assistant_message, missing_fields, risk }
   ↓
Redux applyAIPatch → merge → form re-renders (green highlight on changed fields)
   ↓
POST /api/complaints → PostgreSQL
```

All three AI endpoints return the same response shape, so the frontend has a single
handler (`useAgent.js`) rather than three divergent code paths.

---

## The LangGraph agent

Seven nodes:

| Node       | Purpose                                                  |
| ---------- | -------------------------------------------------------- |
| `router`   | Chooses the branch                                       |
| `extract`  | Reads a document into the full form schema               |
| `modify`   | Turns a chat instruction into a field patch              |
| `clarify`  | Asks which field was meant when a reference is ambiguous |
| `query`    | Answers a question without changing anything             |
| `validate` | Checks required fields (pure Python, no LLM)             |
| `risk`     | Classifies severity with a score and recommended action  |

Two design decisions worth calling out:

**Routing is deterministic where the answer is knowable.** A document either exists in
the request or it doesn't, so `extract` is selected in Python. The LLM classifies only
genuinely ambiguous chat messages, and `extract` is excluded from its candidate set —
an early bug had it misreading "the batch number is MET-9012" as a document to parse.

**Edits are patches, not whole forms.** `modify` returns `{updates, clear}` containing
only what changed. `updates` and `clear` are separate keys because a `null` value cannot
distinguish "leave this alone" from "erase this". A single instruction can never silently
wipe fields it didn't mention.

---

## Model Selection Note

The assignment specifies `gemma2-9b-it` on Groq. Groq announced its deprecation in
August 2025 and removed it from service; the suggested alternative
`llama-3.3-70b-versatile` is also no longer available on GroqCloud.

Verified against the live models endpoint — see `backend/check_models.py`.

The application queries `GET /openai/v1/models` at startup and selects the first
available model from a configured preference list. `GROQ_MODEL` in `.env` is still set
to `gemma2-9b-it`; if Groq restores it, the application will use it with no code change.
Startup logs the substitution.

Currently resolving to:

- Routing and lightweight tasks: `openai/gpt-oss-20b`
- Extraction, modification, risk assessment: `openai/gpt-oss-120b`

---

## Features

**Core**

- Drag-and-drop upload of PDF, DOCX, TXT and EML complaint documents
- Paste-text intake for raw emails
- AI extraction into a 13-field QMS complaint schema
- Natural-language editing of any field through the copilot
- Read-only form with click-to-hint guidance
- Undo, handled client-side for zero latency
- Persistence to PostgreSQL with auto-generated complaint numbers

**Bonus features implemented**

- **AI risk classification** — level, 0–100 score, rationale, and recommended action
  with a timeframe
- **Completeness checker** — required-field validation that drives the Save button
  state and is surfaced conversationally by the copilot
- **Duplicate detection** — SQL lookup by batch number, warns before saving a second
  complaint against the same batch
- **Ambiguity handling** — the agent asks which field was meant rather than guessing

### Bulk import (CSV / Excel)

`POST /api/import` turns a spreadsheet into complaint records.

- Accepts `.csv` and `.xlsx`; ~50 header spellings map to fields (`Batch No`, `Lot`, `Exp. Date`, `Qty`…)
- Every row is validated with the same model as a manual save
- Bad rows are reported by spreadsheet row number, field and reason; good rows are still saved
- All good rows are saved in one transaction
- `?dry_run=true` returns the report without saving; the UI requires a check before import
- Same batch + customer + complaint date is treated as a duplicate, so re-importing a file is safe

## Try it with `samples/complaints_bulk.xlsx` (40 rows, 5 deliberately bad).

## Domain context

A customer complaint in a pharmaceutical QMS is a formal record of an alleged deficiency
in the identity, quality, purity or reliability of a marketed product. Logging and
investigating them is a GMP requirement (21 CFR 211.198, EU GMP Chapter 8).

The full lifecycle is Intake → Triage → Investigation → CAPA → Effectiveness Check →
Closure. This module covers **Intake and Triage**, which is why the form header shows a
"Pending Triage" status chip.

Severity guidance encoded in the risk prompt:

| Level    | Criteria                                                                                                                                      |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Critical | Potential patient harm — contamination, sterility failure, wrong product, adverse-event signal. Escalate to Pharmacovigilance within 24 hours |
| Major    | Significant quality defect without immediate safety risk                                                                                      |
| Minor    | Cosmetic defect                                                                                                                               |

---

## Setup

### Quick start (Docker)

```bash
cp .env.example .env      # add your GROQ_API_KEY
docker compose up --build
```

Frontend: http://localhost:5173 · API docs: http://localhost:8000/docs
The database is migrated and seeded with 50 sample complaints on first start.

### Without Docker

```bash
cd frontend
npm install
npm run dev
```

```bash
cd backend
python -m venv venv && venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
cp .env.example .env      # set DATABASE_URL and GROQ_API_KEY
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

## Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest --cov
```

`samples/` contains three documents chosen to exercise different paths: a complete
formal complaint, an informal email missing several required fields, and an API
contamination case that should classify as Critical.

Tests use a fake LLM and an in-memory database, so they need no API key, no network and no Postgres. CI runs them on Python 3.12 and 3.14, plus the API tests against a real Postgres 16.

### Frontend

App at http://localhost:5173

---

## API

| Method | Endpoint                          | Purpose                               |
| ------ | --------------------------------- | ------------------------------------- |
| `GET`  | `/api/health`                     | Liveness check                        |
| `POST` | `/api/intake/upload`              | Multipart file → extracted form patch |
| `POST` | `/api/intake/text`                | Pasted text → extracted form patch    |
| `POST` | `/api/copilot/chat`               | Instruction + current form → patch    |
| `POST` | `/api/complaints`                 | Persist a complaint                   |
| `GET`  | `/api/complaints`                 | List recent complaints                |
| `POST` | `/api/complaints/check-duplicate` | Batch-number duplicate lookup         |

---

## Project structure

```
backend/
  app/
    main.py         FastAPI routes and CORS
    agent.py        LangGraph agent — 7 nodes
    llm.py          Groq model resolution and fallback
    extract.py      PDF / DOCX / EML text extraction
    schemas.py      Pydantic models — the shared form contract
    models.py       SQLAlchemy ORM
    db.py           Engine and session
    dates.py        Date parsing used on save and import
    seed.py         50 sample complaints for demos
    importer.py     CSV/Excel bulk import
  alembic/          Database migrations
  tests/            pytest suite (fake LLM, no network)
  scripts/
    check_models.py Diagnostic: lists models available to the API key
    make_bulk_sample.py  Builds samples/complaints_bulk.xlsx
docker-compose.yml  db + backend + frontend
frontend/
  src/
    store/          Redux slice — single source of truth for the form
    hooks/          useAgent — one handler for all three AI endpoints
    components/     AIField, ComplaintForm, CopilotPanel
    api.js          axios client
samples/            Realistic complaint documents for testing
```

---

## Known limitations and next steps

- Scanned or image-only PDFs are not supported; production OCR was explicitly out of
  scope for this assignment
- The extraction progress bar is simulated rather than driven by real streaming progress
- JSON is recovered from model output by regex rather than enforced structured output
- The copilot is stateless per turn — it receives the current form but not the
  conversation history
- Only the Intake and Triage stage is implemented; Investigation, CAPA and Closure
  would be the natural next modules

---

## AI tool usage

Built with AI assistance as permitted by the assignment. Architecture decisions,
the LangGraph node design, the patch-based edit model, and the model-deprecation
handling were reasoned through and adapted rather than accepted as generated.
