/**
 * Features section - 3-card grid showcasing key features
 */
export default function Features() {
  const features = [
    {
      title: 'AI-Powered Analysis',
      description: 'Our advanced AI understands your codebase structure, dependencies, and patterns to generate accurate, contextual documentation.',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      color: 'blue',
    },
    {
      title: 'Instant Documentation',
      description: 'Generate comprehensive README files, API docs, and code comments in seconds. No more hours spent writing documentation manually.',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      color: 'purple',
    },
    {
      title: 'Multi-Language Support',
      description: 'Works with JavaScript, TypeScript, Python, Go, Rust, and more. DocuMind adapts to your tech stack automatically.',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
      ),
      color: 'green',
    },
  ];

  const colorClasses = {
    blue: {
      bg: 'bg-blue-100 dark:bg-blue-900/30',
      text: 'text-blue-600 dark:text-blue-400',
      border: 'border-blue-200 dark:border-blue-800',
      hover: 'hover:border-blue-400 dark:hover:border-blue-600',
    },
    purple: {
      bg: 'bg-purple-100 dark:bg-purple-900/30',
      text: 'text-purple-600 dark:text-purple-400',
      border: 'border-purple-200 dark:border-purple-800',
      hover: 'hover:border-purple-400 dark:hover:border-purple-600',
    },
    green: {
      bg: 'bg-green-100 dark:bg-green-900/30',
      text: 'text-green-600 dark:text-green-400',
      border: 'border-green-200 dark:border-green-800',
      hover: 'hover:border-green-400 dark:hover:border-green-600',
    },
  };

  return (
    <div className="py-20 lg:py-28 bg-white dark:bg-gray-900 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            Why Choose DocuMind AI?
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Stop wasting time on documentation. Let AI handle it while you focus on building amazing software.
          </p>
        </div>

        {/* Features Grid */}
        <div 
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
          role="list"
          aria-label="Features list"
        >
          {features.map((feature, index) => {
            const colors = colorClasses[feature.color];
            return (
              <article
                key={index}
                className={`relative p-8 bg-white dark:bg-gray-800 rounded-2xl border-2 ${colors.border} ${colors.hover} shadow-sm hover:shadow-lg transition-all duration-300 group`}
                role="listitem"
              >
                {/* Icon */}
                <div className={`inline-flex p-4 rounded-xl ${colors.bg} ${colors.text} mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  {feature.icon}
                </div>

                {/* Content */}
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                  {feature.description}
                </p>

                {/* Decorative corner */}
                <div className={`absolute top-0 right-0 w-16 h-16 ${colors.bg} rounded-bl-3xl rounded-tr-2xl opacity-50`} />
              </article>
            );
          })}
        </div>
      </div>
    </div>
  );
}
