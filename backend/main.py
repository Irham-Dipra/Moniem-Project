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

# ==========================================
# 4. CORS Details (Security Gate)
# ==========================================
# Browsers block requests between different ports (5173 vs 8000) by default.
# We need to explicitly allow our Frontend URL.
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    # Allow the React App running on this Port:
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)

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

from app.routes.program_routes import router as program_router
app.include_router(program_router)

from app.routes.exam_routes import router as exam_router
app.include_router(exam_router)

from app.routes.attendance_routes import router as attendance_router
app.include_router(attendance_router)

from app.routes.payment_routes import router as payment_router
app.include_router(payment_router)