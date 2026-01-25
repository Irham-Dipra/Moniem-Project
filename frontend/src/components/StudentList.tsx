import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { StudentRepository } from '../repositories/StudentRepository';
import { Search, Filter, Plus, Eye, ChevronRight } from 'lucide-react';
import CreateStudentModal from './CreateStudentModal';

interface Student {
    student_id: number;
    name: string;
    roll_no: number;
    class: number;
    fathers_name?: string;
    school?: string;
    contact?: string;
}

const StudentList: React.FC = () => {
    const [searchTerm, setSearchTerm] = useState('');
    const [classFilter, setClassFilter] = useState('');
    const [isModalOpen, setIsModalOpen] = useState(false);

    const { data: students, isLoading, error } = useQuery({
        queryKey: ['students'],
        queryFn: StudentRepository.getAllStudents,
    });

    if (isLoading) return <div className="p-8 text-center text-gray-500">Loading directory...</div>;
    if (error) return <div className="p-8 text-center text-red-500">Failed to load students.</div>;

    const studentList = students || [];

    // Filter Logic
    const filteredStudents = studentList.filter((s: Student) => {
        const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            s.roll_no.toString().includes(searchTerm);
        const matchesClass = classFilter ? s.class.toString() === classFilter : true;
        return matchesSearch && matchesClass;
    });

    return (
        <div className="space-y-6">
            {/* HEADER & ACTIONS */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-gray-800">Student Directory</h1>
                    <p className="text-gray-500 text-sm">{filteredStudents.length} Students Found</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700 transition-colors"
                >
                    <Plus size={18} />
                    <span>Add Student</span>
                </button>
            </div>

            {/* FILTERS BAR */}
            <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-200 flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="Search by Name or Roll No..."
                        className="pl-10 w-full rounded-lg border-gray-300 border p-2 text-gray-900 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
                <div className="flex items-center gap-2">
                    <Filter className="text-gray-400" size={20} />
                    <select
                        className="rounded-lg border-gray-300 border p-2 text-gray-700 bg-white min-w-[150px]"
                        value={classFilter}
                        onChange={(e) => setClassFilter(e.target.value)}
                    >
                        <option value="">All Classes</option>
                        {[...Array(12)].map((_, i) => (
                            <option key={i} value={i + 1}>Class {i + 1}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* DATA TABLE */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                        <tr>
                            <th className="p-4 border-b">Student Name</th>
                            <th className="p-4 border-b">Roll No</th>
                            <th className="p-4 border-b">Class</th>
                            <th className="p-4 border-b">Contact</th>
                            <th className="p-4 border-b">School</th>
                            <th className="p-4 border-b text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {filteredStudents.length > 0 ? (
                            filteredStudents.map((student: Student) => (
                                <tr key={student.student_id} className="hover:bg-gray-50 transition-colors group">
                                    <td className="p-4">
                                        <div className="font-medium text-gray-900">{student.name}</div>
                                        <div className="text-xs text-gray-500">{student.fathers_name ? `Father: ${student.fathers_name}` : ''}</div>
                                    </td>
                                    <td className="p-4 text-gray-600 font-mono text-sm">{student.roll_no}</td>
                                    <td className="p-4">
                                        <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded-full text-xs font-bold">
                                            Class {student.class}
                                        </span>
                                    </td>
                                    <td className="p-4 text-gray-600 text-sm">{student.contact || '-'}</td>
                                    <td className="p-4 text-gray-600 text-sm">{student.school || '-'}</td>
                                    <td className="p-4 text-right">
                                        <button className="text-gray-400 hover:text-blue-600 transition-colors p-2 rounded-full hover:bg-blue-50">
                                            <ChevronRight size={20} />
                                        </button>
                                    </td>
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={6} className="p-8 text-center text-gray-500">
                                    No students found matching your filters.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* MODAL */}
            <CreateStudentModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />
        </div>
    );
};

export default StudentList;