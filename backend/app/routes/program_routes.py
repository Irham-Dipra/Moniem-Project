from fastapi import APIRouter, HTTPException
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
    try:
        return repo.create_batch(batch)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ==========================================
# PROGRAM ENDPOINTS
# ==========================================

@router.get("/programs")
def get_programs():
    return repo.get_all_programs()

@router.get("/programs/{program_id}")
def get_program_details(program_id: int):
    return repo.get_program_by_id(program_id)

@router.post("/programs")
def create_program(program: ProgramCreate):
    try:
        return repo.create_program(program)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
