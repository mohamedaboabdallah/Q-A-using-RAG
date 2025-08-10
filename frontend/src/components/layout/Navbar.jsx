import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useNavigate } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();
  
  const isActive = (path) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  // Don't show navbar on login page
  if (location.pathname === '/login') return null;

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <NavLink to="/upload">DocChat</NavLink>
      </div>
      
      <div className="navbar-links">
        <NavLink 
          to="/upload" 
          className={isActive('/upload') ? 'active' : ''}
        >
          Upload
        </NavLink>
        <NavLink 
          to="/chatbot" 
          className={isActive('/chatbot') ? 'active' : ''}
        >
          Chat
        </NavLink>
      </div>
      
      <div className="navbar-actions">
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;