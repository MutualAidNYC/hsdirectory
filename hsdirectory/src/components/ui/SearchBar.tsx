'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';

interface SearchBarProps {
    initialQuery?: string;
    size?: 'sm' | 'lg';
    placeholder?: string;
}

/**
 * Reusable search bar component for filtering services.
 * Navigates to /services with search query on submit.
 */
export function SearchBar({
    initialQuery = '',
    size = 'lg',
    placeholder = 'Search for services...'
}: SearchBarProps) {
    const [query, setQuery] = useState(initialQuery);
    const router = useRouter();

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        if (query.trim()) {
            router.push(`/map?q=${encodeURIComponent(query.trim())}`);
        } else {
            router.push('/map');
        }
    };

    const inputClasses = size === 'lg'
        ? 'h-14 text-lg px-6'
        : 'h-10 text-sm px-4';

    return (
        <form onSubmit={handleSubmit} className="w-full max-w-2xl">
            <div className="relative flex items-center">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={placeholder}
                    className={`w-full rounded-full border border-gray-300 bg-white shadow-sm 
            focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20
            dark:border-gray-600 dark:bg-gray-800 dark:text-white
            ${inputClasses}`}
                />
                <button
                    type="submit"
                    className={`absolute right-2 rounded-full bg-blue-600 text-white 
            hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500
            transition-colors ${size === 'lg' ? 'px-6 py-2' : 'px-4 py-1.5 text-sm'}`}
                >
                    Search
                </button>
            </div>
        </form>
    );
}
