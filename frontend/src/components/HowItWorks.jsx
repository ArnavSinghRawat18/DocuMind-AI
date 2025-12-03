/**
 * HowItWorks section - 3-step visual process
 */
export default function HowItWorks() {
  const steps = [
    {
      number: '1',
      title: 'Paste URL',
      description: 'Simply paste your GitHub repository URL into the input field. Public and private repos supported.',
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      ),
    },
    {
      number: '2',
      title: 'Ingest & Index',
      description: 'Our system clones your repo, analyzes the codebase structure, and indexes all files for AI processing.',
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
        </svg>
      ),
    },
    {
      number: '3',
      title: 'Generate Docs',
      description: 'Ask questions or request documentation. Our AI generates accurate, contextual documentation instantly.',
      icon: (
        <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="py-20 lg:py-28 bg-gray-50 dark:bg-gray-800/50 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">
            How It Works
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Three simple steps to transform your codebase into comprehensive documentation.
          </p>
        </div>

        {/* Steps */}
        <div 
          className="relative flex flex-col lg:flex-row items-center lg:items-start justify-center gap-8 lg:gap-4"
          role="list"
          aria-label="Process steps"
        >
          {/* Connecting line (desktop) */}
          <div className="hidden lg:block absolute top-20 left-1/2 -translate-x-1/2 w-2/3 h-1 bg-gradient-to-r from-blue-200 via-purple-200 to-green-200 dark:from-blue-800 dark:via-purple-800 dark:to-green-800 rounded-full" />

          {steps.map((step, index) => (
            <div
              key={index}
              className="relative flex flex-col items-center text-center lg:flex-1 max-w-sm"
              role="listitem"
            >
              {/* Step circle */}
              <div className="relative z-10 mb-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/25 dark:shadow-blue-500/10">
                  <div className="text-white">
                    {step.icon}
                  </div>
                </div>
                {/* Step number badge */}
                <div className="absolute -top-2 -right-2 w-8 h-8 bg-white dark:bg-gray-900 rounded-full border-4 border-blue-500 flex items-center justify-center">
                  <span className="text-sm font-bold text-blue-600 dark:text-blue-400">
                    {step.number}
                  </span>
                </div>
              </div>

              {/* Content */}
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
                {step.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
                {step.description}
              </p>

              {/* Arrow (mobile only) */}
              {index < steps.length - 1 && (
                <div className="lg:hidden my-4 text-gray-300 dark:text-gray-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
