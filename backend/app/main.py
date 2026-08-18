from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from .schemas import AgentResponse, TextIntakeRequest, CopilotRequest
from .db import engine, Base, get_db
from .models import Complaint
from .agent import run_agent
from .extract import extract_text

app = FastAPI(title="AIVOA Complaint Management API")
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/intake/upload", response_model=AgentResponse)
async def intake_upload(file: UploadFile = File(...)):
    data = await file.read()
    text = extract_text(file.filename, data)
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

@app.post("/api/complaints")
def create_complaint(payload: dict, db: Session = Depends(get_db)):
    form, risk = payload.get("form", {}), payload.get("risk") or {}
    count = db.query(Complaint).count() + 1
    number = f"CMP-{datetime.now().year}-{count:04d}"
    c = Complaint(
        complaint_number=number,
        ai_risk_level=risk.get("level"),
        ai_risk_score=risk.get("score"),
        ai_risk_rationale=risk.get("rationale"),
        **{k: v for k, v in form.items() if hasattr(Complaint, k)}
    )
    db.add(c); db.commit(); db.refresh(c)
    return {"id": c.id, "complaint_number": c.complaint_number}

@app.get("/api/complaints")
def list_complaints(db: Session = Depends(get_db)):
    rows = db.query(Complaint).order_by(Complaint.id.desc()).limit(50).all()
    return [{"id": r.id, "complaint_number": r.complaint_number,
             "customer_name": r.customer_name, "product_name": r.product_name,
             "batch_number": r.batch_number, "initial_severity": r.initial_severity,
             "status": r.status, "created_at": r.created_at} for r in rows]