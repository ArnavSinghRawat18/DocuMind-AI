/**
 * frontend/src/components/ToastContext.jsx
 * Global toast notification context and provider
 * 
 * Usage:
 * 1. Wrap your app with <ToastProvider>
 * 2. Use the useToast hook: const { showToast } = useToast();
 * 3. Call showToast('Message', 'success' | 'error' | 'info')
 */

import { createContext, useContext, useState, useCallback } from 'react';

// Create context
const ToastContext = createContext(null);

// Toast ID counter
let toastIdCounter = 0;

/**
 * Generate unique toast ID
 * @returns {string} Unique ID
 */
function generateToastId() {
  return `toast-${++toastIdCounter}-${Date.now()}`;
}

/**
 * ToastProvider Component
 * Provides toast functionality to the entire app
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - Child components
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  /**
   * Shows a toast notification
   * @param {string} message - Toast message
   * @param {'success' | 'error' | 'info'} [type='info'] - Toast type
   * @param {number} [duration=3000] - Auto-hide duration in ms
   * @returns {string} Toast ID
   */
  const showToast = useCallback((message, type = 'info', duration = 3000) => {
    const id = generateToastId();

    const newToast = {
      id,
      message,
      type,
      duration,
      createdAt: Date.now()
    };

    setToasts(prev => [...prev, newToast]);

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }

    return id;
  }, []);

  /**
   * Removes a toast by ID
   * @param {string} id - Toast ID to remove
   */
  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  /**
   * Clears all toasts
   */
  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const value = {
    toasts,
    showToast,
    removeToast,
    clearAllToasts
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
    </ToastContext.Provider>
  );
}

/**
 * Hook to access toast functionality
 * @returns {{ showToast: Function, removeToast: Function, clearAllToasts: Function, toasts: Array }}
 */
export function useToast() {
  const context = useContext(ToastContext);
  
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  
  return context;
}

export default ToastContext;
