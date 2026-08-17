from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Literal

Severity = Literal["Critical", "Major", "Minor"]
Priority = Literal["High", "Medium", "Low"]

class ComplaintForm(BaseModel):
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    manufacturing_date: Optional[str] = None
    expiry_date: Optional[str] = None
    quantity_affected: Optional[str] = None
    complaint_type: Optional[str] = None
    complaint_date: Optional[str] = None
    complaint_description: Optional[str] = None
    initial_severity: Optional[Severity] = None
    priority: Optional[Priority] = None

class FormPatch(BaseModel):
    updates: Dict[str, Any] = {}
    clear: List[str] = []

class RiskAssessment(BaseModel):
    level: str
    score: int
    rationale: str
    recommended_action: str

class AgentResponse(BaseModel):
    patch: FormPatch
    assistant_message: str
    missing_fields: List[str] = []
    risk: Optional[RiskAssessment] = None

class TextIntakeRequest(BaseModel):
    text: str

class CopilotRequest(BaseModel):
    message: str
    current_form: Dict[str, Any]