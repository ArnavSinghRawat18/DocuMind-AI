/**
 * frontend/src/components/Skeleton.jsx
 * Reusable skeleton loading block component
 * 
 * Usage:
 *   <Skeleton width="100%" height="40px" />
 *   <Skeleton className="h-6 w-48" />
 *   <Skeleton rounded="full" height="3rem" width="3rem" />
 */

/**
 * Skeleton Component
 * Displays a pulsing placeholder block for loading states
 * 
 * @param {Object} props
 * @param {string} [props.width='100%'] - Width of skeleton (CSS value)
 * @param {string} [props.height='1rem'] - Height of skeleton (CSS value)
 * @param {'none'|'sm'|'md'|'lg'|'xl'|'2xl'|'full'} [props.rounded='md'] - Border radius
 * @param {string} [props.className] - Additional CSS classes (overrides width/height)
 */
export default function Skeleton({ 
  width = '100%', 
  height = '1rem', 
  rounded = 'md',
  className = '' 
}) {
  // Map rounded prop to Tailwind classes
  const roundedClasses = {
    none: 'rounded-none',
    sm: 'rounded-sm',
    md: 'rounded-md',
    lg: 'rounded-lg',
    xl: 'rounded-xl',
    '2xl': 'rounded-2xl',
    full: 'rounded-full'
  };

  const roundedClass = roundedClasses[rounded] || 'rounded-md';

  // If className is provided, use it for sizing; otherwise use inline styles
  const hasCustomClass = className.includes('w-') || className.includes('h-');
  
  const style = hasCustomClass ? {} : { width, height };

  return (
    <div
      aria-hidden="true"
      role="presentation"
      className={`
        bg-gray-300 dark:bg-gray-700
        animate-pulse
        ${roundedClass}
        ${className}
      `}
      style={style}
    />
  );
}

/**
 * SkeletonText Component
 * Displays multiple lines of skeleton text
 * 
 * @param {Object} props
 * @param {number} [props.lines=3] - Number of text lines
 * @param {string} [props.gap='2'] - Gap between lines (Tailwind spacing)
 */
export function SkeletonText({ lines = 3, gap = '2' }) {
  return (
    <div className={`space-y-${gap}`} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton 
          key={i} 
          height="0.875rem"
          // Last line is shorter for natural look
          width={i === lines - 1 ? '75%' : '100%'}
        />
      ))}
    </div>
  );
}

/**
 * SkeletonCircle Component
 * Displays a circular skeleton (e.g., for avatars)
 * 
 * @param {Object} props
 * @param {string} [props.size='2.5rem'] - Diameter of circle
 */
export function SkeletonCircle({ size = '2.5rem' }) {
  return (
    <Skeleton 
      width={size} 
      height={size} 
      rounded="full" 
    />
  );
}

/**
 * SkeletonButton Component
 * Displays a button-shaped skeleton
 * 
 * @param {Object} props
 * @param {string} [props.width='6rem'] - Button width
 */
export function SkeletonButton({ width = '6rem' }) {
  return (
    <Skeleton 
      width={width} 
      height="2.5rem" 
      rounded="lg" 
    />
  );
}
