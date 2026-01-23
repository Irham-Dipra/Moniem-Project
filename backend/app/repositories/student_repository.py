from app.core.supabase import supabase

class StudentRepository:
    def __init__(self):
        self.table = "Student"

    def get_all_students(self):
        # Fetch data from Supabase
        response = supabase.table(self.table).select("*").execute()
        return response.data

    def enroll_new_student(self, student_data: dict):
        # Insert a new student record
        return supabase.table(self.table).insert(student_data).execute()