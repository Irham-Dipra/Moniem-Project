from typing import List, Optional
from pydantic import BaseModel
from datetime import date

class AttendanceBase(BaseModel):
    attendance_id: Optional[int] = None
    enrollment_id: int
    status: str  # 'Present', 'Absent', 'Late', 'Excused'
    date: str    # Passed as string YYYY-MM-DD for simplicity

class BulkAttendanceRequest(BaseModel):
    program_id: int
    date: str
    records: List[AttendanceBase]
