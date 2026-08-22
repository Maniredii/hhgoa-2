import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://hhgoa-2-fx6c.onrender.com/api';

export const transcribeAudio = async (audioBlob: Blob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'audio.webm'); // Using webm for browser recording
    
    const response = await axios.post(`${API_BASE}/voice/transcribe`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return response.data;
};

export const sendTextQuery = async (query: string) => {
    const response = await axios.post(`${API_BASE}/query`, { query, language: 'en' });
    return response.data;
};

export const runBenchmark = async () => {
    const response = await axios.post(`${API_BASE}/benchmark?iterations=5`);
    return response.data;
};
