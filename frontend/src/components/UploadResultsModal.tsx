import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { ExamRepository } from '../repositories/ExamRepository';
import { X, Upload, FileSpreadsheet, Loader2, Download } from 'lucide-react';
import * as XLSX from 'xlsx';

interface UploadResultsModalProps {
    isOpen: boolean;
    onClose: () => void;
    examId: string;
}

const UploadResultsModal: React.FC<UploadResultsModalProps> = ({ isOpen, onClose, examId }) => {
    const queryClient = useQueryClient();
    const [file, setFile] = useState<File | null>(null);
    const [previewData, setPreviewData] = useState<any[]>([]);
    const [isParsing, setIsParsing] = useState(false);

    // Mutation to send data to backend
    const uploadMutation = useMutation({
        mutationFn: (results: any[]) => ExamRepository.submitBulkResults({
            exam_id: parseInt(examId),
            results: results
        }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['analytics', examId] });
            queryClient.invalidateQueries({ queryKey: ['merit', examId] });
            onClose();
            setFile(null);
            setPreviewData([]);
            alert("Results uploaded successfully!");
        },
        onError: (err) => {
            alert("Failed to upload results: " + err);
        }
    });

    if (!isOpen) return null;

    const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        setFile(selectedFile);
        setIsParsing(true);

        const reader = new FileReader();
        reader.onload = (evt) => {
            try {
                const bstr = evt.target?.result;
                const wb = XLSX.read(bstr, { type: 'binary' });
                const wsname = wb.SheetNames[0];
                const ws = wb.Sheets[wsname];
                const data = XLSX.utils.sheet_to_json(ws);

                // Map keys to lowercase/standardize
                const formattedData = data.map((row: any) => ({
                    student_id: row['Student ID'] || row['student_id'] || row['ID'],
                    written_marks: Number(row['Written'] || row['written'] || 0),
                    mcq_marks: Number(row['MCQ'] || row['mcq'] || 0)
                })).filter((r: any) => r.student_id); // Filter out empty rows

                setPreviewData(formattedData);
            } catch (err) {
                alert("Error parsing file. Make sure it's a valid Excel file.");
                setFile(null);
            } finally {
                setIsParsing(false);
            }
        };
        reader.readAsBinaryString(selectedFile);
    };

    const handleDownloadTemplate = () => {
        const ws = XLSX.utils.json_to_sheet([
            { "Student ID": 101, "Written": 35, "MCQ": 12 },
            { "Student ID": 102, "Written": 40, "MCQ": 15 },
        ]);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, "Template");
        XLSX.writeFile(wb, "Result_Entry_Template.xlsx");
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
                    <X size={24} />
                </button>

                <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Upload className="text-blue-600" /> Upload Results
                </h2>

                <div className="space-y-6">
                    {/* Template Download */}
                    <div className="bg-blue-50 p-4 rounded-lg border border-blue-100 flex justify-between items-center">
                        <div>
                            <h3 className="text-sm font-bold text-blue-800">Need a format?</h3>
                            <p className="text-xs text-blue-600">Download the Excel template to fill marks.</p>
                        </div>
                        <button onClick={handleDownloadTemplate} className="text-xs bg-white border border-blue-200 text-blue-600 px-3 py-1.5 rounded hover:bg-blue-50 flex items-center gap-1">
                            <Download size={14} /> Download Template
                        </button>
                    </div>

                    {/* File Input */}
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:bg-gray-50 transition-colors relative">
                        <input
                            type="file"
                            accept=".xlsx, .xls, .csv"
                            onChange={handleFileChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                        <div className="flex flex-col items-center gap-2">
                            <FileSpreadsheet className="text-green-500" size={40} />
                            {file ? (
                                <div>
                                    <p className="font-medium text-gray-900">{file.name}</p>
                                    <p className="text-sm text-gray-500">{previewData.length} records found</p>
                                </div>
                            ) : (
                                <div>
                                    <p className="font-medium text-gray-700">Click to Upload Excel File</p>
                                    <p className="text-xs text-gray-400">Supports .xlsx, .csv</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Preview (First 3 rows) */}
                    {previewData.length > 0 && (
                        <div>
                            <p className="text-xs font-bold text-gray-500 uppercase mb-2">Preview (First 3 rows)</p>
                            <div className="bg-gray-50 rounded border border-gray-200 overflow-hidden text-sm">
                                <table className="w-full text-left">
                                    <thead className="bg-gray-100 text-gray-600">
                                        <tr>
                                            <th className="p-2">ID</th>
                                            <th className="p-2">Written</th>
                                            <th className="p-2">MCQ</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {previewData.slice(0, 3).map((row, i) => (
                                            <tr key={i} className="border-t border-gray-200">
                                                <td className="p-2">{row.student_id}</td>
                                                <td className="p-2">{row.written_marks}</td>
                                                <td className="p-2">{row.mcq_marks}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-end pt-2">
                        <button onClick={onClose} className="mr-3 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md">
                            Cancel
                        </button>
                        <button
                            onClick={() => uploadMutation.mutate(previewData)}
                            disabled={!file || uploadMutation.isPending || previewData.length === 0}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {uploadMutation.isPending ? <Loader2 className="animate-spin mr-2" size={16} /> : <Upload className="mr-2" size={16} />}
                            Upload & Process
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UploadResultsModal;
