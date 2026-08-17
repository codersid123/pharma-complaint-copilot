from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .schemas import AgentResponse, TextIntakeRequest, CopilotRequest
from . import fake_agent

app = FastAPI(title="AIVOA Complaint Management API")

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
    contents = await file.read()
    print(f"Received {file.filename}, {len(contents)} bytes")
    return fake_agent.fake_extract()

@app.post("/api/intake/text", response_model=AgentResponse)
def intake_text(req: TextIntakeRequest):
    print(f"Received {len(req.text)} chars of pasted text")
    return fake_agent.fake_extract()

@app.post("/api/copilot/chat", response_model=AgentResponse)
def copilot(req: CopilotRequest):
    return fake_agent.fake_modify(req.message, req.current_form)