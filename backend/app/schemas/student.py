from pydantic import BaseModel
from typing import Optional

# ==========================================
# TUTORIAL: What is Pydantic?
# ==========================================
# Pydantic is a library that enforces "Type Hints" at runtime.
# Standard Python:
#    def add(x: int): ...
#    If I call add("hello"), Python crashes INSIDE the function.
#
# Pydantic:
#    If I send "hello" to an integer field, Pydantic stops it AT THE DOOR.
#    It says: "Error: value is not a valid integer" before your code even runs.

# 1. We start by inheriting from 'BaseModel'. 
#    This gives our class the magical validation powers.
class StudentCreate(BaseModel):
    
    # 2. REQUIRED FIELDS
    #    'name: str' means this field MUST be present and MUST be text.
    name: str

    # 3. OPTIONAL FIELDS
    #    'Optional[str]' means it can be a string OR it can be None (empty).
    #    '= None' sets the default value if the user doesn't send anything.
    fathers_name: Optional[str] = None
    school: Optional[str] = None
    contact: Optional[str] = None
    
    # 4. INTEGER FIELDS
    #    Pydantic will try to convert data for you.
    #    If the user sends "10" (string), Pydantic converts it to 10 (int).
    roll_no: Optional[int] = None
    
    # 5. RENAMING
    #    We call this 'class_grade' in Python because 'class' is a reserved keyword.
    #    (We will map this back to the database column 'class' later).
    class_grade: Optional[int] = None
