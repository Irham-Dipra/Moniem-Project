import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom'; // Import useNavigate
import { User, Mail, Shield, BadgeCheck, LogOut } from 'lucide-react'; // Import LogOut

const UserProfile: React.FC = () => {
    const { user, userName, dbUserId, userRole, signOut } = useAuth(); // Destructure signOut
    const navigate = useNavigate();

    const handleLogout = async () => {
        await signOut();
        navigate('/login');
    };

    // Fallback display name logic
    const displayName = userName || user?.user_metadata?.full_name || 'User';

    return (
        <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold text-gray-800">My Profile</h1>
                <button
                    onClick={handleLogout}
                    className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition font-medium"
                >
                    <LogOut size={18} />
                    Sign Out
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="h-32 bg-gradient-to-r from-blue-500 to-indigo-600"></div>

                <div className="px-8 pb-8">
                    <div className="relative flex justify-between items-end -mt-12 mb-6">
                        <div className="flex items-end gap-6">
                            <div className="w-24 h-24 rounded-full bg-white p-1 shadow-lg">
                                <div className="w-full h-full rounded-full bg-gray-100 flex items-center justify-center text-gray-400">
                                    <User size={40} />
                                </div>
                            </div>
                            <div className="mb-1">
                                <h2 className="text-2xl font-bold text-gray-900">{displayName}</h2>
                                <p className="text-gray-500">{user?.email}</p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Account Details</h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 uppercase">Role</label>
                                    <div className="flex items-center gap-2 mt-1 text-gray-800">
                                        <Shield size={18} className="text-blue-600" />
                                        <span className="capitalize font-medium">{userRole}</span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 uppercase">Email</label>
                                    <div className="flex items-center gap-2 mt-1 text-gray-800">
                                        <Mail size={18} className="text-blue-600" />
                                        <span>{user?.email}</span>
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-gray-500 uppercase">User ID</label>
                                    <div className="flex items-center gap-2 mt-1 text-gray-800">
                                        <BadgeCheck size={18} className="text-blue-600" />
                                        <span className="font-mono text-sm">#{dbUserId || 'N/A'}</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div>
                            <h3 className="text-lg font-semibold text-gray-800 mb-4 border-b pb-2">Academic Info</h3>
                            <p className="text-gray-500 text-sm">
                                {userRole === 'student'
                                    ? "Student academic details will appear here once linked."
                                    : "Administrative profile settings."}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default UserProfile;
