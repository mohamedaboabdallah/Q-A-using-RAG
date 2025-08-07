import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import './Upload.css';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError('');
    setSuccess(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a file');
      return;
    }
    
    const formData = new FormData();
    formData.append('document', file);
    
    try {
      setIsLoading(true);
      setError('');
      await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setSuccess(true);
      setTimeout(() => navigate('/chatbot'), 1500);
    } catch (err) {
      setError(err.response?.data?.error || 'Upload failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2>Upload Document</h2>
        <p className="instructions">Supported formats: .txt, .pdf, .docx</p>
        
        {error && <div className="error-message">{error}</div>}
        {success && (
          <div className="success-message">
            Document processed successfully! Redirecting to chat...
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="file-upload">
            <label className="file-label">
              <input 
                type="file" 
                onChange={handleFileChange}
                accept=".txt,.pdf,.docx"
              />
              <span className="file-button">Choose File</span>
              <span className="file-name">
                {file ? file.name : 'No file selected'}
              </span>
            </label>
          </div>
          
          <button 
            type="submit" 
            disabled={isLoading || !file}
            className={isLoading ? 'loading' : ''}
          >
            {isLoading ? 'Processing...' : 'Upload Document'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Upload;