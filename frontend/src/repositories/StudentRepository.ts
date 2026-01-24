// This file is a "Repository". It's a design pattern.
// Instead of writing database code inside every button or page (which gets messy),
// we put all the "Student" related database commands here.

import { supabase } from '../supabaseClient'

export const StudentRepository = {
  // Function to get the list of all students
  // 'async' means this function takes time (network request) and we must wait for it.
  async getAllStudents() {
    // translate to SQL: SELECT * FROM Student;
    const { data, error } = await supabase
      .from('Student') // The table name in Supabase
      .select('*')     // Get all columns

    // If Supabase reports an issue (e.g., internet down), crash appropriately
    if (error) throw error

    // Give the list of students back to whoever asked for it
    return data
  },

  // Function to create a new student
  async addStudent(studentData: any) {
    // translate to SQL: INSERT INTO Student (name, ...) VALUES (...);
    const { data, error } = await supabase
      .from('Student')
      .insert([studentData]) // Supabase expects a list of rows to insert

    if (error) throw error
    return data
  }
}