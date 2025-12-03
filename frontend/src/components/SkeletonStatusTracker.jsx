/**
 * frontend/src/components/SkeletonStatusTracker.jsx
 * Skeleton loading placeholder for StatusTracker component
 * 
 * Displays when:
 * - StatusTracker is loading AND no job data exists yet
 * 
 * Structure matches actual StatusTracker layout:
 * - Header with job ID
 * - Status badge
 * - Progress bar
 * - Timeline steps
 */

import Skeleton, { SkeletonButton } from './Skeleton';

/**
 * SkeletonStatusTracker Component
 * Placeholder version of StatusTracker during initial load
 */
export default function SkeletonStatusTracker() {
  return (
    <div 
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 space-y-6 transition-opacity duration-300"
      aria-hidden="true"
      aria-label="Loading job status"
    >
      {/* ====== Header Section Skeleton ====== */}
      <div className="flex items-center justify-between">
        {/* Left: Title and Job ID */}
        <div className="space-y-2">
          <Skeleton width="120px" height="1.25rem" rounded="md" />
          <Skeleton width="280px" height="0.875rem" rounded="md" />
        </div>
        
        {/* Right: Refresh button and timestamp */}
        <div className="text-right space-y-2">
          <Skeleton width="70px" height="1rem" rounded="md" />
          <Skeleton width="90px" height="0.75rem" rounded="md" />
        </div>
      </div>

      {/* ====== Status Badge Skeleton ====== */}
      <div className="flex items-center gap-3">
        <Skeleton width="140px" height="1.75rem" rounded="full" />
        <Skeleton width="8px" height="8px" rounded="full" />
      </div>

      {/* ====== Progress Bar Section Skeleton ====== */}
      <div className="space-y-2">
        {/* Progress label row */}
        <div className="flex justify-between">
          <Skeleton width="60px" height="0.875rem" />
          <Skeleton width="30px" height="0.875rem" />
        </div>
        
        {/* Progress bar */}
        <div className="w-full h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <Skeleton 
            width="45%" 
            height="100%" 
            rounded="full" 
            className="bg-gray-400 dark:bg-gray-600" 
          />
        </div>
      </div>

      {/* ====== Timeline Steps Skeleton ====== */}
      <div className="pt-4">
        <div className="flex items-center justify-between">
          {/* 6 timeline step placeholders */}
          {[1, 2, 3, 4, 5, 6].map((step) => (
            <div key={step} className="flex flex-col items-center flex-1">
              {/* Step circle */}
              <Skeleton 
                width="2rem" 
                height="2rem" 
                rounded="full" 
              />
              {/* Step label */}
              <Skeleton 
                width="2.5rem" 
                height="0.75rem" 
                className="mt-2"
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
