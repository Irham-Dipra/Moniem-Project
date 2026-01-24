import React, { useEffect, useState } from 'react';
import { StudentRepository } from '../repositories/StudentRepository';

// Define what a 'Student' looks like for TypeScript
interface Student {
  Student_id: number;
  Name: string;
  Roll_no: number;
  Class: string;
}

const StudentList: React.FC = () => {
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // This is the "Effect" that runs as soon as the component loads
    const fetchStudents = async () => {
      try {
        const data = await StudentRepository.getAllStudents();
        setStudents(data || []);
      } catch (error) {
        console.error("Error fetching students:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchStudents();
  }, []);

  if (loading) return <p>Loading students...</p>;

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Enrolled Students</h2>
      <ul className="space-y-2">
        {students.map((student) => (
          <li key={student.Student_id} className="border p-3 rounded shadow-sm bg-white">
            <p><strong>Name:</strong> {student.Name}</p>
            <p className="text-sm text-gray-600">Roll: {student.Roll_no} | Class: {student.Class}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default StudentList;