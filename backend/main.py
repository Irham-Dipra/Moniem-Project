from fastapi import FastAPI
from app.repositories.student_repository import StudentRepository

app = FastAPI()
repo = StudentRepository()

@app.get("/")
def read_root():
    return {"status": "Backend is running!"}

@app.get("/students")
def get_students():
    # Use the repository we just built!
    students = repo.get_all_students()
    return {"data": students}