/**
 * frontend/src/components/AIPanel.jsx
 * AI-powered documentation generation panel
 * 
 * Features:
 * - Multi-line prompt textarea with auto-resize
 * - Generate documentation with AI
 * - Follow-up question suggestions
 * - Model selector (optional)
 * - Loading skeleton while generating
 * - Error handling with toasts
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { generateDoc } from '../services/api';
import { useToast } from './ToastContext';
import Skeleton from './Skeleton';

// Available AI models
const AI_MODELS = [
  { id: 'llama3-70b', name: 'Llama 3 70B', description: 'Most capable' },
  { id: 'llama3-8b', name: 'Llama 3 8B', description: 'Faster' }
];

// Suggested follow-up prompts
const FOLLOW_UP_SUGGESTIONS = [
  { label: 'Explain deeper', prompt: 'Explain this in more detail with examples' },
  { label: 'Summarize', prompt: 'Provide a concise summary of the key points' },
  { label: 'Show related code', prompt: 'Show the related code snippets and explain them' },
  { label: 'Add examples', prompt: 'Add practical usage examples' },
  { label: 'List dependencies', prompt: 'List all dependencies and their purposes' }
];

/**
 * Loading skeleton for AI generation
 */
function GeneratingSkeletonUI() {
  return (
    <div className="space-y-4 p-4" aria-hidden="true">
      <div className="flex items-center gap-3">
        <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
        <span className="text-gray-600 dark:text-gray-300 text-sm">
          Generating documentation...
        </span>
      </div>
      <div className="space-y-3">
        <Skeleton width="80%" height="1.5rem" />
        <Skeleton width="100%" height="0.875rem" />
        <Skeleton width="95%" height="0.875rem" />
        <Skeleton width="70%" height="0.875rem" />
        <Skeleton width="100%" height="0.875rem" className="mt-4" />
        <Skeleton width="88%" height="0.875rem" />
        <Skeleton width="60%" height="0.875rem" />
      </div>
    </div>
  );
}

/**
 * Inline loading spinner
 */
function InlineSpinner() {
  return (
    <svg
      className="animate-spin h-5 w-5 text-white"
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
 * Auto-resizing textarea component
 */
function AutoResizeTextarea({ 
  value, 
  onChange, 
  placeholder, 
  disabled,
  minRows = 3,
  maxRows = 10,
  ...props 
}) {
  const textareaRef = useRef(null);

  // Auto-resize on value change
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    
    // Calculate new height
    const lineHeight = parseInt(getComputedStyle(textarea).lineHeight) || 24;
    const minHeight = lineHeight * minRows;
    const maxHeight = lineHeight * maxRows;
    const newHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight);
    
    textarea.style.height = `${newHeight}px`;
  }, [value, minRows, maxRows]);

  return (
    <textarea
      ref={textareaRef}
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      rows={minRows}
      className={`
        w-full px-4 py-3 rounded-lg border resize-none
        bg-white dark:bg-gray-800
        text-gray-900 dark:text-gray-100
        placeholder-gray-400 dark:placeholder-gray-500
        border-gray-300 dark:border-gray-600
        focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
        disabled:opacity-50 disabled:cursor-not-allowed
        shadow-sm hover:shadow transition-shadow duration-200
      `}
      {...props}
    />
  );
}

/**
 * Model selector dropdown
 */
function ModelSelector({ value, onChange, disabled }) {
  return (
    <div className="flex items-center gap-2">
      <label 
        htmlFor="model-select" 
        className="text-sm text-gray-600 dark:text-gray-400"
      >
        Model:
      </label>
      <select
        id="model-select"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`
          px-3 py-1.5 rounded-lg border text-sm
          bg-white dark:bg-gray-800
          text-gray-900 dark:text-gray-100
          border-gray-300 dark:border-gray-600
          focus:outline-none focus:ring-2 focus:ring-blue-500
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
        aria-label="Select AI model"
      >
        {AI_MODELS.map(model => (
          <option key={model.id} value={model.id}>
            {model.name} ({model.description})
          </option>
        ))}
      </select>
    </div>
  );
}

/**
 * Follow-up suggestion chips
 */
function FollowUpSuggestions({ onSelect, disabled }) {
  return (
    <div className="flex flex-wrap gap-2">
      {FOLLOW_UP_SUGGESTIONS.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => onSelect(suggestion.prompt)}
          disabled={disabled}
          className={`
            px-3 py-1.5 text-sm rounded-full
            bg-gray-100 dark:bg-gray-700
            text-gray-700 dark:text-gray-300
            hover:bg-gray-200 dark:hover:bg-gray-600
            disabled:opacity-50 disabled:cursor-not-allowed
            transition-colors duration-200
          `}
          aria-label={`Use prompt: ${suggestion.label}`}
        >
          {suggestion.label}
        </button>
      ))}
    </div>
  );
}

/**
 * AIPanel Component
 * Provides AI-powered documentation generation interface
 * 
 * @param {Object} props
 * @param {string} props.jobId - Current job ID for context
 * @param {(doc: Object) => void} props.onDocGenerated - Callback when doc is generated
 */
export default function AIPanel({ jobId, onDocGenerated }) {
  // State
  const [prompt, setPrompt] = useState('');
  const [selectedModel, setSelectedModel] = useState('llama3-70b');
  const [generating, setGenerating] = useState(false);
  const [lastResult, setLastResult] = useState(null);

  // Hooks
  const { showToast } = useToast();

  /**
   * Handles form submission
   */
  const handleSubmit = useCallback(async (e) => {
    e?.preventDefault();

    // Validate prompt
    const trimmedPrompt = prompt.trim();
    if (!trimmedPrompt) {
      showToast('Please enter a prompt', 'error');
      return;
    }

    if (!jobId) {
      showToast('Please start an ingestion job first', 'error');
      return;
    }

    setGenerating(true);
    setLastResult(null);

    try {
      // Call API to generate documentation
      const result = await generateDoc(trimmedPrompt, jobId, selectedModel);

      // Validate response
      if (!result || !result.content) {
        throw new Error('Invalid response from AI');
      }

      setLastResult(result);
      
      // Notify parent component
      if (onDocGenerated) {
        onDocGenerated(result);
      }

      showToast('Documentation generated successfully!', 'success');

      // Clear prompt after success
      setPrompt('');

    } catch (err) {
      console.error('[AIPanel] Generation failed:', err);
      showToast(err.message || 'Failed to generate documentation', 'error');
    } finally {
      setGenerating(false);
    }
  }, [prompt, jobId, selectedModel, onDocGenerated, showToast]);

  /**
   * Handles follow-up suggestion click
   */
  const handleFollowUp = useCallback((suggestionPrompt) => {
    setPrompt(suggestionPrompt);
  }, []);

  /**
   * Handles keyboard shortcuts
   */
  const handleKeyDown = useCallback((e) => {
    // Cmd/Ctrl + Enter to submit
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden transition-colors duration-200">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              AI Documentation Generator
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Ask questions or request documentation about your codebase
            </p>
          </div>
          
          {/* Model Selector */}
          <ModelSelector
            value={selectedModel}
            onChange={setSelectedModel}
            disabled={generating}
          />
        </div>
      </div>

      {/* Content */}
      <div className="p-6 space-y-4">
        {/* Prompt Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Textarea */}
          <div>
            <label htmlFor="ai-prompt" className="sr-only">
              Enter your prompt
            </label>
            <AutoResizeTextarea
              id="ai-prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your code... e.g., 'Generate API documentation for the auth module' or 'Explain the data flow'"
              disabled={generating}
              aria-label="Enter your prompt for AI documentation generation"
              aria-describedby="prompt-hint"
            />
            <p id="prompt-hint" className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Press Ctrl+Enter to submit
            </p>
          </div>

          {/* Follow-up Suggestions */}
          <div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
              Quick prompts:
            </p>
            <FollowUpSuggestions 
              onSelect={handleFollowUp}
              disabled={generating}
            />
          </div>

          {/* Submit Button */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={generating || !prompt.trim() || !jobId}
              aria-busy={generating}
              aria-label="Generate documentation"
              className={`
                px-6 py-3 rounded-lg font-semibold
                bg-blue-600 hover:bg-blue-700
                text-white
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                dark:focus:ring-offset-gray-800
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-colors duration-200
                flex items-center gap-2
              `}
            >
              {generating ? (
                <>
                  <InlineSpinner />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Generate Documentation</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Generating Skeleton */}
        {generating && (
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <GeneratingSkeletonUI />
          </div>
        )}

        {/* No Job Warning */}
        {!jobId && (
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-sm text-yellow-700 dark:text-yellow-300">
                Start an ingestion job first to generate AI documentation
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
