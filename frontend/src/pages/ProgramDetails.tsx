import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ProgramRepository } from '../repositories/ProgramRepository';
import { Users, FileText, DollarSign, Calendar, GraduationCap, Clock } from 'lucide-react';
import { Link } from 'react-router-dom';
import CreateExamModal from '../components/CreateExamModal';

const ProgramDetails: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [activeTab, setActiveTab] = useState<'students' | 'exams'>('students');
    const [isExamModalOpen, setIsExamModalOpen] = useState(false);

    const { data: program, isLoading } = useQuery({
        queryKey: ['program', id],
        queryFn: () => ProgramRepository.getProgramById(id!),
        enabled: !!id
    });

    if (isLoading) return <div className="p-8">Loading details...</div>;
    if (!program) return <div className="p-8">Program not found</div>;

    // --- Statistics Calculation ---
    const totalEnrolled = program.enrollment?.length || 0;
    const teachersCount = program.teacher_program_enrollment?.length || 0;
    const totalExams = program.exam?.length || 0;

    // Calculate Fees
    let totalCollected = 0;
    let totalDue = 0; // This requires more complex logic, for now we sum known dues if available

    // Iterate through enrollments to sum up payments (if loaded)
    program.enrollment?.forEach((enroll: any) => {
        enroll.payment?.forEach((pay: any) => {
            // Assuming 'paid_amount' exists in payment table
            totalCollected += Number(pay.paid_amount || 0);
        });
    });

    return (
        <div className="space-y-6">
            {/* HEADER */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center">
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-bold uppercase">
                                {program.batch?.batch_name || 'Batch'}
                            </span>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900">{program.program_name}</h1>
                        <div className="flex gap-4 mt-2 text-sm text-gray-500">
                            <div className="flex items-center gap-1">
                                <Calendar size={16} />
                                <span>Starts: {program.start_date || 'TBD'}</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <Clock size={16} />
                                <span>Ends: {program.end_date || 'Tentative'}</span>
                            </div>
                        </div>
                    </div>
                    <div className="text-right mt-4 md:mt-0">
                        <p className="text-sm text-gray-500">Monthly Fee</p>
                        <p className="text-2xl font-bold text-green-600">৳{program.monthly_fee}</p>
                    </div>
                </div>

                {/* STATS GRID */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-8 pt-6 border-t border-gray-100">
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase font-semibold">Total Students</p>
                        <div className="flex items-center gap-2 mt-1">
                            <Users size={20} className="text-blue-500" />
                            <span className="text-xl font-bold text-gray-900">{totalEnrolled}</span>
                        </div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase font-semibold">Total Revenue</p>
                        <div className="flex items-center gap-2 mt-1">
                            <DollarSign size={20} className="text-green-500" />
                            <span className="text-xl font-bold text-gray-900">৳{totalCollected}</span>
                        </div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase font-semibold">Teachers Info</p>
                        <div className="flex items-center gap-2 mt-1">
                            <GraduationCap size={20} className="text-purple-500" />
                            <span className="text-xl font-bold text-gray-900">{teachersCount} Assigned</span>
                        </div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase font-semibold">Exams Conducted</p>
                        <div className="flex items-center gap-2 mt-1">
                            <FileText size={20} className="text-orange-500" />
                            <span className="text-xl font-bold text-gray-900">{totalExams}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* TABS */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden min-h-[400px]">
                <div className="flex border-b border-gray-200">
                    <button
                        onClick={() => setActiveTab('students')}
                        className={`flex-1 py-4 text-sm font-medium text-center transition-colors ${activeTab === 'students'
                            ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                            : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        Enrolled Students ({totalEnrolled})
                    </button>
                    <button
                        onClick={() => setActiveTab('exams')}
                        className={`flex-1 py-4 text-sm font-medium text-center transition-colors ${activeTab === 'exams'
                            ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50'
                            : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                            }`}
                    >
                        Exams History ({totalExams})
                    </button>
                </div>

                <div className="p-6">
                    {/* STUDENTS TAB */}
                    {activeTab === 'students' && (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold">
                                    <tr>
                                        <th className="p-3 border-b">ID</th>
                                        <th className="p-3 border-b">Name</th>
                                        <th className="p-3 border-b">Roll</th>
                                        <th className="p-3 border-b">Contact</th>
                                        <th className="p-3 border-b">Joined Date</th>
                                        <th className="p-3 border-b">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {program.enrollment?.map((enroll: any) => (
                                        <tr key={enroll.enrollment_id} className="hover:bg-gray-50 border-b border-gray-50">
                                            <td className="p-3 text-gray-500 text-sm">#{enroll.student.student_id}</td>
                                            <td className="p-3 font-medium text-gray-900">{enroll.student.name}</td>
                                            <td className="p-3 text-gray-600 text-sm font-mono">{enroll.student.roll_no}</td>
                                            <td className="p-3 text-gray-600 text-sm">{enroll.student.contact || '-'}</td>
                                            <td className="p-3 text-gray-600 text-sm">{enroll.enrollment_date || '-'}</td>
                                            <td className="p-3">
                                                <span className="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-bold uppercase">
                                                    {enroll.status}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                    {totalEnrolled === 0 && (
                                        <tr>
                                            <td colSpan={6} className="text-center py-8 text-gray-400">
                                                No students enrolled yet.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* EXAMS TAB */}
                    {activeTab === 'exams' && (
                        <div>
                            <div className="flex justify-end mb-4">
                                <button
                                    onClick={() => setIsExamModalOpen(true)}
                                    className="bg-blue-600 text-white px-3 py-1.5 rounded text-sm hover:bg-blue-700"
                                >
                                    + Schedule Exam
                                </button>
                            </div>
                            {totalExams === 0 ? (
                                <div className="text-center py-8 text-gray-400 border border-dashed rounded-lg">
                                    No exams scheduled for this program yet.
                                </div>
                            ) : (
                                <ul className="space-y-2">
                                    {program.exam?.map((exam: any) => (
                                        <li key={exam.exam_id} className="border p-4 rounded-lg flex justify-between items-center hover:bg-gray-50 transition-colors">
                                            <Link to={`/exams/${exam.exam_id}`} className="block flex-1">
                                                <div>
                                                    <p className="font-bold text-blue-600 hover:underline">{exam.exam_name}</p>
                                                    <p className="text-xs text-gray-500">{exam.exam_date} • {exam.exam_type}</p>
                                                </div>
                                            </Link>
                                            <div className="text-right">
                                                <p className="text-sm font-bold text-gray-700">Total Marks: {exam.total_marks}</p>
                                            </div>
                                        </li>
                                    ))}
                                </ul>
                            )}

                            {/* Create Exam Modal */}
                            <CreateExamModal
                                isOpen={isExamModalOpen}
                                onClose={() => setIsExamModalOpen(false)}
                                programId={id!}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProgramDetails;
