/// <reference types="vite/client" />
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail || error.message;
    console.error('API Error:', detail);
    return Promise.reject(error);
  }
);

export default apiClient;
