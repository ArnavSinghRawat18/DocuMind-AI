/**
 * frontend/src/components/StatusTracker.jsx
 * Real-time job status tracker with polling, progress bar, and timeline
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { getJobStatus } from '../services/api';
import { useToast } from './ToastContext';
import SkeletonStatusTracker from './SkeletonStatusTracker';

// Status configuration with labels and colors
const STATUS_CONFIG = {
  started: { label: 'Started', color: 'bg-gray-400', step: 0 },
  cloning: { label: 'Cloning Repository', color: 'bg-blue-400', step: 1 },
  cloned: { label: 'Repository Cloned', color: 'bg-blue-500', step: 1 },
  scanning: { label: 'Scanning Files', color: 'bg-indigo-400', step: 2 },
  scanned: { label: 'Files Scanned', color: 'bg-indigo-500', step: 2 },
  chunking: { label: 'Chunking Code', color: 'bg-purple-400', step: 3 },
  chunked: { label: 'Code Chunked', color: 'bg-purple-500', step: 3 },
  storing: { label: 'Storing in Database', color: 'bg-pink-400', step: 4 },
  stored: { label: 'Stored in Database', color: 'bg-pink-500', step: 4 },
  uploading: { label: 'Uploading to AI', color: 'bg-orange-400', step: 5 },
  processing: { label: 'Processing', color: 'bg-yellow-400', step: 5 },
  completed: { label: 'Completed', color: 'bg-green-500', step: 6 },
  failed: { label: 'Failed', color: 'bg-red-500', step: -1 }
};

// Timeline steps for visual representation
const TIMELINE_STEPS = [
  { key: 'cloning', label: 'Clone' },
  { key: 'scanning', label: 'Scan' },
  { key: 'chunking', label: 'Chunk' },
  { key: 'storing', label: 'Store' },
  { key: 'uploading', label: 'Upload' },
  { key: 'completed', label: 'Done' }
];

/**
 * Formats time difference as human-readable string
 * @param {Date} date - The date to format
 * @returns {string} Human-readable time difference
 */
function formatTimeAgo(date) {
  if (!date) return '';
  
  const seconds = Math.floor((new Date() - new Date(date)) / 1000);
  
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  return `${Math.floor(seconds / 3600)}h ago`;
}

/**
 * Animated checkmark component for completion
 */
function AnimatedCheckmark() {
  return (
    <svg
      className="w-16 h-16 text-green-500 mx-auto animate-bounce"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

/**
 * StatusTracker Component
 * Polls job status and displays real-time progress
 * 
 * @param {Object} props
 * @param {string} props.jobId - Job ID to track
 * @param {(jobDoc: Object) => void} [props.onComplete] - Callback when job completes
 * @param {number} [props.pollInterval=2000] - Polling interval in milliseconds
 */
export default function StatusTracker({ jobId, onComplete, pollInterval = 2000 }) {
  // Toast hook
  const { showToast } = useToast();

  // State
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [timeAgo, setTimeAgo] = useState('');

  // Refs
  const intervalRef = useRef(null);
  const completedRef = useRef(false);

  /**
   * Fetches job status from API
   */
  const fetchStatus = useCallback(async () => {
    if (!jobId) return;

    try {
      const jobDoc = await getJobStatus(jobId);
      
      setJob(jobDoc);
      setError(null);
      setLastUpdated(new Date());
      setLoading(false);

      // Check if job is finished
      if (jobDoc.status === 'completed' || jobDoc.status === 'failed') {
        // Stop polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }

        // Call onComplete callback for completed jobs (only once)
        if (jobDoc.status === 'completed' && onComplete && !completedRef.current) {
          completedRef.current = true;
          showToast('Documentation generated successfully!', 'success');
          onComplete(jobDoc);
        }

        // Show error toast for failed jobs
        if (jobDoc.status === 'failed' && !completedRef.current) {
          completedRef.current = true;
          showToast(jobDoc.error || 'Job failed', 'error');
        }
      }

    } catch (err) {
      setError(err.message || 'Failed to fetch job status');
      setLoading(false);
    }
  }, [jobId, onComplete]);

  /**
   * Starts polling for job status
   */
  const startPolling = useCallback(() => {
    // Clear existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    // Initial fetch
    fetchStatus();

    // Set up polling
    intervalRef.current = setInterval(fetchStatus, pollInterval);
  }, [fetchStatus, pollInterval]);

  /**
   * Handles manual refresh
   */
  const handleRefresh = () => {
    setLoading(true);
    fetchStatus();
  };

  /**
   * Handles retry after error
   */
  const handleRetry = () => {
    setError(null);
    setLoading(true);
    completedRef.current = false;
    startPolling();
  };

  // Start polling on mount and clean up on unmount
  useEffect(() => {
    startPolling();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [startPolling]);

  // Update "time ago" display every second
  useEffect(() => {
    const updateTimeAgo = () => {
      if (lastUpdated) {
        setTimeAgo(formatTimeAgo(lastUpdated));
      }
    };

    updateTimeAgo();
    const timer = setInterval(updateTimeAgo, 1000);

    return () => clearInterval(timer);
  }, [lastUpdated]);

  // Get current status configuration
  const currentStatus = job?.status ? STATUS_CONFIG[job.status] || STATUS_CONFIG.started : STATUS_CONFIG.started;
  const progress = job?.progress ?? 0;
  const currentStep = currentStatus.step;

  // ====== Loading State: Show skeleton when loading AND no job data yet ======
  if (loading && !job) {
    return <SkeletonStatusTracker />;
  }

  // Error state (with no job data)
  if (error && !job) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6">
      {/* Header with Job ID and Last Updated */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Job Status
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 font-mono">
            {jobId}
          </p>
        </div>
        <div className="text-right">
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="text-blue-600 hover:text-blue-700 dark:text-blue-400 text-sm flex items-center gap-1"
          >
            <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
          {timeAgo && (
            <p className="text-xs text-gray-400 mt-1">Updated {timeAgo}</p>
          )}
        </div>
      </div>

      {/* Inline error with retry */}
      {error && job && (
        <div className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <span className="text-yellow-700 dark:text-yellow-300 text-sm">{error}</span>
          <button
            onClick={handleRetry}
            className="text-yellow-700 dark:text-yellow-300 text-sm font-medium hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {/* Current Status Badge */}
      <div className="flex items-center gap-3">
        <span
          className={`px-3 py-1 rounded-full text-white text-sm font-medium ${currentStatus.color}`}
          role="status"
          aria-live="polite"
        >
          {currentStatus.label}
        </span>
        {job?.status !== 'completed' && job?.status !== 'failed' && (
          <span className="animate-pulse text-gray-400">●</span>
        )}
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-300">Progress</span>
          <span className="text-gray-900 dark:text-white font-medium">{Math.max(0, progress)}%</span>
        </div>
        <div
          className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
          role="progressbar"
          aria-valuenow={Math.max(0, progress)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`Job progress: ${Math.max(0, progress)}%`}
        >
          <div
            className={`h-full rounded-full transition-all duration-500 ease-out ${currentStatus.color}`}
            style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
          />
        </div>
      </div>

      {/* Timeline Steps */}
      <div className="pt-4">
        <div className="flex items-center justify-between">
          {TIMELINE_STEPS.map((step, index) => {
            const stepStatus = STATUS_CONFIG[step.key];
            const isActive = currentStep >= stepStatus?.step;
            const isCurrent = currentStep === stepStatus?.step;
            const isFailed = job?.status === 'failed';

            return (
              <div key={step.key} className="flex flex-col items-center flex-1">
                {/* Step Circle */}
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold
                    transition-all duration-300
                    ${isFailed && isCurrent ? 'bg-red-500 text-white' : ''}
                    ${isActive && !isFailed ? 'bg-green-500 text-white' : ''}
                    ${!isActive && !isFailed ? 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400' : ''}
                    ${isCurrent && !isFailed ? 'ring-2 ring-green-300 ring-offset-2' : ''}
                  `}
                >
                  {isActive && !isFailed ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : isFailed && isCurrent ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  ) : (
                    index + 1
                  )}
                </div>
                {/* Step Label */}
                <span className={`
                  text-xs mt-2 text-center
                  ${isActive ? 'text-gray-900 dark:text-white font-medium' : 'text-gray-400'}
                `}>
                  {step.label}
                </span>
                {/* Connector Line (except last) */}
                {index < TIMELINE_STEPS.length - 1 && (
                  <div
                    className={`
                      absolute h-0.5 w-full -z-10
                      ${isActive ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}
                    `}
                    style={{ top: '50%', left: '50%' }}
                  />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Completed State */}
      {job?.status === 'completed' && (
        <div className="text-center py-4 space-y-4">
          <AnimatedCheckmark />
          <h4 className="text-xl font-semibold text-green-600 dark:text-green-400">
            Ingestion Complete!
          </h4>
          {(job.totalFiles || job.totalChunks) && (
            <div className="flex justify-center gap-6 text-sm">
              {job.totalFiles && (
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{job.totalFiles}</p>
                  <p className="text-gray-500">Files Processed</p>
                </div>
              )}
              {job.totalChunks && (
                <div className="text-center">
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">{job.totalChunks}</p>
                  <p className="text-gray-500">Chunks Created</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Failed State */}
      {job?.status === 'failed' && (
        <div className="text-center py-4 space-y-4">
          <div className="text-red-500">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h4 className="text-xl font-semibold text-red-600 dark:text-red-400">
            Ingestion Failed
          </h4>
          {job.error && (
            <p className="text-sm text-gray-600 dark:text-gray-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
              {job.error}
            </p>
          )}
          <button
            onClick={handleRetry}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
