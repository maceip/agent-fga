import { create } from 'zustand';

const useLogStore = create((set) => ({
    logs: [],
    isAuthenticated: false,
    addLog: (message) => set((state) => ({
        logs: [...state.logs, `[${new Date().toLocaleTimeString()}] ${message}`]
    })),
    setAuthenticated: (status) => set({ isAuthenticated: status }),
}));

export default useLogStore;