from app.core.supabase import supabase
from app.schemas.exam import ExamCreate
from fastapi.encoders import jsonable_encoder

class ExamRepository:
    def __init__(self):
        self.table = "exam"

    def get_exams_by_program(self, program_id: int):
        # Ordered by date descending
        response = supabase.table(self.table)\
            .select("*")\
            .eq("program_id", program_id)\
            .order("exam_date", desc=True)\
            .execute()
        return response.data

    def get_all_exams(self):
        # Fetch all exams with program and batch info
        # program(program_name, batch(batch_name))
        response = supabase.table(self.table)\
            .select("*, program(program_name, batch(batch_name))")\
            .order("exam_date", desc=True)\
            .execute()
        return response.data

    def get_exam_by_id(self, exam_id: int):
        response = supabase.table(self.table)\
            .select("*")\
            .eq("exam_id", exam_id)\
            .execute()
        return response.data[0] if response.data else None

    def create_exam(self, exam: ExamCreate):
        data = jsonable_encoder(exam)
        response = supabase.table(self.table).insert(data).execute()
        return response.data[0]

    def delete_exam(self, exam_id: int):
        supabase.table(self.table).delete().eq("exam_id", exam_id).execute()
        return True
