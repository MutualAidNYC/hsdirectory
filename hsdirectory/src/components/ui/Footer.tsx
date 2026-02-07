import Link from 'next/link';

/**
 * Site footer with links and attribution.
 */
export function Footer() {
    return (
        <footer className="border-t border-gray-200 bg-gray-50 dark:border-gray-800 dark:bg-gray-900">
            <div className="container mx-auto px-4 py-8">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    {/* Branding */}
                    <div className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white font-bold text-sm">
                            HS
                        </div>
                        <span className="font-medium text-gray-700 dark:text-gray-300">
                            HSDirectory
                        </span>
                    </div>

                    {/* Links */}
                    <nav className="flex flex-wrap gap-6 text-sm text-gray-600 dark:text-gray-400">
                        <Link href="/services" className="hover:text-gray-900 dark:hover:text-white">
                            Services
                        </Link>
                        <Link href="/organizations" className="hover:text-gray-900 dark:hover:text-white">
                            Organizations
                        </Link>
                        <Link href="/map" className="hover:text-gray-900 dark:hover:text-white">
                            Map
                        </Link>
                    </nav>

                    {/* Attribution */}
                    <p className="text-sm text-gray-500 dark:text-gray-500">
                        Powered by{' '}
                        <a
                            href="https://openreferral.org"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline dark:text-blue-400"
                        >
                            Open Referral HSDS
                        </a>
                    </p>
                </div>
            </div>
        </footer>
    );
}
