import axios from 'axios';
import { GraphData, GraphOverview } from '../types/graph';

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Allow cookies for session-based auth
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

// API response types
export interface User {
  id: number;
  username: string;
  email: string;
}

export interface LoginResponse {
  user: User;
  token: string;
  message: string;
}

export interface FileUploadResponse {
  message: string;
  file: {
    id: number;
    name: string;
    size: number;
  };
  graph: {
    nodesCreated: number;
    relationshipsCreated: number;
    graphData: GraphData;
  };
}

export interface QueryResponse {
  id: string;
  query: string;
  response: string;
  graphData: GraphData;
  timestamp: string;
}

export interface HealthCheckResponse {
  status: string;
  neo4j: string;
  llm: string;
}

export interface DbConfigResponse {
  message: string;
  config: {
    useInMemory: boolean;
    connected: boolean;
  };
}

// Authentication API
export const authAPI = {
  register: (username: string, password: string, email: string) => 
    api.post<LoginResponse>('/register', { username, password, email }),
  
  login: (username: string, password: string) => 
    api.post<LoginResponse>('/login', { username, password }),
  
  getCurrentUser: () => 
    api.get<User>('/user'),
    
  logout: () => 
    api.post('/logout'),
};

// Graph API
export const graphAPI = {
  getOverview: () => 
    api.get<GraphOverview>('/graph/overview'),
  
  query: (query: string) => 
    api.post<QueryResponse>('/graph/query', { query }),
};

// File API
export const fileAPI = {
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<FileUploadResponse>('/upload', formData, {
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
    api.get<QueryResponse[]>('/history'),
};

// System API
export const systemAPI = {
  health: () => 
    api.get<HealthCheckResponse>('/health'),
    
  setDbConfig: (useInMemory: boolean) => 
    api.post<DbConfigResponse>('/db-config', { useInMemory }),
};

export default api;
