import React from 'react';
import { useQuery } from '@tanstack/react-query'; // <--- New Import
import { StudentRepository } from '../repositories/StudentRepository';

interface Student {
    student_id: number;
    name: string;
    roll_no: number;
    class: number; // Changed from string to number (based on SQL 'class INTEGER')
    fathers_name?: string; // Optional field
    school?: string;
    contact?: string;
}

const StudentList: React.FC = () => {
    // ==========================================
    // The React Query Way
    // ==========================================
    // 1. queryKey: A unique ID for this data. React Query uses this to cache it.
    //    If you ask for ['students'] again elsewhere, it won't fetch; it just gives you the cached copy!
    // 2. queryFn: The function that actually gets the data.
    const { data: students, isLoading, error } = useQuery({
        queryKey: ['students'],
        queryFn: StudentRepository.getAllStudents,
    });

    if (isLoading) return <p>Loading students...</p>;
    if (error) return <p className="text-red-500">Error loading data!</p>;

    // Notice: We default to [] if data is undefined
    const studentList = students || [];

    return (
        <div className="p-4">
            <h2 className="text-2xl font-bold mb-4">Enrolled Students</h2>
            <ul className="space-y-2">
                {studentList.map((student: Student) => (
                    <li key={student.student_id} className="border p-3 rounded shadow-sm bg-white">
                        <p><strong>Name:</strong> {student.name}</p>
                        <p className="text-sm text-gray-600">
                            Roll: {student.roll_no} | Class: {student.class}
                        </p>
                        {/* Show extra details if they exist */}
                        {student.fathers_name && <p className="text-xs text-gray-500">Father: {student.fathers_name}</p>}
                        {student.contact && <p className="text-xs text-gray-500">Contact: {student.contact}</p>}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default StudentList;