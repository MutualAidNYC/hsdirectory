'use client';

import { useState, useMemo, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';

/** NYC boroughs and the city names that map to them in address data. */
const BOROUGH_MAP: Record<string, string[]> = {
    'Manhattan': ['New York', 'Manhattan'],
    'Brooklyn': ['Brooklyn'],
    'Bronx': ['Bronx', 'The Bronx'],
    'Queens': ['Queens'],
    'Staten Island': ['Staten Island'],
};
const BOROUGHS = Object.keys(BOROUGH_MAP);

/** Extract the city/borough from a formatted address string ("street, city, state, zip"). */
function extractBorough(address?: string): string | null {
    if (!address) return null;
    const parts = address.split(',').map(p => p.trim());
    if (parts.length < 2) return null;
    const city = parts[1];
    for (const [borough, cities] of Object.entries(BOROUGH_MAP)) {
        if (cities.some(c => c.toLowerCase() === city.toLowerCase())) return borough;
    }
    return null;
}

interface Service {
    id: string;
    name: string;
    description?: string;
    address?: string;
    phone?: string;
    url?: string;
    needFocus?: string[];
    communityFocus?: string[];
    latitude?: number;
    longitude?: number;
}

interface MapPageClientProps {
    services: Service[];
    needCategories: string[];
    communityCategories: string[];
}

/**
 * Client component for interactive map page with URL-synced filters.
 *
 * Reads initial filter state from URL query params (?category=, ?community=)
 * and pushes URL updates when the user changes filters, enabling sharable
 * filtered views like /map?category=Housing.
 */
export default function MapPageClient({
    services,
    needCategories,
    communityCategories
}: MapPageClientProps) {
    const searchParams = useSearchParams();
    const router = useRouter();

    // Initialize state from URL query params
    const [searchQuery, setSearchQuery] = useState<string>(
        searchParams.get('q') || ''
    );
    const [selectedNeed, setSelectedNeed] = useState<string>(
        searchParams.get('category') || ''
    );
    const [selectedCommunity, setSelectedCommunity] = useState<string>(
        searchParams.get('community') || ''
    );
    const [selectedBorough, setSelectedBorough] = useState<string>(
        searchParams.get('borough') || ''
    );

    /**
     * Push filter state into the browser URL so that filtered views are
     * bookmarkable and sharable (e.g. /map?category=Housing&q=food&borough=Brooklyn).
     */
    const syncUrl = useCallback((query: string, need: string, community: string, borough: string) => {
        const params = new URLSearchParams();
        if (query) params.set('q', query);
        if (need) params.set('category', need);
        if (community) params.set('community', community);
        if (borough) params.set('borough', borough);
        const qs = params.toString();
        router.replace(qs ? `/map?${qs}` : '/map', { scroll: false });
    }, [router]);

    // Handle search submit
    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        syncUrl(searchQuery, selectedNeed, selectedCommunity, selectedBorough);
    };

    // Handle need category change
    const handleNeedChange = (value: string) => {
        setSelectedNeed(value);
        syncUrl(searchQuery, value, selectedCommunity, selectedBorough);
    };

    // Handle community focus change
    const handleCommunityChange = (value: string) => {
        setSelectedCommunity(value);
        syncUrl(searchQuery, selectedNeed, value, selectedBorough);
    };

    // Handle borough change
    const handleBoroughChange = (value: string) => {
        setSelectedBorough(value);
        syncUrl(searchQuery, selectedNeed, selectedCommunity, value);
    };

    // Clear all filters
    const handleClearFilters = () => {
        setSearchQuery('');
        setSelectedNeed('');
        setSelectedCommunity('');
        setSelectedBorough('');
        syncUrl('', '', '', '');
    };

    // Filter and rank services by relevance.
    // Each search token earns points based on which field it matches:
    //   Name match = 4pts, Tag match = 3pts, Address = 2pts, Description = 1pt.
    // Results are sorted by total score (highest first).
    const filteredServices = useMemo(() => {
        const STOP_WORDS = new Set(['in', 'the', 'a', 'an', 'and', 'or', 'for', 'of', 'to', 'at', 'on', 'near', 'by', 'with']);
        const tokens = searchQuery
            .toLowerCase()
            .split(/\s+/)
            .filter(t => t.length > 0 && !STOP_WORDS.has(t));

        const scored = services.map(service => {
            // Apply dropdown filters first (pass/fail)
            if (selectedNeed && !service.needFocus?.includes(selectedNeed)) return null;
            if (selectedCommunity && !service.communityFocus?.includes(selectedCommunity)) return null;
            if (selectedBorough && extractBorough(service.address) !== selectedBorough) return null;

            if (tokens.length === 0) return { service, score: 0 };

            const nameLower = (service.name || '').toLowerCase();
            const descLower = (service.description || '').toLowerCase();
            const addrLower = (service.address || '').toLowerCase();
            const tagsLower = [
                ...(service.needFocus || []),
                ...(service.communityFocus || []),
            ].join(' ').toLowerCase();
            const allText = `${nameLower} ${descLower} ${addrLower} ${tagsLower}`;

            // Every token must appear somewhere (AND logic)
            if (!tokens.every(t => allText.includes(t))) return null;

            // Score each token by best field match
            let score = 0;
            for (const token of tokens) {
                if (nameLower.includes(token)) score += 4;
                else if (tagsLower.includes(token)) score += 3;
                else if (addrLower.includes(token)) score += 2;
                else if (descLower.includes(token)) score += 1;
            }
            return { service, score };
        });

        return scored
            .filter((s): s is { service: Service; score: number } => s !== null)
            .sort((a, b) => b.score - a.score)
            .map(s => s.service);
    }, [services, searchQuery, selectedNeed, selectedCommunity, selectedBorough]);

    // Get locations for map
    const mapLocations = useMemo(() => {
        return filteredServices
            .filter(s => s.latitude && s.longitude)
            .map(s => ({
                id: s.id,
                name: s.name,
                latitude: s.latitude!,
                longitude: s.longitude!,
                serviceName: s.name,
                serviceId: s.id,
            }));
    }, [filteredServices]);

    return (
        <div className="flex h-[calc(100vh-80px)] overflow-hidden">
            {/* Left Column: Filters */}
            <div className="w-64 flex-shrink-0 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 p-4 overflow-y-auto">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    Filters
                </h2>

                {/* Search Input */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Search
                    </label>
                    <form onSubmit={handleSearchSubmit}>
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => {
                                setSearchQuery(e.target.value);
                                syncUrl(e.target.value, selectedNeed, selectedCommunity, selectedBorough);
                            }}
                            placeholder="Search services..."
                            className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        />
                    </form>
                </div>

                {/* Need Category Filter */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Need Category
                    </label>
                    <select
                        value={selectedNeed}
                        onChange={(e) => handleNeedChange(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="">All Categories</option>
                        {needCategories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                </div>

                {/* Community Focus Filter */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Community Focus
                    </label>
                    <select
                        value={selectedCommunity}
                        onChange={(e) => handleCommunityChange(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="">All Communities</option>
                        {communityCategories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                </div>

                {/* Borough Filter */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Borough
                    </label>
                    <select
                        value={selectedBorough}
                        onChange={(e) => handleBoroughChange(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                        <option value="">All Boroughs</option>
                        {BOROUGHS.map(b => (
                            <option key={b} value={b}>{b}</option>
                        ))}
                    </select>
                </div>

                {/* Clear Filters */}
                {(searchQuery || selectedNeed || selectedCommunity || selectedBorough) && (
                    <button
                        onClick={handleClearFilters}
                        className="w-full px-4 py-2 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                    >
                        Clear All Filters
                    </button>
                )}

                {/* Results count */}
                <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                    {filteredServices.length} services found
                </div>
            </div>

            {/* Middle Column: Service Cards */}
            <div className="w-[32rem] flex-shrink-0 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
                <div className="p-4 space-y-4">
                    {filteredServices.length === 0 ? (
                        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                            No services match your filters
                        </div>
                    ) : (
                        filteredServices.map(service => (
                            <ServiceCard key={service.id} service={service} />
                        ))
                    )}
                </div>
            </div>

            {/* Right Column: Map */}
            <div className="flex-1 relative h-full min-w-0">
                <MapViewDynamic locations={mapLocations} />
            </div>
        </div>
    );
}

/**
 * Service card component
 */
function ServiceCard({ service }: { service: Service }) {
    return (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                {service.name}
            </h3>

            {service.address && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 flex items-start gap-2">
                    <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    <span className="line-clamp-2">{service.address}</span>
                </p>
            )}

            {service.phone && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                    <a href={`tel:${service.phone}`} className="hover:text-blue-600">{service.phone}</a>
                </p>
            )}

            {service.url && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                    </svg>
                    <a
                        href={service.url.startsWith('http') ? service.url : `https://${service.url}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-blue-600 truncate"
                    >
                        {service.url.replace(/^https?:\/\//, '').split('/')[0]}
                    </a>
                </p>
            )}

            {service.description && (
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">
                    {service.description}
                </p>
            )}

            {/* Service Category tags */}
            {service.needFocus && service.needFocus.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                    {service.needFocus.map((need, i) => (
                        <span
                            key={`need-${i}`}
                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
                        >
                            {need}
                        </span>
                    ))}
                </div>
            )}

            {/* Community Focus tags */}
            {service.communityFocus && service.communityFocus.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                    {service.communityFocus.map((community, i) => (
                        <span
                            key={`community-${i}`}
                            className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300"
                        >
                            {community}
                        </span>
                    ))}
                </div>
            )}

            <Link
                href={`/services/${service.id}`}
                className="inline-flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
            >
                More Details
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
            </Link>
        </div>
    );
}

/**
 * Dynamic map component (lazy loaded)
 */
import dynamic from 'next/dynamic';

const MapViewDynamic = dynamic(
    () => import('@/components/map/MapView'),
    {
        ssr: false,
        loading: () => (
            <div className="w-full h-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                <div className="text-gray-500">Loading map...</div>
            </div>
        )
    }
);
