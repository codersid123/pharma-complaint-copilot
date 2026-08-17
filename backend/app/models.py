from sqlalchemy import Column, Integer, String, Text, DateTime, func
from .db import Base

class Complaint(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True)
    complaint_number = Column(String(30), unique=True)
    complaint_source = Column(String(100))
    customer_name = Column(String(200))
    product_name = Column(String(200))
    product_strength = Column(String(100))
    batch_number = Column(String(100), index=True)
    manufacturing_date = Column(String(20))
    expiry_date = Column(String(20))
    quantity_affected = Column(String(50))
    complaint_type = Column(String(100))
    complaint_date = Column(String(20))
    complaint_description = Column(Text)
    initial_severity = Column(String(20))
    priority = Column(String(20))
    ai_risk_level = Column(String(20))
    ai_risk_score = Column(Integer)
    ai_risk_rationale = Column(Text)
    source_text = Column(Text)
    status = Column(String(30), default="Pending Triage")
    created_at = Column(DateTime, server_default=func.now())