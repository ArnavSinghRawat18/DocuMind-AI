/**
 * frontend/src/components/IngestionForm.jsx
 * Form component for starting repository ingestion
 * Validates URL and communicates with backend API
 */

import { useState } from 'react';
import { startIngest } from '../services/api';
import { useToast } from './ToastContext';

/**
 * Validates a repository URL
 * @param {string} url - URL to validate
 * @returns {{ valid: boolean, message: string }}
 */
function validateRepoUrl(url) {
  if (!url || url.trim() === '') {
    return { valid: false, message: 'Repository URL is required' };
  }

  const trimmedUrl = url.trim();

  if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
    return { valid: false, message: 'URL must start with http:// or https://' };
  }

  return { valid: true, message: '' };
}

/**
 * Inline loading spinner component
 */
function InlineSpinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-white inline-block"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
}

/**
 * IngestionForm Component
 * Allows users to submit a GitHub repository URL for ingestion
 * 
 * @param {Object} props
 * @param {(jobId: string) => void} props.onStarted - Callback when job successfully starts
 */
export default function IngestionForm({ onStarted }) {
  // Toast hook
  const { showToast } = useToast();

  // Local state
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  /**
   * Handles form submission
   * @param {React.FormEvent} e - Form event
   */
  async function handleSubmit(e) {
    e.preventDefault();
    
    console.log('[IngestionForm] handleSubmit triggered');
    console.log('[IngestionForm] repoUrl:', repoUrl);

    // Clear previous error
    setError('');

    // Validate URL
    const validation = validateRepoUrl(repoUrl);
    if (!validation.valid) {
      console.log('[IngestionForm] Validation failed:', validation.message);
      setError(validation.message);
      return;
    }

    setLoading(true);
    console.log('[IngestionForm] Starting API call...');

    try {
      // Call API to start ingestion
      const jobId = await startIngest(repoUrl.trim());
      
      console.log('[IngestionForm] Success! Job ID:', jobId);

      // Show success toast
      showToast(`Ingestion started! Job ID: ${jobId}`, 'success');

      // Clear the input on success
      setRepoUrl('');

      // Notify parent component
      if (onStarted) {
        onStarted(jobId, repoUrl.trim());
      }

    } catch (err) {
      console.error('[IngestionForm] Error:', err);
      // Display user-friendly error
      const errorMsg = err.message || 'Failed to start ingestion. Please try again.';
      setError(errorMsg);
      showToast(errorMsg, 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="space-y-4">
        {/* Input Group */}
        <div>
          <label
            htmlFor="repoUrl"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            GitHub Repository URL
          </label>
          
          <div className="flex gap-3">
            <input
              type="text"
              id="repoUrl"
              name="repoUrl"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              disabled={loading}
              className={`
                flex-1 px-4 py-3 rounded-lg border
                bg-white dark:bg-gray-800
                text-gray-900 dark:text-gray-100
                placeholder-gray-400 dark:placeholder-gray-500
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors duration-200
                ${error ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'}
              `}
              aria-describedby={error ? 'error-message' : undefined}
              aria-invalid={error ? 'true' : 'false'}
            />

            <button
              type="submit"
              disabled={loading}
              aria-busy={loading}
              className={`
                px-6 py-3 rounded-lg font-semibold
                bg-blue-600 hover:bg-blue-700
                text-white
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors duration-200
                flex items-center gap-2
              `}
            >
              {loading ? (
                <>
                  <InlineSpinner />
                  <span>Starting…</span>
                </>
              ) : (
                <span>Start Ingestion</span>
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div
            id="error-message"
            role="alert"
            className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
          >
            <div className="flex items-center gap-2">
              <svg
                className="h-5 w-5 text-red-500"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <span className="text-red-700 dark:text-red-300 text-sm font-medium">
                {error}
              </span>
            </div>
          </div>
        )}

        {/* Helper Text */}
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Enter a public GitHub repository URL. The ingestion process will clone the repo,
          scan files, and create embeddings for AI-powered documentation.
        </p>
      </div>
    </form>
  );
}
