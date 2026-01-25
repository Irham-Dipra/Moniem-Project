from fastapi.encoders import jsonable_encoder
from app.core.supabase import supabase
from app.schemas.program import ProgramCreate, BatchCreate

class ProgramRepository:
    def __init__(self):
        self.program_table = "program"
        self.batch_table = "batch"

    # ==========================================
    # BATCH OPERATIONS
    # ==========================================
    # We manage Batches here too because they are so closely related to Programs.
    
    def get_all_batches(self):
        return supabase.table(self.batch_table).select("*").execute().data

    def create_batch(self, batch: BatchCreate):
        # jsonable_encoder converts Pydantic models to simple Python types (str, int)
        # This handles dates automatically (date -> "2024-01-01")
        data = jsonable_encoder(batch)
        response = supabase.table(self.batch_table).insert(data).execute()
        return response.data[0]

    # ==========================================
    # PROGRAM OPERATIONS
    # ==========================================
    
    def get_all_programs(self):
        # FANCY SUPABASE TRICK: Relationship Joins + Counts
        # enrollment(count) gives us a field "enrollment": [{"count": 5}]
        response = supabase.table(self.program_table)\
            .select("*, batch(*), enrollment(count)")\
            .execute()
        return response.data

    def get_program_by_id(self, program_id: int):
        # Fetch detailed info:
        # 1. Basic Program Info + Batch
        # 2. Enrolled Students (via enrollment -> student)
        # 3. Exam List
        # 4. Teacher List (via teacher_program_enrollment -> teacher)
        query = """
            *,
            batch(*),
            enrollment(
                *,
                student(*),
                payment(*)
            ),
            exam(*),
            teacher_program_enrollment(
                teacher(*)
            )
        """
        response = supabase.table(self.program_table)\
            .select(query)\
            .eq("program_id", program_id)\
            .execute()
        return response.data[0] if response.data else None

    def create_program(self, program: ProgramCreate):
        # The 'program' object coming from the user already has 'batch_id'.
        # We use jsonable_encoder to ensure dates are strings, not objects.
        data = jsonable_encoder(program)
        response = supabase.table(self.program_table).insert(data).execute()
        return response.data[0]
