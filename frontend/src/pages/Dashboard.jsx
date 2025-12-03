/**
 * frontend/src/pages/Dashboard.jsx
 * Main dashboard page for DocuMind AI
 * 
 * This component orchestrates:
 * - IngestionForm: Submit GitHub repos for documentation generation
 * - StatusTracker: Real-time job progress tracking
 * - DocumentViewer: Display generated documentation
 * 
 * Configuration:
 * - Set VITE_API_URL in .env to configure the backend API URL
 * - Example: VITE_API_URL=http://localhost:3000
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import IngestionForm from '../components/IngestionForm';
import StatusTracker from '../components/StatusTracker';
import DocumentViewer from '../components/DocumentViewer';
import ThemeToggle from '../components/ThemeToggle';
import SkeletonRecentJobs from '../components/SkeletonRecentJobs';
import AIPanel from '../components/AIPanel';
import { useToast } from '../components/ToastContext';

// localStorage key for recent jobs
const RECENT_JOBS_KEY = 'recentJobs';
const MAX_RECENT_JOBS = 5;

/**
 * Loads recent jobs from localStorage
 * @returns {Array} Array of recent job entries
 */
function loadRecentJobs() {
  try {
    const stored = localStorage.getItem(RECENT_JOBS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (err) {
    console.error('[Dashboard] Failed to load recent jobs:', err);
    return [];
  }
}

/**
 * Saves recent jobs to localStorage
 * @param {Array} jobs - Array of recent job entries
 */
function saveRecentJobs(jobs) {
  try {
    localStorage.setItem(RECENT_JOBS_KEY, JSON.stringify(jobs));
  } catch (err) {
    console.error('[Dashboard] Failed to save recent jobs:', err);
  }
}

/**
 * Formats a date as relative time or short date
 * @param {string|Date} date - Date to format
 * @returns {string} Formatted date string
 */
function formatDate(date) {
  if (!date) return '';
  const d = new Date(date);
  const now = new Date();
  const diffMs = now - d;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString();
}

/**
 * Status badge component for recent jobs
 */
function StatusBadge({ status }) {
  const statusStyles = {
    completed: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    running: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
    default: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
  };

  const style = statusStyles[status] || statusStyles.default;

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${style}`}>
      {status || 'pending'}
    </span>
  );
}

/**
 * Welcome placeholder when no job is active
 */
function WelcomePlaceholder() {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
      <div className="text-blue-500 mb-4">
        <svg className="w-20 h-20 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
        Welcome to DocuMind AI
      </h3>
      <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
        Start by submitting a GitHub repository to generate documentation.
        Your code will be analyzed and comprehensive docs will be created automatically.
      </p>
      <div className="mt-6 flex justify-center gap-4 text-sm text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Auto-detect languages
        </div>
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          AI-powered analysis
        </div>
      </div>
    </div>
  );
}

/**
 * Tab bar for switching between multiple documents
 */
function DocumentTabs({ docs, selectedIndex, onSelect }) {
  if (!docs || docs.length <= 1) return null;

  return (
    <div className="flex gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg mb-4 overflow-x-auto">
      {docs.map((doc, index) => (
        <button
          key={index}
          onClick={() => onSelect(index)}
          aria-selected={selectedIndex === index}
          aria-label={`View document: ${doc.title || `Document ${index + 1}`}`}
          className={`
            px-4 py-2 text-sm font-medium rounded-md whitespace-nowrap transition-colors
            ${selectedIndex === index
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }
          `}
        >
          {doc.title || `Document ${index + 1}`}
        </button>
      ))}
    </div>
  );
}

/**
 * Recent jobs sidebar panel
 */
function RecentJobsPanel({ jobs, currentJobId, onSelectJob }) {
  if (!jobs || jobs.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
          Recent Jobs
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
          No recent jobs yet
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
        Recent Jobs
      </h3>
      <div className="space-y-2">
        {jobs.slice(0, MAX_RECENT_JOBS).map((job) => (
          <button
            key={job.jobId}
            onClick={() => onSelectJob(job)}
            aria-label={`Load job for ${job.repoUrl}`}
            className={`
              w-full text-left p-3 rounded-lg transition-colors
              ${currentJobId === job.jobId
                ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
              }
            `}
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate flex-1">
                {extractRepoName(job.repoUrl)}
              </p>
              <StatusBadge status={job.status} />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 truncate">
              {job.repoUrl}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              {formatDate(job.createdAt)}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * Extracts repository name from URL
 * @param {string} url - GitHub repository URL
 * @returns {string} Repository name
 */
function extractRepoName(url) {
  if (!url) return 'Unknown';
  try {
    const match = url.match(/github\.com\/([^/]+\/[^/]+)/);
    return match ? match[1] : url;
  } catch {
    return url;
  }
}

/**
 * Dashboard Component
 * Main orchestrator for the DocuMind AI interface
 */
export default function Dashboard() {
  // Toast hook
  const { showToast } = useToast();

  // Core state
  const [jobId, setJobId] = useState(null);
  const [jobDoc, setJobDoc] = useState(null);
  const [generatedDocs, setGeneratedDocs] = useState(null);
  const [selectedDocIndex, setSelectedDocIndex] = useState(0);
  const [recentJobs, setRecentJobs] = useState([]);
  const [recentJobsLoaded, setRecentJobsLoaded] = useState(false); // Track if jobs have loaded

  // Refs
  const documentViewerRef = useRef(null);

  // Load recent jobs on mount
  useEffect(() => {
    // Simulate brief delay for smooth skeleton transition
    const timer = setTimeout(() => {
      const jobs = loadRecentJobs();
      setRecentJobs(jobs);
      setRecentJobsLoaded(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  /**
   * Handles job start from IngestionForm
   * @param {string} newJobId - The newly created job ID
   * @param {string} repoUrl - The repository URL that was submitted
   */
  const handleJobStarted = useCallback((newJobId, repoUrl) => {
    // Set current job
    setJobId(newJobId);
    setJobDoc(null);
    setGeneratedDocs(null);
    setSelectedDocIndex(0);

    // Add to recent jobs
    const newJob = {
      jobId: newJobId,
      repoUrl: repoUrl || 'Unknown',
      status: 'running',
      createdAt: new Date().toISOString()
    };

    setRecentJobs(prev => {
      const filtered = prev.filter(j => j.jobId !== newJobId);
      const updated = [newJob, ...filtered].slice(0, MAX_RECENT_JOBS);
      saveRecentJobs(updated);
      return updated;
    });
  }, []);

  /**
   * Handles job completion from StatusTracker
   * @param {Object} completedJobDoc - The completed job document
   */
  const handleJobComplete = useCallback((completedJobDoc) => {
    setJobDoc(completedJobDoc);

    // Extract generated docs from various possible fields
    const docs = 
      completedJobDoc.generated_docs ||
      completedJobDoc.outputs ||
      (completedJobDoc.document ? [completedJobDoc.document] : null) ||
      [];

    if (docs.length > 0) {
      setGeneratedDocs(docs);
      setSelectedDocIndex(0);

      // Smooth scroll to document viewer
      setTimeout(() => {
        documentViewerRef.current?.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }, 100);
    }

    // Update recent jobs with completed status
    setRecentJobs(prev => {
      const updated = prev.map(job => 
        job.jobId === completedJobDoc.jobId 
          ? { ...job, status: completedJobDoc.status || 'completed' }
          : job
      );
      saveRecentJobs(updated);
      return updated;
    });
  }, []);

  /**
   * Handles selecting a job from recent jobs list
   * @param {Object} job - The job to load
   */
  const handleSelectRecentJob = useCallback((job) => {
    setJobId(job.jobId);
    setJobDoc(null);
    setGeneratedDocs(null);
    setSelectedDocIndex(0);
    showToast(`Loading job: ${extractRepoName(job.repoUrl)}`, 'info');
  }, [showToast]);

  /**
   * Handles AI-generated documentation
   * Appends to existing docs and selects the new one
   * @param {Object} newDoc - The generated document
   */
  const handleAIDocGenerated = useCallback((newDoc) => {
    setGeneratedDocs(prev => {
      const existingDocs = prev || [];
      const updatedDocs = [...existingDocs, newDoc];
      
      // Select the newly added document
      setSelectedDocIndex(updatedDocs.length - 1);
      
      return updatedDocs;
    });

    // Smooth scroll to document viewer
    setTimeout(() => {
      documentViewerRef.current?.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'start' 
      });
    }, 100);
  }, []);

  // Get current document to display
  const currentDoc = generatedDocs?.[selectedDocIndex] || null;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  DocuMind AI
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  AI-Powered Documentation Generator
                </p>
              </div>
            </div>
            {/* Theme Toggle */}
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Two-column layout on desktop, stacked on mobile */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT COLUMN: Form + Recent Jobs */}
          <div className="lg:col-span-1 space-y-6">
            {/* Ingestion Form */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Submit Repository
              </h2>
              <IngestionForm onStarted={handleJobStarted} />
            </div>

            {/* Recent Jobs - Show skeleton before loaded */}
            {!recentJobsLoaded ? (
              <SkeletonRecentJobs count={3} />
            ) : (
              <RecentJobsPanel 
                jobs={recentJobs}
                currentJobId={jobId}
                onSelectJob={handleSelectRecentJob}
              />
            )}
          </div>

          {/* RIGHT COLUMN: Status Tracker + Documents + AI Panel */}
          <div className="lg:col-span-2 space-y-6">
            {/* Status Tracker or Welcome Placeholder */}
            {jobId ? (
              <StatusTracker 
                jobId={jobId}
                onComplete={handleJobComplete}
                pollInterval={2000}
              />
            ) : (
              <WelcomePlaceholder />
            )}

            {/* Document Viewer Section */}
            {generatedDocs && generatedDocs.length > 0 && (
              <div ref={documentViewerRef}>
                {/* Tabs for multiple documents */}
                <DocumentTabs
                  docs={generatedDocs}
                  selectedIndex={selectedDocIndex}
                  onSelect={setSelectedDocIndex}
                />

                {/* Document Viewer */}
                <DocumentViewer 
                  doc={currentDoc}
                  showMeta={true}
                />
              </div>
            )}

            {/* AI Documentation Generator Panel */}
            <AIPanel 
              jobId={jobId}
              onDocGenerated={handleAIDocGenerated}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            DocuMind AI — Intelligent documentation for your codebase
          </p>
        </div>
      </footer>
    </div>
  );
}
