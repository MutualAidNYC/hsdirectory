'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';

interface OrgSearchProps {
    initialQuery?: string;
}

/**
 * Client-side search input for the organizations page.
 * Submitting navigates to /organizations?q=... which triggers
 * a server-side re-fetch with the search parameter.
 */
export function OrgSearch({ initialQuery = '' }: OrgSearchProps) {
    const [query, setQuery] = useState(initialQuery);
    const router = useRouter();

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            router.push(`/organizations?q=${encodeURIComponent(query.trim())}`);
        } else {
            router.push('/organizations');
        }
    };

    const handleClear = () => {
        setQuery('');
        router.push('/organizations');
    };

    return (
        <form onSubmit={handleSubmit} className="max-w-xl">
            <div className="relative flex items-center">
                <svg className="absolute left-3 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search organizations by name..."
                    className="w-full pl-10 pr-24 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                />
                <div className="absolute right-2 flex items-center gap-1">
                    {query && (
                        <button
                            type="button"
                            onClick={handleClear}
                            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                            title="Clear search"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    )}
                    <button
                        type="submit"
                        className="px-4 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors"
                    >
                        Search
                    </button>
                </div>
            </div>
        </form>
    );
}
