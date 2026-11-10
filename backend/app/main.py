from datetime import datetime

from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .agent import run_agent
from .db import get_db
from .extract import extract_text
from .models import Complaint
from .schemas import (
    AgentResponse,
    ComplaintCreate,
    ComplaintCreated,
    CopilotRequest,
    DuplicateCheckRequest,
    TextIntakeRequest,
)

app = FastAPI(title="Complaint Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def complaint_number(row_id: int, year: int) -> str:
    """Built from the row id, so two saves can never get the same number."""
    return f"CMP-{year}-{row_id:04d}"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/intake/upload", response_model=AgentResponse)
async def intake_upload(file: UploadFile = File(...)):
    data = await file.read()
    text = extract_text(file.filename or "", data)
    if not text.strip():
        return AgentResponse(
            patch={"updates": {}, "clear": []},
            assistant_message="I couldn't read any text from that file. "
                              "Try a text-based PDF, or paste the content instead.")
    return AgentResponse(**run_agent(raw_text=text))


@app.post("/api/intake/text", response_model=AgentResponse)
def intake_text(req: TextIntakeRequest):
    return AgentResponse(**run_agent(raw_text=req.text))


@app.post("/api/copilot/chat", response_model=AgentResponse)
def copilot(req: CopilotRequest):
    return AgentResponse(**run_agent(user_message=req.message,
                                     current_form=req.current_form))


@app.post("/api/complaints", response_model=ComplaintCreated)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    risk = payload.risk
    c = Complaint(
        ai_risk_level=risk.level if risk else None,
        ai_risk_score=risk.score if risk else None,
        ai_risk_rationale=risk.rationale if risk else None,
        **payload.form.model_dump(),
    )
    db.add(c)
    db.flush()  # sends the INSERT, so c.id exists, but nothing is committed yet
    c.complaint_number = complaint_number(c.id, datetime.now().year)
    db.commit()
    db.refresh(c)
    return ComplaintCreated(id=c.id, complaint_number=c.complaint_number)


@app.get("/api/complaints")
def list_complaints(db: Session = Depends(get_db)):
    rows = db.query(Complaint).order_by(Complaint.id.desc()).limit(50).all()
    return [{"id": r.id, "complaint_number": r.complaint_number,
             "customer_name": r.customer_name, "product_name": r.product_name,
             "batch_number": r.batch_number, "initial_severity": r.initial_severity,
             "status": r.status, "created_at": r.created_at} for r in rows]


@app.post("/api/complaints/check-duplicate")
def check_duplicate(payload: DuplicateCheckRequest, db: Session = Depends(get_db)):
    batch = (payload.form.get("batch_number") or "").strip()
    if not batch:
        return {"duplicates": []}
    rows = db.query(Complaint).filter(Complaint.batch_number == batch).all()
    return {"duplicates": [{"complaint_number": r.complaint_number,
                            "product_name": r.product_name,
                            "created_at": str(r.created_at)} for r in rows]}
