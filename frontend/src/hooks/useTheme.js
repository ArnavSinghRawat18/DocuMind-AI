/**
 * frontend/src/hooks/useTheme.js
 * Theme management hook for light/dark mode
 * 
 * Features:
 * - Detects system theme preference
 * - Persists user choice to localStorage
 * - Updates <html> classList for Tailwind dark mode
 * - Provides smooth transitions
 */

import { useState, useEffect, useCallback } from 'react';

// localStorage key for theme persistence
const THEME_STORAGE_KEY = 'theme';

// Valid theme values
const THEMES = {
  LIGHT: 'light',
  DARK: 'dark'
};

/**
 * Gets the system's preferred color scheme
 * @returns {'light' | 'dark'} System theme preference
 */
function getSystemTheme() {
  if (typeof window === 'undefined') return THEMES.LIGHT;
  return window.matchMedia('(prefers-color-scheme: dark)').matches 
    ? THEMES.DARK 
    : THEMES.LIGHT;
}

/**
 * Gets the initial theme from localStorage or system preference
 * @returns {'light' | 'dark'} Initial theme
 */
function getInitialTheme() {
  if (typeof window === 'undefined') return THEMES.LIGHT;
  
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === THEMES.LIGHT || stored === THEMES.DARK) {
      return stored;
    }
  } catch (err) {
    console.error('[useTheme] Failed to read theme from localStorage:', err);
  }
  
  return getSystemTheme();
}

/**
 * Applies theme class to document
 * @param {'light' | 'dark'} theme - Theme to apply
 */
function applyThemeToDocument(theme) {
  if (typeof document === 'undefined') return;
  
  const html = document.documentElement;
  
  if (theme === THEMES.DARK) {
    html.classList.add('dark');
  } else {
    html.classList.remove('dark');
  }
}

/**
 * Saves theme to localStorage
 * @param {'light' | 'dark'} theme - Theme to save
 */
function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (err) {
    console.error('[useTheme] Failed to save theme to localStorage:', err);
  }
}

/**
 * useTheme Hook
 * Manages theme state and provides toggle functionality
 * 
 * @returns {{
 *   theme: 'light' | 'dark',
 *   isDarkMode: boolean,
 *   toggleTheme: () => void,
 *   setTheme: (theme: 'light' | 'dark') => void
 * }}
 */
export function useTheme() {
  const [theme, setThemeState] = useState(getInitialTheme);

  // Derived state
  const isDarkMode = theme === THEMES.DARK;

  /**
   * Sets theme and persists to localStorage
   * @param {'light' | 'dark'} newTheme - Theme to set
   */
  const setTheme = useCallback((newTheme) => {
    if (newTheme !== THEMES.LIGHT && newTheme !== THEMES.DARK) {
      console.warn('[useTheme] Invalid theme:', newTheme);
      return;
    }
    setThemeState(newTheme);
    saveTheme(newTheme);
    applyThemeToDocument(newTheme);
  }, []);

  /**
   * Toggles between light and dark themes
   */
  const toggleTheme = useCallback(() => {
    const newTheme = theme === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
    setTheme(newTheme);
  }, [theme, setTheme]);

  // Apply theme on mount and listen for system theme changes
  useEffect(() => {
    // Apply initial theme
    applyThemeToDocument(theme);

    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleSystemThemeChange = (e) => {
      // Only update if user hasn't set a preference
      const stored = localStorage.getItem(THEME_STORAGE_KEY);
      if (!stored) {
        const newTheme = e.matches ? THEMES.DARK : THEMES.LIGHT;
        setThemeState(newTheme);
        applyThemeToDocument(newTheme);
      }
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleSystemThemeChange);
    } else {
      // Legacy support
      mediaQuery.addListener(handleSystemThemeChange);
    }

    return () => {
      if (mediaQuery.removeEventListener) {
        mediaQuery.removeEventListener('change', handleSystemThemeChange);
      } else {
        mediaQuery.removeListener(handleSystemThemeChange);
      }
    };
  }, [theme]);

  return {
    theme,
    isDarkMode,
    toggleTheme,
    setTheme
  };
}

export default useTheme;
