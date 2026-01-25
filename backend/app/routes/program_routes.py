from fastapi import APIRouter
from app.repositories.program_repository import ProgramRepository
from app.schemas.program import ProgramCreate, BatchCreate

router = APIRouter()
repo = ProgramRepository()

# ==========================================
# BATCH ENDPOINTS
# ==========================================

@router.get("/batches")
def get_batches():
    return repo.get_all_batches()

@router.post("/batches")
def create_batch(batch: BatchCreate):
    return repo.create_batch(batch)

# ==========================================
# PROGRAM ENDPOINTS
# ==========================================

@router.get("/programs")
def get_programs():
    return repo.get_all_programs()

@router.post("/programs")
def create_program(program: ProgramCreate):
    return repo.create_program(program)
