import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Upload.css';

const Upload = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  const allowedTypes = [
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  ];

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = [];
    const newErrors = {};

    files.forEach((file, index) => {
      if (!allowedTypes.includes(file.type)) {
        newErrors[`file_${index}`] = `${file.name}: Unsupported file type. Please upload PDF, TXT, DOC, or DOCX files.`;
      } else if (file.size > 10 * 1024 * 1024) { // 10MB limit
        newErrors[`file_${index}`] = `${file.name}: File too large. Maximum size is 10MB.`;
      } else {
        validFiles.push(file);
      }
    });

    setErrors(newErrors);
    setSelectedFiles(validFiles);
    setUploadStatus('');
  };

  const removeFile = (indexToRemove) => {
    setSelectedFiles(files => files.filter((_, index) => index !== indexToRemove));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setErrors({ general: 'Please select at least one file to upload.' });
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);
    setUploadStatus('Preparing upload...');
    setErrors({});

    try {
      const formData = new FormData();
      selectedFiles.forEach((file, index) => {
        formData.append(`file_${index}`, file);
      });

      // Simulate upload progress and API call
      // In a real application, you would call your Flask backend upload endpoint
      const uploadSimulation = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(uploadSimulation);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      setUploadStatus('Uploading files...');
      
      // Simulate API call (replace with actual Flask endpoint)
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      clearInterval(uploadSimulation);
      setUploadProgress(100);
      setUploadStatus('Processing files...');
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setUploadStatus('Upload completed successfully!');
      
      // Store upload success state
      localStorage.setItem('filesUploaded', 'true');
      
      // Navigate to chatbot after successful upload
      setTimeout(() => {
        navigate('/chat');
      }, 1500);

    } catch (error) {
      console.error('Upload error:', error);
      setErrors({ general: 'Upload failed. Please try again.' });
      setUploadStatus('');
    } finally {
      setIsUploading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated');
    localStorage.removeItem('username');
    localStorage.removeItem('filesUploaded');
    navigate('/');
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="upload-container">
      <div className="upload-header">
        <div className="user-info">
          <span>Welcome, {localStorage.getItem('username')}!</span>
          <button onClick={handleLogout} className="btn btn-secondary logout-btn">
            Logout
          </button>
        </div>
      </div>

      <div className="upload-card card">
        <div className="upload-title">
          <h1>Upload Documents</h1>
          <p>Upload your documents to start chatting with your AI assistant</p>
        </div>

        {errors.general && (
          <div className="error-message general-error">
            {errors.general}
          </div>
        )}

        <div className="upload-section">
          <div className="file-input-wrapper">
            <input
              type="file"
              id="file-input"
              multiple
              accept=".pdf,.txt,.doc,.docx"
              onChange={handleFileSelect}
              disabled={isUploading}
              className="file-input"
            />
            <label htmlFor="file-input" className={`file-input-label ${isUploading ? 'disabled' : ''}`}>
              <div className="upload-icon">📁</div>
              <div className="upload-text">
                <strong>Choose files</strong> or drag and drop
                <br />
                <small>PDF, TXT, DOC, DOCX (Max 10MB each)</small>
              </div>
            </label>
          </div>

          {Object.keys(errors).length > 0 && (
            <div className="file-errors">
              {Object.values(errors).map((error, index) => (
                <div key={index} className="error-message">{error}</div>
              ))}
            </div>
          )}

          {selectedFiles.length > 0 && (
            <div className="selected-files">
              <h3>Selected Files ({selectedFiles.length})</h3>
              <div className="file-list">
                {selectedFiles.map((file, index) => (
                  <div key={index} className="file-item">
                    <div className="file-info">
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">{formatFileSize(file.size)}</span>
                    </div>
                    {!isUploading && (
                      <button
                        onClick={() => removeFile(index)}
                        className="remove-file-btn"
                        title="Remove file"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {isUploading && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <div className="progress-text">
                {uploadStatus} ({uploadProgress}%)
              </div>
            </div>
          )}

          <div className="upload-actions">
            <button
              onClick={handleUpload}
              disabled={selectedFiles.length === 0 || isUploading}
              className={`btn btn-primary upload-btn ${isUploading ? 'loading' : ''}`}
            >
              {isUploading ? 'Uploading...' : `Upload ${selectedFiles.length} File${selectedFiles.length !== 1 ? 's' : ''}`}
            </button>
            
            {localStorage.getItem('filesUploaded') && (
              <button
                onClick={() => navigate('/chat')}
                className="btn btn-secondary"
              >
                Skip to Chat
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;