import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Authentication API
export const authAPI = {
  register: (username: string, password: string, email: string) => 
    api.post('/auth/register', { username, password, email }),
  
  login: (username: string, password: string) => 
    api.post('/auth/login', { username, password }),
  
  getCurrentUser: () => 
    api.get('/auth/user'),
};

// Graph API
export const graphAPI = {
  getOverview: () => 
    api.get('/graph/overview'),
  
  query: (query: string) => 
    api.post('/graph/query', { query }),
};

// File API
export const fileAPI = {
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  getUserFiles: () => 
    api.get('/files'),
};

// History API
export const historyAPI = {
  getQueryHistory: () => 
    api.get('/history'),
};

// Health check
export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
