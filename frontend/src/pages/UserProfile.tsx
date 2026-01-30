import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { User, Mail, Shield, BadgeCheck } from 'lucide-react';

const UserProfile: React.FC = () => {
    const { user, userName, userRole, userStatus } = useAuth();

    return (
        <div className="max-w-4xl mx-auto">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">My Profile</h1>

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
                                <h2 className="text-2xl font-bold text-gray-900">{userName || 'User'}</h2>
                                <p className="text-gray-500">{user?.email}</p>
                            </div>
                        </div>
                        <div className={`px-4 py-1 rounded-full text-sm font-semibold capitalize border ${userStatus === 'approved'
                                ? 'bg-green-50 text-green-700 border-green-200'
                                : 'bg-yellow-50 text-yellow-700 border-yellow-200'
                            }`}>
                            {userStatus}
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
                                        <span className="font-mono text-sm">{user?.id}</span>
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
