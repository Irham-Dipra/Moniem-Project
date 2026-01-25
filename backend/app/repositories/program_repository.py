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
        # FANCY SUPABASE TRICK: Relationship Joins
        # By saying "*, batch(*)", we tell Supabase:
        # "Get all program columns, AND go look up the connected 'batch' info."
        # This way, the frontend gets { "program_name": "Physics", "batch": { "batch_name": "HSC 2024" } }
        response = supabase.table(self.program_table).select("*, batch(*)").execute()
        return response.data

    def create_program(self, program: ProgramCreate):
        # The 'program' object coming from the user already has 'batch_id'.
        # We use jsonable_encoder to ensure dates are strings, not objects.
        data = jsonable_encoder(program)
        response = supabase.table(self.program_table).insert(data).execute()
        return response.data[0]
