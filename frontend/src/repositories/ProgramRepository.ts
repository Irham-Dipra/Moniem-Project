const API_BASE_URL = "http://127.0.0.1:8000";

export const ProgramRepository = {
    // ==========================
    // BATCHES
    // ==========================
    async getAllBatches() {
        const response = await fetch(`${API_BASE_URL}/batches`);
        if (!response.ok) throw new Error("Failed to fetch batches");
        return await response.json();
    },

    async createBatch(batchData: { batch_name: string }) {
        const response = await fetch(`${API_BASE_URL}/batches`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(batchData),
        });
        if (!response.ok) throw new Error("Failed to create batch");
        return await response.json();
    },

    // ==========================
    // PROGRAMS
    // ==========================
    async getAllPrograms() {
        const response = await fetch(`${API_BASE_URL}/programs`);
        if (!response.ok) throw new Error("Failed to fetch programs");
        return await response.json();
    },

    async createProgram(programData: any) {
        const response = await fetch(`${API_BASE_URL}/programs`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(programData),
        });
        if (!response.ok) throw new Error("Failed to create program");
        return await response.json();
    }
};
