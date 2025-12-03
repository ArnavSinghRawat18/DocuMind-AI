import { useState } from 'react';
import { startIngest } from '../services/api';
import { useToast } from './ToastContext';

/**
 * DemoPanel - Interactive demo section for repository ingestion
 * Uses API client and toast notifications
 */
export default function DemoPanel({ onStarted }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { showToast } = useToast();

  /**
   * Validate repository URL
   */
  const validateUrl = (url) => {
    if (!url.trim()) {
      return 'Please enter a GitHub repository URL';
    }
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return 'URL must start with http:// or https://';
    }
    if (!url.includes('github.com')) {
      return 'Please enter a valid GitHub repository URL';
    }
    return '';
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate
    const validationError = validateUrl(repoUrl);
    if (validationError) {
      setError(validationError);
      showToast(validationError, 'error');
      return;
    }

    setError('');
    setIsLoading(true);

    try {
      const result = await startIngest(repoUrl);
      const jobId = result.jobId || result.job_id;
      
      showToast(`Job started: ${jobId}`, 'success');
      setRepoUrl('');
      
      if (onStarted) {
        onStarted(jobId);
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to start ingestion. Please try again.';
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="py-20 lg:py-28 bg-gradient-to-br from-blue-600 via-purple-600 to-blue-700 dark:from-blue-800 dark:via-purple-800 dark:to-blue-900 transition-colors duration-300">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-bold text-white">
            Try It Now — Free Demo
          </h2>
          <p className="mt-4 text-lg text-blue-100">
            Paste your GitHub repository URL and watch the magic happen.
          </p>
        </div>

        {/* Demo Form */}
        <form 
          onSubmit={handleSubmit}
          className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-6 sm:p-8"
        >
          <div className="space-y-6">
            {/* Input Field */}
            <div>
              <label 
                htmlFor="repo-url"
                className="block text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2"
              >
                GitHub Repository URL
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                </div>
                <input
                  type="url"
                  id="repo-url"
                  value={repoUrl}
                  onChange={(e) => {
                    setRepoUrl(e.target.value);
                    setError('');
                  }}
                  placeholder="https://github.com/username/repository"
                  className={`
                    w-full pl-12 pr-4 py-4 
                    border-2 rounded-xl 
                    text-gray-900 dark:text-white 
                    bg-gray-50 dark:bg-gray-800
                    placeholder-gray-400 dark:placeholder-gray-500
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                    transition-colors duration-200
                    ${error 
                      ? 'border-red-300 dark:border-red-600' 
                      : 'border-gray-200 dark:border-gray-700'
                    }
                  `}
                  disabled={isLoading}
                  aria-describedby={error ? 'url-error' : undefined}
                  aria-invalid={!!error}
                />
              </div>
              
              {/* Error Message */}
              {error && (
                <p 
                  id="url-error"
                  className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-center gap-1"
                  role="alert"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  {error}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`
                w-full py-4 px-6 
                bg-gradient-to-r from-blue-600 to-purple-600 
                hover:from-blue-700 hover:to-purple-700
                text-white font-semibold text-lg
                rounded-xl shadow-lg
                transition-all duration-200
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900
                disabled:opacity-60 disabled:cursor-not-allowed
                ${isLoading ? '' : 'hover:shadow-xl hover:-translate-y-0.5'}
              `}
              aria-busy={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-3">
                  <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Start Free Demo
                </span>
              )}
            </button>

            {/* Helper Text */}
            <p className="text-center text-sm text-gray-500 dark:text-gray-400">
              Public repositories only for free demo. No account required.
            </p>
          </div>
        </form>

        {/* Trust indicators */}
        <div className="mt-8 flex flex-wrap justify-center gap-6 text-blue-100/80">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-sm">Secure & Private</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
            </svg>
            <span className="text-sm">Lightning Fast</span>
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
            </svg>
            <span className="text-sm">AI Powered</span>
          </div>
        </div>
      </div>
    </div>
  );
}
