from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class PaymentBase(BaseModel):
    payment_id: Optional[int] = None
    enrollment_id: int
    paid_amount: float
    due_amount: Optional[float] = 0
    status: str = 'Paid' 
    payment_date: str
    month: Optional[float] = None
    year: Optional[float] = None
    payment_method: Optional[str] = "Cash"
    remarks: Optional[str] = None

class PaymentCreate(BaseModel):
    student_id: int
    program_id: int 
    paid_amount: float
    payment_date: str
    month: int
    year: int
    payment_method: str
    remarks: Optional[str] = None

class PaymentResponse(PaymentBase):
    student_name: str
    program_name: str
    roll_no: Optional[int] = None
