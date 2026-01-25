// This file is a "Repository". It's a design pattern.
// Instead of writing database code inside every button or page (which gets messy),
// we put all the "Student" related database commands here.

// ==========================================
// THE SWITCH: From Supabase Direct -> FastAPI
// ==========================================
// We are no longer using 'supabase' here. 
// We are using standard web 'fetch' to talk to our Python Backend.

const API_BASE_URL = "http://127.0.0.1:8000";

export const StudentRepository = {

  // 1. Get All Students
  async getAllStudents() {
    // Call the Python API: GET /students
    const response = await fetch(`${API_BASE_URL}/students`);

    // Check if the server said "OK"
    if (!response.ok) {
      throw new Error("Failed to fetch students from Backend");
    }

    // Return the JSON data (List of students)
    return await response.json();
  },

  // 2. Add Student
  async addStudent(studentData: any) {
    // Call the Python API: POST /students
    const response = await fetch(`${API_BASE_URL}/students`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(studentData),
    });

    if (!response.ok) {
      throw new Error("Failed to add student via Backend");
    }

    return await response.json();
  }
}