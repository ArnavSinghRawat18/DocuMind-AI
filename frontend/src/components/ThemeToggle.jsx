/**
 * frontend/src/components/ThemeToggle.jsx
 * Theme toggle button component with sun/moon icons
 * Shows sun icon in dark mode, moon icon in light mode
 */

import { useTheme } from '../hooks/useTheme';

/**
 * Sun icon for dark mode (click to switch to light)
 */
function SunIcon() {
  return (
    <svg
      className="w-5 h-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
      />
    </svg>
  );
}

/**
 * Moon icon for light mode (click to switch to dark)
 */
function MoonIcon() {
  return (
    <svg
      className="w-5 h-5"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
      />
    </svg>
  );
}

/**
 * ThemeToggle Component
 * Circular button that toggles between light and dark themes
 * 
 * @param {Object} props
 * @param {string} [props.className] - Additional CSS classes
 */
export default function ThemeToggle({ className = '' }) {
  const { isDarkMode, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      className={`
        rounded-full p-2 
        bg-gray-100 dark:bg-gray-700
        text-gray-600 dark:text-gray-300
        shadow hover:shadow-md
        hover:bg-gray-200 dark:hover:bg-gray-600
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        dark:focus:ring-offset-gray-800
        transition-all duration-200
        ${className}
      `}
    >
      {isDarkMode ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}
