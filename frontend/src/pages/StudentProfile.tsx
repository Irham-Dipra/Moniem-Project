import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { StudentRepository } from '../repositories/StudentRepository';
import { ProgramRepository } from '../repositories/ProgramRepository';
import { User, Calendar, BookOpen, CreditCard, Edit2, Save, Plus } from 'lucide-react';

const StudentProfile: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const queryClient = useQueryClient();
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm] = useState<any>({});
    const [showEnrollModal, setShowEnrollModal] = useState(false);
    const [selectedProgramId, setSelectedProgramId] = useState('');

    // 1. Fetch Student Details
    const { data: student, isLoading } = useQuery({
        queryKey: ['student', id],
        queryFn: () => StudentRepository.getStudentById(id!),
        enabled: !!id
    });

    // 2. Fetch Enrollments
    const { data: enrollments } = useQuery({
        queryKey: ['enrollments', id],
        queryFn: () => StudentRepository.getEnrollments(id!),
        enabled: !!id
    });

    // 3. Fetch All Programs (for dropdown)
    const { data: allPrograms } = useQuery({
        queryKey: ['programs'],
        queryFn: ProgramRepository.getAllPrograms
    });

    // Mutations
    const updateMutation = useMutation({
        mutationFn: (updates: any) => StudentRepository.updateStudent(id!, updates),
        onSuccess: () => {
            setIsEditing(false);
            queryClient.invalidateQueries({ queryKey: ['student', id] });
        }
    });

    const enrollMutation = useMutation({
        mutationFn: (programId: number) => StudentRepository.enrollStudent({
            student_id: parseInt(id!),
            program_id: programId
        }),
        onSuccess: () => {
            setShowEnrollModal(false);
            queryClient.invalidateQueries({ queryKey: ['enrollments', id] });
        }
    });

    if (isLoading) return <div className="p-8">Loading profile...</div>;
    if (!student) return <div className="p-8">Student not found</div>;

    const handleEditToggle = () => {
        setEditForm(student);
        setIsEditing(true);
    };

    const handleSave = () => {
        updateMutation.mutate(editForm);
    };

    return (
        <div className="max-w-5xl mx-auto">
            {/* HEADER CARD */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
                <div className="flex justify-between items-start">
                    <div className="flex gap-4">
                        <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center text-gray-400">
                            <User size={40} />
                        </div>
                        <div>
                            {isEditing ? (
                                <div className="space-y-2">
                                    <input
                                        className="block w-full border p-1 rounded font-bold text-xl text-gray-900 bg-white"
                                        value={editForm.name}
                                        onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                                    />
                                    <div className="flex gap-2">
                                        <input
                                            className="border p-1 rounded text-sm text-gray-900 bg-white" placeholder="Roll No"
                                            value={editForm.roll_no}
                                            onChange={e => setEditForm({ ...editForm, roll_no: parseInt(e.target.value) })}
                                        />
                                        <input
                                            className="border p-1 rounded text-sm text-gray-900 bg-white" placeholder="Class"
                                            value={editForm.class}
                                            onChange={e => setEditForm({ ...editForm, class: parseInt(e.target.value) })}
                                        />
                                    </div>
                                </div>
                            ) : (
                                <>
                                    <h1 className="text-2xl font-bold text-gray-900">{student.name}</h1>
                                    <p className="text-gray-500">Roll: {student.roll_no} • Class {student.class}</p>
                                    <p className="text-sm text-gray-400 mt-1">Student ID: #{student.student_id}</p>
                                </>
                            )}
                        </div>
                    </div>
                    <div>
                        {isEditing ? (
                            <button onClick={handleSave} className="bg-green-600 text-white px-4 py-2 rounded flex items-center gap-2">
                                <Save size={16} /> Save
                            </button>
                        ) : (
                            <button onClick={handleEditToggle} className="border border-gray-300 px-4 py-2 rounded flex items-center gap-2 hover:bg-gray-50 text-gray-700">
                                <Edit2 size={16} /> Edit Profile
                            </button>
                        )}
                    </div>
                </div>

                {/* DETAILS GRID */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 pt-6 border-t border-gray-100">
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase">Father's Name</label>
                        {isEditing ? (
                            <input
                                className="block w-full border p-1 rounded text-gray-900 bg-white"
                                value={editForm.fathers_name || ''}
                                onChange={e => setEditForm({ ...editForm, fathers_name: e.target.value })}
                            />
                        ) : (
                            <p className="text-gray-800 font-medium">{student.fathers_name || '-'}</p>
                        )}
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase">School/College</label>
                        {isEditing ? (
                            <input
                                className="block w-full border p-1 rounded text-gray-900 bg-white"
                                value={editForm.school || ''}
                                onChange={e => setEditForm({ ...editForm, school: e.target.value })}
                            />
                        ) : (
                            <p className="text-gray-800 font-medium">{student.school || '-'}</p>
                        )}
                    </div>
                    <div>
                        <label className="text-xs font-bold text-gray-400 uppercase">Contact</label>
                        {isEditing ? (
                            <input
                                className="block w-full border p-1 rounded text-gray-900 bg-white"
                                value={editForm.contact || ''}
                                onChange={e => setEditForm({ ...editForm, contact: e.target.value })}
                            />
                        ) : (
                            <p className="text-gray-800 font-medium">{student.contact || '-'}</p>
                        )}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* LEFT COLUMN: Enrollments */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-bold text-gray-800 flex items-center gap-2">
                                <BookOpen size={20} className="text-blue-600" />
                                Enrolled Programs
                            </h3>
                            <button
                                onClick={() => setShowEnrollModal(true)}
                                className="text-sm bg-blue-50 text-blue-600 px-3 py-1 rounded-full font-medium hover:bg-blue-100"
                            >
                                + Enroll
                            </button>
                        </div>

                        {showEnrollModal && (
                            <div className="bg-blue-50 p-4 rounded-lg mb-4 border border-blue-100">
                                <p className="text-sm font-bold text-blue-800 mb-2">Select Program to Enroll</p>
                                <div className="flex gap-2">
                                    <select
                                        className="flex-1 border p-2 rounded text-gray-900 bg-white"
                                        value={selectedProgramId}
                                        onChange={e => setSelectedProgramId(e.target.value)}
                                    >
                                        <option value="">Choose a Program...</option>
                                        {allPrograms?.map((p: any) => (
                                            <option key={p.program_id} value={p.program_id}>
                                                {p.program_name} (Batch: {p.batch?.batch_name})
                                            </option>
                                        ))}
                                    </select>
                                    <button
                                        onClick={() => enrollMutation.mutate(parseInt(selectedProgramId))}
                                        className="bg-blue-600 text-white px-4 py-2 rounded shadow-sm hover:bg-blue-700"
                                        disabled={!selectedProgramId}
                                    >
                                        Confirm
                                    </button>
                                    <button onClick={() => setShowEnrollModal(false)} className="text-gray-500 px-2">Cancel</button>
                                </div>
                            </div>
                        )}

                        <div className="space-y-3">
                            {enrollments?.map((enroll: any) => (
                                <div key={enroll.enrollment_id} className="border border-gray-100 p-4 rounded-lg flex justify-between items-center hover:bg-gray-50">
                                    <div>
                                        <p className="font-bold text-gray-900">{enroll.program?.program_name || 'Unknown Program'}</p>
                                        <p className="text-sm text-gray-500">Joined: {enroll.enrollment_date || 'N/A'}</p>
                                    </div>
                                    <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs font-bold uppercase">
                                        Active
                                    </span>
                                </div>
                            ))}
                            {(!enrollments || enrollments.length === 0) && (
                                <p className="text-center text-gray-400 py-4">Not enrolled in any programs yet.</p>
                            )}
                        </div>
                    </div>
                </div>

                {/* RIGHT COLUMN: Fees & Stats */}
                <div className="space-y-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="font-bold text-gray-800 flex items-center gap-2 mb-4">
                            <CreditCard size={20} className="text-green-600" />
                            Financial Status
                        </h3>

                        <div className="space-y-4">
                            <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg border border-red-100">
                                <span className="text-sm text-red-700 font-medium">Total Dues</span>
                                <span className="text-xl font-bold text-red-700">৳0.00</span>
                            </div>
                            <button className="w-full py-2 border border-gray-300 rounded text-gray-600 hover:bg-gray-50 font-medium">
                                View Payment History
                            </button>
                        </div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <h3 className="font-bold text-gray-800 mb-4">Quick Actions</h3>
                        <div className="space-y-2">
                            <button className="w-full py-2 bg-gray-800 text-white rounded hover:bg-gray-900 font-medium text-sm">
                                Generate ID Card (PDF)
                            </button>
                            <button className="w-full py-2 border border-red-200 text-red-600 rounded hover:bg-red-50 font-medium text-sm">
                                Suspend Student
                            </button>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default StudentProfile;
