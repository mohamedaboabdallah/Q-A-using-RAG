import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
  const location = useLocation();
  const navigate = useNavigate();

  if (location.pathname === '/login' || location.pathname === '/register') return null;

  const username = localStorage.getItem('username') || 'User';

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <NavLink to="/chatUpload">DocChat</NavLink>
      </div>
      <div className="navbar-links">
        <span className="hello">Hello, {username}</span>
      </div>
      <div className="navbar-actions">
        <button onClick={handleLogout} className="logout-button">Logout</button>
      </div>
    </nav>
  );
};

export default Navbar;
