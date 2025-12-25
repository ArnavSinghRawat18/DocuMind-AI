/**
 * frontend/src/App.jsx
 * Main application entry point
 * Wraps the app with ToastProvider for global toast notifications
 * Initializes theme system for light/dark mode
 */

import { useEffect } from 'react';
import { ToastProvider } from './components/ToastContext';
import ToastContainer from './components/ToastContainer';
import Landing from './pages/Landing';
import { useTheme } from './hooks/useTheme';

/**
 * ThemeInitializer Component
 * Initializes and manages theme state
 */
function ThemeInitializer({ children }) {
  const { theme } = useTheme();

  // Effect to handle theme changes
  useEffect(() => {
    // Theme is already applied by useTheme hook
    // This effect can be used for additional side effects if needed
  }, [theme]);

  return children;
}

/**
 * App Component
 * Root component that sets up providers and renders main content
 */
export default function App() {
  return (
    <ToastProvider>
      <ThemeInitializer>
        <Landing />
        <ToastContainer />
      </ThemeInitializer>
    </ToastProvider>
  );
}
