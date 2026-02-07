import Link from 'next/link';

/**
 * Custom 404 Not Found page.
 */
export default function NotFound() {
    return (
        <div className="container mx-auto px-4 py-16">
            <div className="max-w-md mx-auto text-center">
                {/* Icon */}
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 dark:bg-gray-800 mb-6">
                    <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>

                {/* Title */}
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                    404
                </h1>
                <h2 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-4">
                    Page Not Found
                </h2>

                {/* Description */}
                <p className="text-gray-600 dark:text-gray-400 mb-8">
                    Sorry, we couldn&apos;t find the page you&apos;re looking for.
                    It may have been moved or deleted.
                </p>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link
                        href="/"
                        className="inline-flex items-center justify-center px-6 py-3 rounded-lg 
              bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
                    >
                        Go Home
                    </Link>
                    <Link
                        href="/services"
                        className="inline-flex items-center justify-center px-6 py-3 rounded-lg 
              border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300
              hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                        Browse Services
                    </Link>
                </div>
            </div>
        </div>
    );
}
