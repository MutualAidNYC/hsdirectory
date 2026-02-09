import Link from 'next/link';
import { SearchBar } from './SearchBar';

interface HeaderProps {
    showSearch?: boolean;
}

/**
 * Site header with navigation and optional search bar.
 * Shows compact search on inner pages.
 */
export function Header({ showSearch = true }: HeaderProps) {
    return (
        <header className="sticky top-0 z-50 w-full border-b border-gray-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 dark:border-gray-800 dark:bg-gray-900/95">
            <div className="container mx-auto flex h-16 items-center justify-between px-4">
                {/* Logo */}
                <Link href="/" className="flex items-center gap-2">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white font-bold text-lg">
                        HS
                    </div>
                    <span className="font-semibold text-lg text-gray-900 dark:text-white">
                        HSDirectory
                    </span>
                </Link>

                {/* Search Bar (compact) */}
                {showSearch && (
                    <div className="hidden md:block flex-1 max-w-md mx-8">
                        <SearchBar size="sm" placeholder="Search services..." />
                    </div>
                )}

                {/* Navigation */}
                <nav className="flex items-center gap-6">
                    <Link
                        href="/services"
                        className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors"
                    >
                        Services
                    </Link>
                    <Link
                        href="/organizations"
                        className="text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-colors"
                    >
                        Organizations
                    </Link>
                </nav>
            </div>
        </header>
    );
}
