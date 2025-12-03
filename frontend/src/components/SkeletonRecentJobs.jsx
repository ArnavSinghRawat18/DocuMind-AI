/**
 * frontend/src/components/SkeletonRecentJobs.jsx
 * Skeleton loading placeholder for Recent Jobs list
 * 
 * Displays when:
 * - Recent jobs are being loaded from localStorage on mount
 * - Initial app load before jobs data is available
 * 
 * Structure matches actual RecentJobsPanel layout:
 * - Header title
 * - 3 job item placeholders
 */

import Skeleton from './Skeleton';

/**
 * Single skeleton job item
 */
function SkeletonJobItem() {
  return (
    <div 
      className="w-full p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50"
      aria-hidden="true"
    >
      {/* Top row: repo name and status badge */}
      <div className="flex items-start justify-between gap-2">
        <Skeleton width="70%" height="0.875rem" rounded="md" />
        <Skeleton width="60px" height="1.25rem" rounded="full" />
      </div>
      
      {/* URL row */}
      <Skeleton width="90%" height="0.75rem" className="mt-2" />
      
      {/* Timestamp row */}
      <Skeleton width="50px" height="0.75rem" className="mt-2" />
    </div>
  );
}

/**
 * SkeletonRecentJobs Component
 * Placeholder version of RecentJobsPanel during load
 * 
 * @param {Object} props
 * @param {number} [props.count=3] - Number of skeleton job items to show
 */
export default function SkeletonRecentJobs({ count = 3 }) {
  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4 transition-opacity duration-300"
      aria-hidden="true"
      aria-label="Loading recent jobs"
    >
      {/* ====== Header Skeleton ====== */}
      <Skeleton width="100px" height="0.875rem" rounded="md" className="mb-3" />

      {/* ====== Job Items Skeleton ====== */}
      <div className="space-y-2">
        {Array.from({ length: count }).map((_, index) => (
          <SkeletonJobItem key={index} />
        ))}
      </div>
    </div>
  );
}
