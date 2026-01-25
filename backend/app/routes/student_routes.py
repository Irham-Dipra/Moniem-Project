from fastapi import APIRouter
from app.repositories.student_repository import StudentRepository
from app.schemas.student import StudentCreate

# 1. Create a Router (like a mini-app for students)
router = APIRouter()

# 2. Add the Logic
repo = StudentRepository()

# 3. Define the "Endpoints" (URL paths)

@router.get("/students")
def get_students():
    return repo.get_all_students()

@router.post("/students")
def create_student(student: StudentCreate):
    # FastAPI automatically validates 'student' against your Pydantic rules here!
    return repo.enroll_new_student(student)

@router.get("/students/{student_id}")
def get_student(student_id: int):
    return repo.get_student_by_id(student_id)

@router.patch("/students/{student_id}")
def update_student(student_id: int, student_data: dict):
    # We accept a dict so we can do partial updates
    return repo.update_student(student_id, student_data)