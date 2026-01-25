import React from 'react';

const Dashboard: React.FC = () => {
    return (
        <div>
            <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-gray-500 text-sm font-medium">Total Students</h3>
                    <p className="text-3xl font-bold text-gray-900 mt-2">--</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-gray-500 text-sm font-medium">Fees Collected (This Month)</h3>
                    <p className="text-3xl font-bold text-green-600 mt-2">৳--</p>
                </div>
                <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                    <h3 className="text-gray-500 text-sm font-medium">Any Active Alerts</h3>
                    <p className="text-lg text-gray-600 mt-2">System Running Normally</p>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
