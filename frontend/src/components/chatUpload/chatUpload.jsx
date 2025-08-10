import React, { useRef, useState, useEffect } from 'react';
import api from '../../services/api';
import './chatUpload.css';
import { useNavigate } from 'react-router-dom';

const ChatUpload = () => {
  const fileInputRef = useRef(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || '';

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchFiles();
  }, [navigate]);

  const fetchFiles = async () => {
    try {
      const res = await api.get('/files');
      setUploadedFiles(res.data.files || []);
    } catch (err) {
      console.error('Error fetching files', err);
    }
  };

  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      alert('File > 5MB. Choose a smaller file.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setIsUploading(true);
      const res = await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      await fetchFiles();
      alert(res.data?.message || 'Uploaded successfully');
    } catch (err) {
      console.error('Upload error', err);
      alert(err.response?.data?.error || 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { sender: 'user', text: input }]);
    const text = input;
    setInput('');
    try {
      const res = await api.post('/query', { query: text });
      const botReply = res.data?.matches?.length
        ? res.data.matches.map(m => m.text || '').join('\n')
        : 'No relevant results found.';
      setMessages(prev => [...prev, { sender: 'bot', text: botReply }]);
    } catch (err) {
      console.error('Chat error', err);
      setMessages(prev => [...prev, { sender: 'bot', text: 'Error: ' + (err.response?.data?.error || 'Chat failed') }]);
    }
  };

  const handleLogout = () => {
    // Keep localStorage values, just navigate away
    navigate('/login');
  };

  return (
    <div className="chat-page">
      <div className="navbar">
        <span>Hello, {username}</span>
        <button className="logout-btn" onClick={handleLogout}>Logout</button>
      </div>

      <div className="chatupload-container">
        <div className="sidebar">
          <h2>Uploaded Files</h2>
          <div className="uploaded-files">
            {uploadedFiles.length === 0 ? (
              <div>No documents yet</div>
            ) : (
              uploadedFiles.map((f) => (
                <div key={f.id || f.filename} className="file-item">{f.filename}</div>
              ))
            )}
          </div>

          <input
            type="file"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileChange}
            accept=".txt,.pdf,.docx"
          />

          <button onClick={handleUploadClick} className="upload-btn" disabled={isUploading}>
            {isUploading ? 'Uploading...' : 'Upload File'}
          </button>
        </div>

        <div className="chat-section">
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.sender === 'user' ? 'user' : 'bot'}`}>
                {m.text}
              </div>
            ))}
          </div>

          <div className="input-area">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            />
            <button onClick={sendMessage}>➤</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatUpload;
