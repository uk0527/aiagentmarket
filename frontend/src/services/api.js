import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth endpoints
export const auth = {
  signup: (userData) => api.post('/auth/signup', userData),
  login: (credentials) => api.post('/auth/token', credentials),
  getCurrentUser: () => api.get('/auth/me'),
};

// Agent endpoints
export const agents = {
  getAll: () => api.get('/agents'),
  getById: (id) => api.get(`/agents/${id}`),
  create: (agentData) => api.post('/agents', agentData),
  update: (id, agentData) => api.put(`/agents/${id}`, agentData),
  delete: (id) => api.delete(`/agents/${id}`),
};

// Cart endpoints
export const cart = {
  getItems: () => api.get('/cart'),
  addItem: (agentId) => api.post('/cart', { agent_id: agentId }),
  removeItem: (agentId) => api.delete(`/cart/${agentId}`),
  checkout: () => api.post('/cart/checkout'),
};

// Purchase endpoints
export const purchases = {
  getAll: () => api.get('/purchases'),
  getById: (id) => api.get(`/purchases/${id}`),
};

// Review endpoints
export const reviews = {
  create: (agentId, reviewData) => api.post(`/agents/${agentId}/reviews`, reviewData),
  update: (reviewId, reviewData) => api.put(`/reviews/${reviewId}`, reviewData),
  delete: (reviewId) => api.delete(`/reviews/${reviewId}`),
};

export default api; 