import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import './Login.css';

const Login = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      console.log("Attempting login with:", credentials);
      
      const response = await api.post('/login', credentials);
      console.log("Login response:", response);
      
      if (response.data && response.data.token) {
        localStorage.setItem('token', response.data.token);
        navigate('/upload');
      } else {
        throw new Error('No token received in response');
      }
    } catch (err) {
      console.error("Login error:", err);
      
      // Handle Axios errors
      if (err.response) {
        // Server responded with error status (4xx, 5xx)
        setError(err.response.data?.error || `Server error: ${err.response.status}`);
      } else if (err.request) {
        // Request was made but no response received
        setError('Network error: Server did not respond');
      } else {
        // Other errors
        setError(err.message || 'Login failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Document Chat System</h2>
        {error && <div className="error-message">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              value={credentials.username}
              onChange={(e) => setCredentials({...credentials, username: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={credentials.password}
              onChange={(e) => setCredentials({...credentials, password: e.target.value})}
              required
            />
          </div>
          <button 
            type="submit" 
            disabled={isLoading}
            className={isLoading ? 'loading' : ''}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        
        {/* Temporary testing credentials */}
        <div className="test-credentials">
          <p>For testing, use any username and password</p>
          <p>Example: username: <strong>test</strong>, password: <strong>test</strong></p>
        </div>
      </div>
    </div>
  );
};

export default Login;