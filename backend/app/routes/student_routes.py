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