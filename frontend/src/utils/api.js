// frontend/src/utils/api.js
import axios from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5232';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    }
    return Promise.reject(error);
  }
);

// API methods
export const authAPI = {
  login: (credentials) => api.post('/api/auth/login', credentials),
  register: (userData) => api.post('/api/auth/register', userData),
  profile: () => api.get('/api/auth/profile'),
  logout: () => api.post('/api/auth/logout'),
};

// UPDATE projectsAPI to include getProjectWebsites
export const projectsAPI = {
  getAll: (params) => api.get('/api/projects', { params }),
  getById: (id) => api.get(`/api/projects/${id}`),
  create: (data) => api.post('/api/projects', data),
  update: (id, data) => api.put(`/api/projects/${id}`, data),
  delete: (id) => api.delete(`/api/projects/${id}`),
  getCollaborators: (id) => api.get(`/api/projects/${id}/collaborators`),
  addCollaborator: (id, data) => api.post(`/api/projects/${id}/collaborators`, data),
  getStatistics: (id) => api.get(`/api/projects/${id}/statistics`),
  // **FIX: Add missing method for getting project websites**
  getProjectWebsites: (id, params) => api.get(`/api/projects/${id}/websites`, { params }),
};

// For websitesAPI - add these methods if not present
export const websitesAPI = {
  // Existing methods...
  create: (data) => api.post('/api/websites', data),
  getById: (id) => api.get(`/api/websites/${id}`),
  update: (id, data) => api.put(`/api/websites/${id}`, data),
  delete: (id) => api.delete(`/api/websites/${id}`),
  
  // **FIX: Add missing methods for website management**
  getByProject: (projectId, params) => api.get(`/api/projects/${projectId}/websites`, { params }),
  updateStatus: (id, status) => api.put(`/api/websites/${id}`, { status }),
};


// UPDATE scrapingAPI to include missing methods
export const scrapingAPI = {
  run: (data) => api.post('/api/scraping/run', data),
  getStatus: (websiteId) => api.get(`/api/scraping/status/${websiteId}`),
  schedule: (data) => api.post('/api/scraping/schedule', data),
  // **FIX: Add missing stop method**
  stop: (websiteId) => api.post(`/api/scraping/stop/${websiteId}`),
  // **FIX: Add missing jobs methods**
  getJobs: (params) => api.get('/api/scraping/jobs', { params }),
  getAllStatus: () => api.get('/api/scraping/status'),
};

export const contentAPI = {
  getSnippets: (params) => api.get('/api/content/snippets', { params }),
  approveSnippet: (id, data) => api.put(`/api/content/snippets/${id}/approve`, data),
  extractContent: (data) => api.post('/api/content/extract', data),
  getRules: (params) => api.get('/api/content/rules', { params }),
  createRule: (data) => api.post('/api/content/rules', data),
  search: (params) => api.get('/api/content/search', { params }),
  suggestRules: (data) => api.post('/api/content/suggest-rules', data),
};

export const reportsAPI = {
  createExport: (data) => api.post('/api/reports/export', data),
  getExports: (params) => api.get('/api/reports/exports', { params }),
  getExportStatus: (id) => api.get(`/api/reports/exports/${id}`),
  downloadExport: (id) => api.get(`/api/reports/downloads/${id}`, { responseType: 'blob' }),
};

export const adminAPI = {
  executeSQL: (data) => api.post('/api/admin/sql/execute', data),
  getUsers: (params) => api.get('/api/admin/users', { params }),
  getAuditLogs: (params) => api.get('/api/admin/audit-logs', { params }),
  getSystemStatus: () => api.get('/api/admin/system/status'),
  getSettings: () => api.get('/api/admin/settings'),
};

export default api;