# Imports the 'supabase' connection object we created in app/core/supabase.py
from app.core.supabase import supabase
from app.schemas.student import StudentCreate

class StudentRepository:
    def __init__(self):
        # Define the table name once so we don't typo it later
        # NOTE: Postgres table names are usually lowercase!
        self.table = "student"

    def get_all_students(self):
        # 1. Select the table
        # 2. Select all columns ("*")
        # 3. Execute the query and wait for the result
        response = supabase.table(self.table).select("*").execute()
        
        # Return only the 'data' part (ignoring status codes, etc.)
        return response.data

    def enroll_new_student(self, student_data: StudentCreate):
        # Convert Pydantic object to a dictionary
        data_dict = student_data.dict()
        
        # FIX: The database column is named "class", but our Pydantic field is "class_grade"
        # We need to rename it before sending to Supabase
        if 'class_grade' in data_dict:
            data_dict['class'] = data_dict.pop('class_grade')

        # Insert the corrected dictionary
        response = supabase.table(self.table).insert(data_dict).execute()
        
        # Return only the 'data' part (ignoring status codes, etc.)
        return response.data[0]