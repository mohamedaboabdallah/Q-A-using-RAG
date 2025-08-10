// src/services/api.js   (you already have this — good)
import axios from 'axios';
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'development' ? 'http://localhost:5000/api' : '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
});
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
api.interceptors.response.use(response => response, error => {
  if (error.response?.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    window.location.href = '/login';
  }
  return Promise.reject(error);
});
export default api;
