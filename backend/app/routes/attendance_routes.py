from fastapi import APIRouter
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.attendance import BulkAttendanceRequest

router = APIRouter()
attendance_repo = AttendanceRepository()

@router.get("/programs/{program_id}/attendance")
def get_daily_attendance(program_id: int, date: str):
    return attendance_repo.get_daily_attendance(program_id, date)

@router.post("/attendance/bulk")
def upsert_attendance(data: BulkAttendanceRequest):
    return attendance_repo.upsert_attendance(data.records)
