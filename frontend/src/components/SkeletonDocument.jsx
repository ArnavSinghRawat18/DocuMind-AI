/**
 * frontend/src/components/SkeletonDocument.jsx
 * Skeleton loading placeholder for DocumentViewer component
 * 
 * Displays when:
 * - Document is expected but not yet loaded
 * - Transitioning between documents
 * 
 * Structure matches actual DocumentViewer layout:
 * - Header with title and action buttons
 * - Content area with text lines
 * - Optional metadata section
 */

import Skeleton, { SkeletonText, SkeletonButton } from './Skeleton';

/**
 * SkeletonDocument Component
 * Placeholder version of DocumentViewer during load
 */
export default function SkeletonDocument() {
  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden transition-opacity duration-300"
      aria-hidden="true"
      aria-label="Loading document"
    >
      {/* ====== Header Section Skeleton ====== */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          {/* Title skeleton */}
          <Skeleton width="200px" height="1.5rem" rounded="md" />

          {/* Action buttons skeleton */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Copy Markdown button */}
            <Skeleton width="130px" height="2.25rem" rounded="lg" />
            {/* Download button */}
            <Skeleton width="120px" height="2.25rem" rounded="lg" />
            {/* Open Raw button */}
            <Skeleton width="100px" height="2.25rem" rounded="lg" />
          </div>
        </div>
      </div>

      {/* ====== Content Area Skeleton ====== */}
      <div className="p-6 space-y-4">
        {/* Heading skeleton */}
        <Skeleton width="60%" height="1.75rem" rounded="md" />
        
        {/* Paragraph 1 */}
        <div className="space-y-2">
          <Skeleton width="100%" height="0.875rem" />
          <Skeleton width="95%" height="0.875rem" />
          <Skeleton width="88%" height="0.875rem" />
          <Skeleton width="70%" height="0.875rem" />
        </div>

        {/* Subheading skeleton */}
        <Skeleton width="45%" height="1.25rem" rounded="md" className="mt-6" />

        {/* Paragraph 2 */}
        <div className="space-y-2">
          <Skeleton width="100%" height="0.875rem" />
          <Skeleton width="92%" height="0.875rem" />
          <Skeleton width="85%" height="0.875rem" />
        </div>

        {/* Code block skeleton */}
        <div className="bg-gray-100 dark:bg-gray-900 rounded-lg p-4 space-y-2 mt-4">
          <Skeleton width="80%" height="0.875rem" className="bg-gray-300 dark:bg-gray-700" />
          <Skeleton width="65%" height="0.875rem" className="bg-gray-300 dark:bg-gray-700" />
          <Skeleton width="90%" height="0.875rem" className="bg-gray-300 dark:bg-gray-700" />
          <Skeleton width="50%" height="0.875rem" className="bg-gray-300 dark:bg-gray-700" />
        </div>

        {/* Paragraph 3 */}
        <div className="space-y-2 mt-4">
          <Skeleton width="100%" height="0.875rem" />
          <Skeleton width="78%" height="0.875rem" />
        </div>
      </div>

      {/* ====== Metadata Section Skeleton (Chunks Used) ====== */}
      <div className="px-6 pb-6">
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          {/* Collapsible header */}
          <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800 flex items-center justify-between">
            <Skeleton width="160px" height="0.875rem" />
            <Skeleton width="1.25rem" height="1.25rem" rounded="md" />
          </div>
        </div>
      </div>
    </div>
  );
}
