import axios, { AxiosInstance } from 'axios';
import { LoginCredentials, SignupData, User, CartItem } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api: AxiosInstance = axios.create({
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

interface ApiResponse<T> {
  data: T;
}

// Auth endpoints
export const auth = {
  signup: (userData: SignupData): Promise<ApiResponse<void>> => 
    api.post('/auth/signup', userData),
  
  login: (credentials: LoginCredentials): Promise<ApiResponse<{ access_token: string }>> => 
    api.post('/auth/token', credentials),
  
  getCurrentUser: (): Promise<ApiResponse<User>> => 
    api.get('/auth/me'),
};

// Agent endpoints
export const agents = {
  getAll: (): Promise<ApiResponse<any[]>> => 
    api.get('/agents'),
  
  getById: (id: number): Promise<ApiResponse<any>> => 
    api.get(`/agents/${id}`),
  
  create: (agentData: any): Promise<ApiResponse<any>> => 
    api.post('/agents', agentData),
  
  update: (id: number, agentData: any): Promise<ApiResponse<any>> => 
    api.put(`/agents/${id}`, agentData),
  
  delete: (id: number): Promise<ApiResponse<void>> => 
    api.delete(`/agents/${id}`),
};

// Cart endpoints
export const cart = {
  getItems: (): Promise<ApiResponse<CartItem[]>> => 
    api.get('/cart'),
  
  addItem: (agentId: number): Promise<ApiResponse<void>> => 
    api.post('/cart', { agent_id: agentId }),
  
  removeItem: (agentId: number): Promise<ApiResponse<void>> => 
    api.delete(`/cart/${agentId}`),
  
  checkout: (): Promise<ApiResponse<void>> => 
    api.post('/cart/checkout'),
};

// Purchase endpoints
export const purchases = {
  getAll: (): Promise<ApiResponse<any[]>> => 
    api.get('/purchases'),
  
  getById: (id: number): Promise<ApiResponse<any>> => 
    api.get(`/purchases/${id}`),
};

// Review endpoints
export const reviews = {
  create: (agentId: number, reviewData: any): Promise<ApiResponse<any>> => 
    api.post(`/agents/${agentId}/reviews`, reviewData),
  
  update: (reviewId: number, reviewData: any): Promise<ApiResponse<any>> => 
    api.put(`/reviews/${reviewId}`, reviewData),
  
  delete: (reviewId: number): Promise<ApiResponse<void>> => 
    api.delete(`/reviews/${reviewId}`),
};

export default api; 