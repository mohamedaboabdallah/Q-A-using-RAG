import React, { useState, useRef, useEffect } from 'react';
import api from '../../services/api';
import './Chatbot.css';

const Chatbot = () => {
  const [message, setMessage] = useState('');
  const [conversation, setConversation] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Load previous conversation from localStorage
  useEffect(() => {
    const savedConversation = localStorage.getItem('chatConversation');
    if (savedConversation) {
      setConversation(JSON.parse(savedConversation));
    }
  }, []);

  // Save conversation to localStorage
  useEffect(() => {
    localStorage.setItem('chatConversation', JSON.stringify(conversation));
  }, [conversation]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    // Add user message to chat
    const userMessage = { text: message, sender: 'user' };
    const updatedConversation = [...conversation, userMessage];
    setConversation(updatedConversation);
    setMessage('');
    setIsLoading(true);

    try {
      // Get bot response
      const response = await api.post('/chat', { message });
      
      // Add bot response to chat
      const botMessage = { text: response.data.reply, sender: 'bot' };
      setConversation([...updatedConversation, botMessage]);
    } catch (error) {
      const errorMessage = { 
        text: 'Error: Could not get response from the server', 
        sender: 'bot' 
      };
      setConversation([...updatedConversation, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversation]);

  const clearChat = () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      setConversation([]);
      localStorage.removeItem('chatConversation');
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>Document Chat</h2>
        <button onClick={clearChat} className="clear-button">
          Clear Chat
        </button>
      </div>
      
      <div className="chat-messages">
        {conversation.length === 0 ? (
          <div className="empty-state">
            <p>Ask questions about your uploaded document</p>
            <p>Examples:</p>
            <ul>
              <li>What is the main idea of this document?</li>
              <li>Summarize the key points</li>
              <li>Explain the concept of...</li>
            </ul>
          </div>
        ) : (
          conversation.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <div className="message-content">
                {msg.text}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message bot">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSubmit} className="chat-input">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask about your document..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !message.trim()}>
          <i className="send-icon">➤</i>
        </button>
      </form>
    </div>
  );
};

export default Chatbot;