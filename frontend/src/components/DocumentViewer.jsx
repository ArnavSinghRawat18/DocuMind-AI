/**
 * frontend/src/components/DocumentViewer.jsx
 * Document viewer component for rendering generated documentation
 * 
 * Optional dependency: react-markdown
 * Install with: npm i react-markdown
 * If not installed, content will be rendered as plain preformatted text.
 * 
 * This component is safe for client-side rendering.
 */

import { useState, useEffect } from 'react';
import SkeletonDocument from './SkeletonDocument';

// Try to import react-markdown, fallback to null if not available
let ReactMarkdown = null;
try {
  ReactMarkdown = require('react-markdown').default;
} catch (e) {
  // react-markdown not installed, will use fallback
}

/**
 * Copies text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    console.error('[DocumentViewer] Failed to copy:', err);
    return false;
  }
}

/**
 * Downloads content as a file
 * @param {string} content - File content
 * @param {string} filename - Desired filename
 */
function downloadAsFile(content, filename) {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Copy button with tooltip feedback
 */
function CopyButton({ text, label, className = '' }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <button
      onClick={handleCopy}
      aria-label={label}
      className={`
        relative px-3 py-2 text-sm font-medium rounded-lg
        bg-gray-100 dark:bg-gray-700 
        text-gray-700 dark:text-gray-300
        hover:bg-gray-200 dark:hover:bg-gray-600
        transition-colors duration-200
        flex items-center gap-2
        ${className}
      `}
    >
      {copied ? (
        <>
          <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-green-500">Copied!</span>
        </>
      ) : (
        <>
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span>{label}</span>
        </>
      )}
    </button>
  );
}

/**
 * Collapsible panel for chunks used
 */
function ChunksPanel({ chunks }) {
  const [isOpen, setIsOpen] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState(null);

  if (!chunks || chunks.length === 0) return null;

  const handleCopyChunk = async (chunk, index) => {
    const text = `${chunk.filePath}:${chunk.startLine}-${chunk.endLine}`;
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    }
  };

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-750 transition-colors"
        aria-expanded={isOpen}
        aria-controls="chunks-list"
      >
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Source Chunks Used ({chunks.length})
        </span>
        <svg
          className={`w-5 h-5 text-gray-500 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div id="chunks-list" className="divide-y divide-gray-200 dark:divide-gray-700">
          {chunks.map((chunk, index) => (
            <div
              key={index}
              className="px-4 py-2 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-mono text-gray-600 dark:text-gray-400 truncate">
                  {chunk.filePath}
                </p>
                <p className="text-xs text-gray-500">
                  Lines {chunk.startLine} - {chunk.endLine}
                </p>
              </div>
              <button
                onClick={() => handleCopyChunk(chunk, index)}
                className="ml-2 p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                aria-label={`Copy ${chunk.filePath} reference`}
              >
                {copiedIndex === index ? (
                  <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Markdown/Text content renderer
 */
function ContentRenderer({ content }) {
  if (!content) return null;

  // Use react-markdown if available, otherwise fallback to pre
  if (ReactMarkdown) {
    return (
      <div className="prose prose-gray dark:prose-invert max-w-none">
        <ReactMarkdown>{content}</ReactMarkdown>
      </div>
    );
  }

  // Fallback: render as preformatted text
  return (
    <pre className="whitespace-pre-wrap text-sm text-gray-800 dark:text-gray-200 font-mono bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto">
      {content}
    </pre>
  );
}

/**
 * DocumentViewer Component
 * Renders generated documentation with utilities for copying, downloading, and viewing source chunks
 * 
 * @param {Object} props
 * @param {Object} props.doc - Document object with title, content, raw_url, chunksUsed
 * @param {boolean} [props.showMeta=true] - Whether to show metadata section
 * @param {boolean} [props.loading=false] - Whether document is loading
 */
export default function DocumentViewer({ doc, showMeta = true, loading = false }) {
  const [contentKey, setContentKey] = useState(0);

  // Update content key when content changes for aria-live
  useEffect(() => {
    if (doc?.content) {
      setContentKey(prev => prev + 1);
    }
  }, [doc?.content]);

  // ====== Loading State: Show skeleton when loading prop is true ======
  if (loading) {
    return <SkeletonDocument />;
  }

  // Empty state
  if (!doc || !doc.content) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 text-center">
        <div className="text-gray-400 mb-4">
          <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-600 dark:text-gray-400">
          No document generated yet
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
          Start an ingestion job to generate documentation.
        </p>
      </div>
    );
  }

  const { title, content, raw_url, chunksUsed } = doc;
  const filename = `${title || 'document'}.md`.replace(/[^a-zA-Z0-9.-]/g, '_');

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Title */}
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            {title || 'Generated Document'}
          </h2>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <CopyButton
              text={content}
              label="Copy Markdown"
            />

            <button
              onClick={() => downloadAsFile(content, filename)}
              aria-label="Download as Markdown file"
              className="px-3 py-2 text-sm font-medium rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download .md
            </button>

            {raw_url && (
              <a
                href={raw_url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Open raw document in new tab"
                className="px-3 py-2 text-sm font-medium rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                Open Raw
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div
        className="p-6"
        aria-live="polite"
        aria-atomic="true"
        key={contentKey}
      >
        <ContentRenderer content={content} />
      </div>

      {/* Metadata Section */}
      {showMeta && chunksUsed && chunksUsed.length > 0 && (
        <div className="px-6 pb-6">
          <ChunksPanel chunks={chunksUsed} />
        </div>
      )}
    </div>
  );
}
