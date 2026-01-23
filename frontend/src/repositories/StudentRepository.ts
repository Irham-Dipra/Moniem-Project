import { supabase } from '../supabaseClient'

export const StudentRepository = {
  async getAllStudents() {
    const { data, error } = await supabase
      .from('Student')
      .select('*')
    
    if (error) throw error
    return data
  },

  async addStudent(studentData: any) {
    const { data, error } = await supabase
      .from('Student')
      .insert([studentData])
    
    if (error) throw error
    return data
  }
}