import React from "react";
import { Routes, Route, Navigate, Link } from "react-router-dom";
import Login from "./components/auth/Login";
import Register from "./components/auth/Register";
import ChatUpload from "./components/chatUpload/chatUpload";

class ErrorBoundary extends React.Component {
  constructor(props){ super(props); this.state = { hasError: false, err: null }; }
  static getDerivedStateFromError(err){ return { hasError: true, err }; }
  componentDidCatch(err, info){ console.error("Render error:", err, info); }
  render(){
    if (this.state.hasError) {
      return (
        <div style={{ padding: 16 }}>
          <h2>Something broke while rendering.</h2>
          <pre>{String(this.state.err)}</pre>
          <p><Link to="/ping">Go to ping page</Link></p>
        </div>
      );
    }
    return this.props.children;
  }
}

function Ping() {
  return (
    <div style={{ padding: 16 }}>
      <h1>Frontend is alive ✅</h1>
      <p><Link to="/login">Go to Login</Link></p>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/chatUpload" element={<ChatUpload />} />
        <Route path="/chat" element={<sendMessage />} />
        <Route path="/ping" element={<Ping />} />
        <Route path="*" element={<div style={{padding:16}}>Not Found</div>} />
      </Routes>
    </ErrorBoundary>
  );
}
