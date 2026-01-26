from pydantic import BaseModel
from typing import Optional
from datetime import date

class ExamBase(BaseModel):
    program_id: int
    exam_name: str
    exam_date: Optional[date] = None
    exam_type: str = "Weekly"  # Weekly, Monthly, Term
    subject: Optional[str] = None
    total_marks: float

class ExamCreate(ExamBase):
    pass

class ExamResponse(ExamBase):
    exam_id: int
    
    class Config:
        from_attributes = True
