# ==========================================
# The Entry Point (The "Reception Desk")
# ==========================================
# This file is where the application starts. 
# When you run the server, it looks for 'app' inside this file.

from fastapi import FastAPI
from app.routes.student_routes import router as student_router

# 1. Initialize the Application
#    This creates the main object that will receive ALL web requests.
app = FastAPI()

# 2. Base Endpoint (Health Check)
#    This is a simple sanity check. If you go to http://localhost:8000/,
#    and see this message, you know the server is alive.
@app.get("/")
def read_root():
    return {"status": "Backend is running!"}

# 3. Register the Routers (Departments)
#    We built the 'student_router' in another file. 
#    Now we plug it into the main app.
#    It's like adding a "Student Department" sign to the building directory.
app.include_router(student_router)