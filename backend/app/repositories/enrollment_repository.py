from app.core.supabase import supabase
from app.schemas.enrollment import EnrollmentCreate
from fastapi.encoders import jsonable_encoder

class EnrollmentRepository:
    def __init__(self):
        self.table = "enrollment"

    def get_by_student(self, student_id: int):
        # Join with 'program' to get course name, and 'program.batch' for batch info
        response = supabase.table(self.table)\
            .select("*, program(*, batch(*))")\
            .eq("student_id", student_id)\
            .execute()
        return response.data

    def enroll_student(self, enrollment: EnrollmentCreate):
        data = jsonable_encoder(enrollment)
        # remove 'program' or any extra fields if they sneaked in, though Pydantic handles this.
        response = supabase.table(self.table).insert(data).execute()
        return response.data[0]
