/**
 * frontend/src/main.jsx
 * Application entry point
 * Initializes React and applies theme before mounting to prevent flash
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

// Initialize theme immediately before React mounts to prevent flash
(function initTheme() {
  const THEME_KEY = 'theme';
  let theme;
  
  try {
    theme = localStorage.getItem(THEME_KEY);
  } catch (e) {
    // localStorage not available
  }
  
  // If no saved theme, check system preference
  if (!theme) {
    theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  
  // Apply theme class immediately
  if (theme === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
})();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
