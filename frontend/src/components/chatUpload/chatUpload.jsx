import React, { useRef, useState, useEffect } from "react";
import api from "../../services/api";
import "./chatUpload.css";
import { useNavigate } from "react-router-dom";

const ChatUpload = () => {
  const fileInputRef = useRef(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const navigate = useNavigate();
  const username = localStorage.getItem("username") || "";

  // Redirect to login if no token
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/Login");
      return;
    }
    fetchFiles();
  }, [navigate]);

  // Fetch uploaded files from backend, with simple retry
  const fetchFiles = async (retryCount = 1) => {
    try {
      const res = await api.get("/files");
      setUploadedFiles(res.data.files || []);
    } catch (err) {
      console.error("Error fetching files:", err);
      if (retryCount > 0) {
        console.log("Retrying fetchFiles...");
        setTimeout(() => fetchFiles(retryCount - 1), 500);
      }
    }
  };

  // Trigger file picker
  const handleUploadClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
      fileInputRef.current.click();
    }
  };

  // Handle file selection & upload
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
      alert("File size exceeds 5MB. Please choose a smaller file.");
      return;
    }

    const formData = new FormData();
    formData.append("document", file);

    try {
      setIsUploading(true);
      // No manual Content-Type header, let Axios handle it
      const res = await api.post("/upload", formData);

      await new Promise(resolve => setTimeout(resolve, 1000)); // increase delay a bit
      await fetchFiles();

      alert(res.data?.message || "File uploaded successfully");
    } catch (err) {
      console.error("Upload error:", err);
      alert(err.response?.data?.error || "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  // Send a chat message
  const sendMessage = async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    setMessages((prev) => [...prev, { sender: "user", text: trimmed }]);
    setInput("");

    try {
      const res = await api.post("/chat", { query: trimmed });
      const botReply = res.data?.reply || "No response available.";

      setMessages((prev) => [...prev, { sender: "bot", text: botReply }]);
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "Error: " + (err.response?.data?.error || "Chat failed") },
      ]);
    }
  };

  // Navigate to login without clearing storage
  const handleLogout = () => {
    navigate("/login");
  };

  return (
    <div className="chat-page">
      <div className="navbar">
        <span>Hello, {username}</span>
        <button className="logout-btn" onClick={handleLogout}>
          Logout
        </button>
      </div>

      <div className="chatupload-container">
        <div className="sidebar">
          <h2>Uploaded Files</h2>
          <div className="uploaded-files">
            {uploadedFiles.length === 0 ? (
              <div>No documents yet</div>
            ) : (
              uploadedFiles.map((f) => (
                <div key={f.id || f.filename} className="file-item">
                  {f.filename}
                </div>
              ))
            )}
          </div>

          <input
            type="file"
            ref={fileInputRef}
            style={{ display: "none" }}
            onChange={handleFileChange}
            accept=".txt,.pdf,.docx"
          />

          <button onClick={handleUploadClick} className="upload-btn" disabled={isUploading}>
            {isUploading ? "Uploading..." : "Upload File"}
          </button>
        </div>

        <div className="chat-section">
          <div className="messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.sender === "user" ? "user" : "bot"}`}>
                {m.text}
              </div>
            ))}
          </div>

          <div className="input-area">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            />
            <button onClick={sendMessage}>➤</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatUpload;
