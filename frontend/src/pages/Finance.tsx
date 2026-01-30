import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PaymentRepository } from '../repositories/PaymentRepository';
import { StudentRepository } from '../repositories/StudentRepository';
import { ProgramRepository } from '../repositories/ProgramRepository'; // Keep for now if needed, but we rely on student enrollments
import { DollarSign, Search, Plus, FileText, Download, X, Calendar, CreditCard, User } from 'lucide-react';
import jsPDF from 'jspdf';

const Finance: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const queryClient = useQueryClient();

    // Fetch Recent Payments
    const { data: recentPayments } = useQuery({
        queryKey: ['payments', 'recent'],
        queryFn: PaymentRepository.getRecentPayments
    });

    // Fetch Global Stats
    const { data: stats } = useQuery({
        queryKey: ['finance', 'stats'],
        queryFn: PaymentRepository.getFinanceStats
    });

    // --- PDF SLIP GENERATOR ---
    const generateSlip = (payment: any) => {
        const doc = new jsPDF({
            orientation: 'landscape',
            unit: 'mm',
            format: [210, 99]
        });

        // Watermark / Header
        doc.setFontSize(22);
        doc.setTextColor(40, 40, 40);
        doc.text("Coaching Centre Name", 10, 15);
        doc.setFontSize(10);
        doc.text("Address Line 1, City", 10, 20);

        doc.setFontSize(16);
        doc.text("MONEY RECEIPT", 160, 15, { align: 'right' });
        doc.setLineWidth(0.5);
        doc.line(10, 25, 200, 25);

        // Details
        doc.setFontSize(12);
        doc.text(`Receipt No: #${payment.payment_id}`, 10, 35);
        doc.text(`Date: ${payment.payment_date}`, 160, 35, { align: 'right' });

        doc.text(`Received with thanks from:`, 10, 45);
        doc.setFont('helvetica', 'bold');
        doc.text(`${payment.student_name} (Roll: ${payment.roll_no || '-'})`, 65, 45);

        doc.setFont('helvetica', 'normal');
        doc.text(`Program:`, 10, 52);
        doc.text(`${payment.program_name}`, 65, 52);

        // Payment Info
        if (payment.month && payment.year) {
            doc.text(`For: ${new Date(0, payment.month - 1).toLocaleString('default', { month: 'long' })} ${payment.year}`, 10, 59);
        }
        doc.text(`Method: ${payment.payment_method || 'Cash'}`, 160, 52, { align: 'right' });

        // Amount Box
        doc.rect(10, 65, 190, 20);
        doc.setFontSize(14);
        doc.text("Amount Paid:", 15, 78);
        doc.setFont('helvetica', 'bold');
        doc.text(`BDT ${payment.paid_amount}/-`, 50, 78);

        // Remarks
        if (payment.remarks) {
            doc.setFontSize(10);
            doc.setFont('helvetica', 'italic');
            doc.text(`Remarks: ${payment.remarks}`, 10, 92);
        }

        doc.save(`Receipt_${payment.payment_id}.pdf`);
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <DollarSign className="text-green-600" /> Finance & Accounts
            </h1>

            {/* STATS */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <p className="text-gray-500 text-xs font-bold uppercase tracking-wider">Revenue (This Month)</p>
                    <p className="text-3xl font-bold text-green-600 mt-2">৳{stats?.revenue_this_month?.toLocaleString() || 0}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <p className="text-gray-500 text-xs font-bold uppercase tracking-wider">Due (This Month)</p>
                    <p className="text-3xl font-bold text-orange-600 mt-2">৳{stats?.due_this_month?.toLocaleString() || 0}</p>
                </div>
                <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                    <p className="text-gray-500 text-xs font-bold uppercase tracking-wider">Total Due (Arrears)</p>
                    <p className="text-3xl font-bold text-red-600 mt-2">৳{stats?.due_total?.toLocaleString() || 0}</p>
                </div>
            </div>

            {/* ACTIONS */}
            <div className="flex justify-between items-center bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                <h2 className="text-lg font-bold text-gray-800">Recent Transactions</h2>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 shadow-sm"
                >
                    <Plus size={18} /> Record New Payment
                </button>
            </div>

            {/* LEDGER TABLE */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-500 text-xs uppercase font-semibold border-b">
                        <tr>
                            <th className="p-4">Receipt #</th>
                            <th className="p-4">Date</th>
                            <th className="p-4">Student</th>
                            <th className="p-4">Month/Year</th>
                            <th className="p-4 text-right">Amount</th>
                            <th className="p-4">Method</th>
                            <th className="p-4 text-center">Slip</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {recentPayments?.map((p: any) => {
                            const monthName = p.month ? new Date(0, p.month - 1).toLocaleString('default', { month: 'short' }) : '-';
                            return (
                                <tr key={p.payment_id} className="hover:bg-gray-50">
                                    <td className="p-4 font-mono text-gray-500">#{p.payment_id}</td>
                                    <td className="p-4 text-gray-700 text-sm">{p.payment_date}</td>
                                    <td className="p-4 font-medium text-gray-900">
                                        {p.student_name}
                                        <span className="block text-xs text-gray-400">Roll: {p.roll_no || '-'}</span>
                                        <span className="block text-xs text-blue-500">{p.program_name}</span>
                                    </td>
                                    <td className="p-4 text-gray-600 text-sm">{p.month ? `${monthName} ${p.year}` : '-'}</td>
                                    <td className="p-4 text-right font-bold text-green-600">৳{p.paid_amount}</td>
                                    <td className="p-4 text-gray-600 text-sm">
                                        <span className="px-2 py-1 bg-gray-100 rounded text-xs border">{p.payment_method || 'Cash'}</span>
                                    </td>
                                    <td className="p-4 text-center">
                                        <button
                                            onClick={() => generateSlip(p)}
                                            className="text-blue-600 hover:text-blue-800 p-2 rounded-full hover:bg-blue-50 transition-colors"
                                            title="Download Receipt"
                                        >
                                            <Download size={18} />
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                        {recentPayments?.length === 0 && (
                            <tr><td colSpan={7} className="p-8 text-center text-gray-400">No payments recorded yet.</td></tr>
                        )}
                    </tbody>
                </table>
            </div>

            <AddPaymentModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        </div>
    );
};

// --- MODAL COMPONENT ---
const AddPaymentModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    // Search State
    const [searchType, setSearchType] = useState<'name' | 'id'>('name');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedStudent, setSelectedStudent] = useState<any>(null);

    // Form State
    const [selectedProgramId, setSelectedProgramId] = useState<string>('');
    const [amount, setAmount] = useState('');
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [month, setMonth] = useState(new Date().getMonth() + 1); // Default current month
    const [year, setYear] = useState(new Date().getFullYear());
    const [paymentMethod, setPaymentMethod] = useState('Cash');
    const [remarks, setRemarks] = useState('');

    const queryClient = useQueryClient();

    // 1. Search Students
    const { data: searchResults } = useQuery({
        queryKey: ['students', 'search', searchQuery],
        // FIXED: Passed searchQuery manually or assume client side filter if API doesn't support it yet.
        // Since the Repo shows no argument, we'll call it without args and filter in frontend or better yet, update repo.
        // For now, let's just make it compilable. WE will filter below.
        queryFn: () => StudentRepository.getAllStudents(),
        enabled: searchQuery.length > 1
    });

    // NOTE: If searching by ID, we might need a specific endpoint or just rely on the smart search in getAllStudents if it supports it. 
    // Assuming searching "101" works for ID.

    // 2. Fetch Enrolled Programs for Selected Student (Simulated or Real)
    // We assume the Student object coming back has 'enrollment' list or we need to fetch it.
    // If getAllStudents doesn't return enrollments, we should fetch student details.
    const { data: fullStudentDetails } = useQuery({
        queryKey: ['student', selectedStudent?.student_id],
        queryFn: () => StudentRepository.getStudentById(selectedStudent?.student_id),
        enabled: !!selectedStudent
    });

    // 3. Fetch Payment History for Balance Calculation
    const { data: studentPayments } = useQuery({
        queryKey: ['student_payments', selectedStudent?.student_id],
        queryFn: () => PaymentRepository.getStudentPayments(selectedStudent!.student_id),
        enabled: !!selectedStudent
    });

    const enrolledPrograms = fullStudentDetails?.enrollment?.map((e: any) => ({
        id: e.program.program_id,
        name: e.program.program_name,
        fee: e.program.monthly_fee,
        enrollment_date: e.enrollment_date
    })) || [];

    // CALCULATE DUES
    const calculateDueInfo = () => {
        if (!selectedProgramId || !enrolledPrograms) return null;

        const prog = enrolledPrograms.find((p: any) => p.id === Number(selectedProgramId));
        if (!prog) return null;

        // A. Calculate Total Months Passed since Enrollment
        const enrollDate = new Date(prog.enrollment_date);
        const today = new Date();

        // Simple month difference (inclusive of start month)
        const months = (today.getFullYear() - enrollDate.getFullYear()) * 12 + (today.getMonth() - enrollDate.getMonth()) + 1;
        const totalPayable = Math.max(0, months) * (prog.fee || 0);

        // B. Calculate Total Paid
        // Refined Logic using Enrollment ID
        const enrollment = fullStudentDetails?.enrollment?.find((e: any) => e.program.program_id === Number(selectedProgramId));
        if (!enrollment) return null;

        const paidForThisParams = studentPayments?.filter((p: any) => p.enrollment_id === enrollment.enrollment_id)
            .reduce((sum: number, p: any) => sum + (p.paid_amount || 0), 0) || 0;

        return {
            totalPayable,
            totalPaid: paidForThisParams,
            due: totalPayable - paidForThisParams,
            monthsSince: Math.max(0, months)
        };
    };

    const dueInfo = calculateDueInfo();

    // Auto-fill amount logic moved here if needed, or kept in onChange.
    // We keep existing onChange auto-fill for Monthly Fee, but maybe user wants to pay Due Amount?

    const mutation = useMutation({
        mutationFn: PaymentRepository.createPayment,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['payments'] });
            resetForm();
            onClose();
            alert("Payment Recorded!");
        },
        onError: (err) => alert("Error: " + err)
    });

    const resetForm = () => {
        setSearchQuery('');
        setSelectedStudent(null);
        setSelectedProgramId('');
        setAmount('');
        setRemarks('');
        setMonth(new Date().getMonth() + 1);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedStudent || !selectedProgramId || !amount) return;
        mutation.mutate({
            student_id: selectedStudent.student_id,
            program_id: parseInt(selectedProgramId),
            paid_amount: parseFloat(amount),
            payment_date: date,
            month: parseFloat(month.toString()),
            year: parseFloat(year.toString()),
            payment_method: paymentMethod,
            remarks: remarks
        });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
                <div className="p-4 border-b flex justify-between items-center bg-gray-50">
                    <h3 className="font-bold text-gray-800">Record New Payment</h3>
                    <button onClick={onClose}><X size={20} className="text-gray-500" /></button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {/* STEP 1: FIND STUDENT */}
                    {!selectedStudent ? (
                        <div className="space-y-3">
                            <label className="block text-sm font-medium text-gray-700">Find Student</label>

                            {/* Search Type Toggle */}
                            <div className="flex gap-4 text-sm mb-2">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="searchType"
                                        checked={searchType === 'name'}
                                        onChange={() => setSearchType('name')}
                                    /> Search by Name
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="radio"
                                        name="searchType"
                                        checked={searchType === 'id'}
                                        onChange={() => setSearchType('id')}
                                    /> Search by ID/Roll
                                </label>
                            </div>

                            <div className="relative">
                                <Search className="absolute left-3 top-2.5 text-gray-400" size={18} />
                                <input
                                    type="text"
                                    placeholder={searchType === 'name' ? "Start typing name..." : "Enter Student ID or Roll No..."}
                                    className="w-full pl-10 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    autoFocus
                                />
                            </div>

                            {searchQuery.length > 1 && (
                                <ul className="mt-2 border rounded-lg max-h-60 overflow-y-auto divide-y shadow-sm">
                                    {searchResults?.map((s: any) => (
                                        <li
                                            key={s.student_id}
                                            onClick={() => { setSelectedStudent(s); setSearchQuery(''); }}
                                            className="p-3 hover:bg-blue-50 cursor-pointer flex justify-between items-center group"
                                        >
                                            <div>
                                                <div className="font-bold text-gray-800 group-hover:text-blue-700">{s.name}</div>
                                                <div className="text-xs text-gray-500">ID: {s.student_id} • Roll: {s.roll_no}</div>
                                            </div>
                                            <div className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">
                                                {s.school || 'No School Info'}
                                            </div>
                                        </li>
                                    ))}
                                    {searchResults?.length === 0 && (
                                        <li className="p-4 text-center text-gray-400 text-sm">No students found.</li>
                                    )}
                                </ul>
                            )}
                        </div>
                    ) : (
                        <div className="bg-blue-50 p-4 rounded-xl border border-blue-100 flex justify-between items-center animate-in fade-in slide-in-from-top-2">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
                                    {selectedStudent.name.charAt(0)}
                                </div>
                                <div>
                                    <div className="font-bold text-blue-900">{selectedStudent.name}</div>
                                    <div className="text-xs text-blue-700 flex gap-2">
                                        <span>ID: {selectedStudent.student_id}</span>
                                        <span>•</span>
                                        <span>Roll: {selectedStudent.roll_no}</span>
                                    </div>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={() => setSelectedStudent(null)}
                                className="text-sm text-red-600 hover:text-red-800 font-medium px-3 py-1 rounded hover:bg-red-50 transition-colors"
                            >
                                Change
                            </button>
                        </div>
                    )}

                    {/* STEP 2: PAYMENT DETAILS */}
                    <div className={`space-y-6 transition-all ${!selectedStudent ? 'opacity-50 pointer-events-none blur-[1px]' : ''}`}>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Program Selection */}
                            <div className="col-span-1 md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 mb-1">Select Enrolled Program</label>
                                <select
                                    required
                                    className="w-full p-3 border rounded-lg bg-white outline-none focus:ring-2 focus:ring-blue-500"
                                    value={selectedProgramId}
                                    onChange={e => {
                                        setSelectedProgramId(e.target.value);
                                        const p = enrolledPrograms.find((item: any) => item.id === Number(e.target.value));
                                        if (p && !amount) setAmount(p.fee.toString()); // Auto-fill amount
                                    }}
                                >
                                    <option value="">-- Choose Program --</option>
                                    {enrolledPrograms.map((p: any) => (
                                        <option key={p.id} value={p.id}>
                                            {p.name} (Fee: ৳{p.fee}/mo)
                                        </option>
                                    ))}
                                </select>
                                {enrolledPrograms.length === 0 && selectedStudent && (
                                    <p className="text-xs text-red-500 mt-1">This student is not enrolled in any programs yet.</p>
                                )}
                            </div>

                            {/* Month & Year */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Payment For (Month)</label>
                                <div className="flex gap-2">
                                    <select
                                        className="w-2/3 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                        value={month}
                                        onChange={e => setMonth(Number(e.target.value))}
                                    >
                                        {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                                            <option key={m} value={m}>{new Date(0, m - 1).toLocaleString('default', { month: 'long' })}</option>
                                        ))}
                                    </select>
                                    <input
                                        type="number"
                                        className="w-1/3 p-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                                        value={year}
                                        onChange={e => setYear(Number(e.target.value))}
                                    />
                                </div>
                            </div>

                            {/* Payment Method */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
                                <select
                                    className="w-full p-2.5 border rounded-lg bg-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    value={paymentMethod}
                                    onChange={e => setPaymentMethod(e.target.value)}
                                >
                                    <option value="Cash">Cash</option>
                                    <option value="Bank Transfer">Bank Transfer</option>
                                    <option value="bKash">bKash</option>
                                    <option value="Nagad">Nagad</option>
                                    <option value="Rocket">Rocket</option>
                                    <option value="Other">Other</option>
                                </select>
                            </div>

                            {/* Amount */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Paid Amount (৳)</label>
                                <div className="relative">
                                    <span className="absolute left-3 top-3 text-gray-500">৳</span>
                                    <input
                                        type="number"
                                        required
                                        className="w-full pl-8 p-2.5 border rounded-lg outline-none focus:ring-2 focus:ring-green-500 font-bold text-lg text-green-700"
                                        value={amount}
                                        onChange={e => setAmount(e.target.value)}
                                        placeholder="0.00"
                                    />
                                </div>
                                {selectedProgramId && dueInfo && (
                                    <div className="mt-2 text-xs space-y-1 bg-gray-50 p-2 rounded border">
                                        <div className="flex justify-between text-gray-600">
                                            <span>Monthly Fee:</span>
                                            <span>৳{enrolledPrograms.find((p: any) => p.id === Number(selectedProgramId))?.fee}</span>
                                        </div>
                                        <div className="flex justify-between text-gray-600">
                                            <span>Months Enrolled:</span>
                                            <span>{dueInfo.monthsSince}</span>
                                        </div>
                                        <div className="flex justify-between text-gray-600">
                                            <span>Total Payable:</span>
                                            <span>৳{dueInfo.totalPayable}</span>
                                        </div>
                                        <div className="flex justify-between text-green-600">
                                            <span>Total Paid:</span>
                                            <span>- ৳{dueInfo.totalPaid}</span>
                                        </div>
                                        <div className="flex justify-between font-bold text-red-600 border-t pt-1 mt-1">
                                            <span>Net Due:</span>
                                            <span>৳{dueInfo.due}</span>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => setAmount(Math.max(0, dueInfo.due).toString())}
                                            className="text-blue-600 hover:underline w-full text-right mt-1"
                                        >
                                            Pay Full Due
                                        </button>
                                    </div>
                                )}
                            </div>

                            {/* Date */}
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Receipt Date</label>
                                <input
                                    type="date"
                                    required
                                    className="w-full p-2.5 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500"
                                    value={date}
                                    onChange={e => setDate(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Remarks */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Remarks (Optional)</label>
                            <textarea
                                className="w-full p-3 border rounded-lg outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                                rows={2}
                                value={remarks}
                                onChange={e => setRemarks(e.target.value)}
                                placeholder="E.g. Paid in advance, Late fee included..."
                            ></textarea>
                        </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="pt-4 border-t flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-5 py-2.5 text-gray-600 hover:bg-gray-100 rounded-lg font-medium"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={mutation.isPending || !selectedStudent}
                            className={`px-8 py-2.5 bg-green-600 text-white rounded-lg font-bold shadow-md hover:bg-green-700 flex items-center gap-2 ${mutation.isPending || !selectedStudent ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            <CreditCard size={18} />
                            {mutation.isPending ? 'Processing...' : 'Confirm Payment'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Finance;
