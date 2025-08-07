import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import './Upload.css';

const Upload = () => {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [progress, setProgress] = useState(0); // NEW: Progress state
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    
    // File size validation (5MB max)
    if (selectedFile && selectedFile.size > 5 * 1024 * 1024) {
      setError('File size exceeds 5MB limit');
      return;
    }
    
    setFile(selectedFile);
    setError('');
    setSuccess(false);
    setProgress(0); // Reset progress when file changes
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
      setProgress(0); // Reset progress on new upload
      
      // UPDATED: Added progress tracking
      await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        }
      });
      
      setSuccess(true);
      setTimeout(() => navigate('/chatbot'), 1500);
    } catch (err) {
      if (err.code === 'ECONNABORTED') {
        setError('Processing took too long. Try a smaller file.');
      } else {
        setError(err.response?.data?.error || 
                err.message || 
                'Upload failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2>Upload Document</h2>
        <p className="instructions">Supported formats: .txt, .pdf, .docx</p>
        
        <div className="message-container" style={{ minHeight: '3rem' }}>
          {error && <div className="error-message">{error}</div>}
          {success && (
            <div className="success-message">
              ✓ Document processed successfully! Redirecting to chat...
            </div>
          )}
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="file-upload">
            <label className="file-label">
              <input 
                type="file" 
                onChange={handleFileChange}
                accept=".txt,.pdf,.docx"
                className="file-input"
              />
              <span className="file-button">Choose File</span>
              <span className="file-name">
                {file ? file.name : 'No file selected'}
              </span>
            </label>
          </div>
          
          {/* NEW: Progress bar added here */}
          {isLoading && (
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${progress}%` }}
              >
                {progress}%
              </div>
            </div>
          )}
          
          <button 
            type="submit" 
            disabled={isLoading || !file}
            className={`upload-button ${isLoading ? 'loading' : ''}`}
          >
            {isLoading ? (
              <>
                <span className="spinner"></span> Processing...
              </>
            ) : 'Upload Document'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Upload;