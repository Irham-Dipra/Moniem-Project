import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ProgramRepository } from '../repositories/ProgramRepository';
import { X, Loader2 } from 'lucide-react';

interface CreateProgramModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const CreateProgramModal: React.FC<CreateProgramModalProps> = ({ isOpen, onClose }) => {
    const queryClient = useQueryClient();
    const [formData, setFormData] = useState({
        program_name: '',
        batch_id: '',
        monthly_fee: 0,
        start_date: '',
        end_date: ''
    });

    // 1. Fetch Batches for Dropdown
    const { data: batches } = useQuery({
        queryKey: ['batches'],
        queryFn: ProgramRepository.getAllBatches
    });

    // 2. Mutation for Creating Program
    const createMutation = useMutation({
        mutationFn: ProgramRepository.createProgram,
        onSuccess: () => {
            // Refresh the list immediately
            queryClient.invalidateQueries({ queryKey: ['programs'] });
            onClose();
            // Reset form (optional)
            setFormData({ program_name: '', batch_id: '', monthly_fee: 0, start_date: '', end_date: '' });
        },
        onError: (err) => {
            alert("Failed to create program: " + err);
        }
    });

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Convert form data to match API schema
        const payload = {
            ...formData,
            // Convert batch_id to integer
            batch_id: formData.batch_id ? parseInt(formData.batch_id) : null,
            // Ensure fee is a number
            monthly_fee: parseFloat(formData.monthly_fee.toString()),
            // Convert empty strings to null for dates
            start_date: formData.start_date || null,
            end_date: formData.end_date || null
        };

        createMutation.mutate(payload);
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                    <X size={24} />
                </button>

                <h2 className="text-xl font-bold mb-4">Create New Program</h2>

                <form onSubmit={handleSubmit} className="space-y-4">

                    {/* Program Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Program Name</label>
                        <input
                            type="text"
                            required
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border text-gray-900 bg-white"
                            placeholder="e.g. Physics Cycle 1"
                            value={formData.program_name}
                            onChange={e => setFormData({ ...formData, program_name: e.target.value })}
                        />
                    </div>

                    {/* Batch Dropdown */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Batch</label>
                        <select
                            required
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border text-gray-900 bg-white"
                            value={formData.batch_id}
                            onChange={e => setFormData({ ...formData, batch_id: e.target.value })}
                        >
                            <option value="">Select a Batch</option>
                            {batches?.map((b: any) => (
                                <option key={b.batch_id} value={b.batch_id}>{b.batch_name}</option>
                            ))}
                        </select>
                        <p className="text-xs text-gray-500 mt-1">Don't see your batch? Create it in Settings.</p>
                    </div>

                    {/* Fee */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700">Monthly Fee (৳)</label>
                        <input
                            type="number"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border text-gray-900 bg-white"
                            value={formData.monthly_fee}
                            onChange={e => setFormData({ ...formData, monthly_fee: Number(e.target.value) })}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700">Start Date</label>
                            <input
                                type="date"
                                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border text-gray-900 bg-white"
                                value={formData.start_date}
                                onChange={e => setFormData({ ...formData, start_date: e.target.value })}
                            />
                        </div>
                    </div>

                    <div className="flex justify-end pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="mr-3 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={createMutation.isPending}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center"
                        >
                            {createMutation.isPending && <Loader2 className="animate-spin mr-2" size={16} />}
                            Create Program
                        </button>
                    </div>

                </form>
            </div>
        </div>
    );
};

export default CreateProgramModal;
