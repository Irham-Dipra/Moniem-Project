const API_BASE_URL = "http://127.0.0.1:8000";

export const PaymentRepository = {
    // Get recent payments (Ledger)
    async getRecentPayments() {
        const response = await fetch(`${API_BASE_URL}/payments/recent`);
        if (!response.ok) throw new Error("Failed to fetch payments");
        return await response.json();
    },

    // Record new payment
    async createPayment(payment: any) {
        const response = await fetch(`${API_BASE_URL}/payments`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payment)
        });
        if (!response.ok) throw new Error("Failed to record payment");
        return await response.json();
    },

    // Get student history
    async getStudentPayments(studentId: number) {
        const response = await fetch(`${API_BASE_URL}/students/${studentId}/payments`);
        if (!response.ok) throw new Error("Failed to fetch student payments");
        return await response.json();
    },

    // Get Overall Stats
    async getFinanceStats() {
        const response = await fetch(`${API_BASE_URL}/finance/stats`);
        if (!response.ok) throw new Error("Failed to fetch finance stats");
        return await response.json();
    },

    // Get Program Breakdown
    async getProgramStats() {
        const response = await fetch(`${API_BASE_URL}/finance/programs`);
        if (!response.ok) throw new Error("Failed to fetch program stats");
        return await response.json();
    }
};
