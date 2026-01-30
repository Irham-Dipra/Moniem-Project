from fastapi import APIRouter, HTTPException
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment import PaymentCreate

router = APIRouter()
payment_repo = PaymentRepository()

@router.get("/payments/recent")
def get_recent_payments():
    return payment_repo.get_recent_payments()

@router.post("/payments")
def create_payment(payment: PaymentCreate):
    try:
        return payment_repo.create_payment(payment.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/students/{student_id}/payments")
def get_student_payments(student_id: int):
    return payment_repo.get_student_payments(student_id)

@router.get("/finance/stats")
def get_finance_stats():
    return payment_repo.get_finance_stats()

@router.get("/finance/programs")
def get_program_finance_stats():
    return payment_repo.get_program_finance_stats()
