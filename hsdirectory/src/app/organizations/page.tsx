import { Metadata } from "next";
import { getOrganizations, Organization } from "@/lib/api";
import { OrganizationCard } from "@/components/organizations/OrganizationCard";
import { Pagination } from "@/components/ui/Pagination";
import { OrgSearch } from "./OrgSearch";

export const metadata: Metadata = {
    title: "Organizations",
    description: "Browse organizations providing community services and resources.",
};

interface OrganizationsPageProps {
    searchParams: Promise<{ page?: string; q?: string }>;
}

/**
 * Organizations listing page with search and pagination.
 * The `q` param drives server-side text search against the API.
 */
export default async function OrganizationsPage({ searchParams }: OrganizationsPageProps) {
    const params = await searchParams;
    const page = parseInt(params.page || "1");
    const query = params.q || "";

    let organizations: Organization[] = [];
    let totalPages = 1;
    let totalItems = 0;
    let error = null;

    try {
        const response = await getOrganizations(page, 12, query || undefined);
        organizations = response.contents || [];
        totalPages = response.total_pages || 1;
        totalItems = response.total_items || 0;
    } catch (e) {
        error = e instanceof Error ? e.message : "Failed to load organizations";
        console.error("Failed to fetch organizations:", e);
    }

    // Build pagination URL preserving search query
    const paginationBase = query ? `/organizations?q=${encodeURIComponent(query)}` : "/organizations";

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Page Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                    Organizations
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    {totalItems.toLocaleString()} organizations providing community services
                </p>
            </div>

            {/* Search Input */}
            <div className="mb-8">
                <OrgSearch initialQuery={query} />
            </div>

            {/* Error State */}
            {error && (
                <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 mb-8">
                    <p className="text-red-700 dark:text-red-400">{error}</p>
                </div>
            )}

            {/* Organizations Grid */}
            {organizations.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    {organizations.map((org) => (
                        <OrganizationCard key={org.id} organization={org} />
                    ))}
                </div>
            ) : !error ? (
                <div className="text-center py-16">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-4">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                        {query ? `No results for "${query}"` : "No organizations found"}
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                        {query ? "Try a different search term." : "No organizations are currently available."}
                    </p>
                </div>
            ) : null}

            {/* Pagination */}
            {totalPages > 1 && (
                <Pagination currentPage={page} totalPages={totalPages} baseUrl={paginationBase} />
            )}
        </div>
    );
}
