import { Metadata } from "next";
import Link from "next/link";
import { getServices, Service } from "@/lib/api";
import { ServiceCard } from "@/components/services/ServiceCard";
import { Pagination } from "@/components/ui/Pagination";
import { SearchBar } from "@/components/ui/SearchBar";

export const metadata: Metadata = {
    title: "Browse Services",
    description: "Search and browse all available community services and resources.",
};

/**
 * Category display names mapping (needFocus values to display names)
 */
const CATEGORY_DISPLAY_NAMES: Record<string, string> = {
    "Food": "Food",
    "Housing": "Housing",
    "Legal": "Legal",
    "Medical": "Medical",
    "Education": "Education",
    "Jobs": "Jobs",
    "Money": "Money",
    "Mental & Behavioral Health": "Mental Health",
    "Safety from Violence": "Safety",
    "Clothing": "Clothing",
    "Social Service Guidance": "Social Services",
};

interface ServicesPageProps {
    searchParams: Promise<{ page?: string; q?: string; category?: string }>;
}

/**
 * Services listing page with search, category filtering, and pagination.
 */
export default async function ServicesPage({ searchParams }: ServicesPageProps) {
    const params = await searchParams;
    const page = parseInt(params.page || "1");
    const query = params.q || "";
    const category = params.category || "";

    const categoryDisplayName = category ? (CATEGORY_DISPLAY_NAMES[category] || category) : null;

    let services: Service[] = [];
    let totalPages = 1;
    let totalItems = 0;
    let error = null;

    try {
        // For category filtering, we need more services to filter client-side
        // API limit is 100, so we fetch multiple pages if filtering
        let allServices: Service[] = [];

        if (category) {
            // Fetch up to 5 pages for category filtering
            for (let p = 1; p <= 5; p++) {
                const response = await getServices(p, 100, query || undefined);
                allServices = [...allServices, ...(response.contents || [])];
                if (response.last_page) break;
            }

            // Filter by category using the actual need_focus taxonomy array
            allServices = allServices.filter(service => {
                const needFocus = service.need_focus || [];
                return needFocus.includes(category);
            });
        } else {
            // Normal pagination — let API handle search + pagination
            const response = await getServices(page, 12, query || undefined);
            allServices = response.contents || [];
            totalPages = response.total_pages || 1;
            totalItems = response.total_items || 0;
            services = allServices;
        }

        // For category filtering, handle pagination client-side
        if (category) {
            totalItems = allServices.length;
            totalPages = Math.ceil(totalItems / 12);
            const startIndex = (page - 1) * 12;
            services = allServices.slice(startIndex, startIndex + 12);
        }
    } catch (e) {
        error = e instanceof Error ? e.message : "Failed to load services";
        console.error("Failed to fetch services:", e);
    }

    // Build base URL for pagination
    const buildBaseUrl = () => {
        const params = new URLSearchParams();
        if (query) params.set("q", query);
        if (category) params.set("category", category);
        const paramString = params.toString();
        return paramString ? `/services?${paramString}` : "/services";
    };

    const baseUrl = buildBaseUrl();

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Page Header */}
            <div className="mb-8">
                {categoryDisplayName ? (
                    <>
                        <div className="flex items-center gap-2 mb-2">
                            <Link href="/services" className="text-blue-600 hover:text-blue-700 text-sm">
                                ← All Services
                            </Link>
                        </div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                            {categoryDisplayName}
                        </h1>
                    </>
                ) : (
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                        Browse Services
                    </h1>
                )}
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                    {totalItems.toLocaleString()} services available
                </p>

                {/* Search Bar */}
                <div className="max-w-xl">
                    <SearchBar initialQuery={query} placeholder="Search services..." />
                </div>
            </div>

            {/* Error State */}
            {error && (
                <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 mb-8">
                    <p className="text-red-700 dark:text-red-400">{error}</p>
                </div>
            )}

            {/* Services Grid */}
            {services.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
                    {services.map((service) => (
                        <ServiceCard key={service.id} service={service} />
                    ))}
                </div>
            ) : !error ? (
                <div className="text-center py-16">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-100 dark:bg-gray-800 mb-4">
                        <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                        No services found
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400">
                        {query ? `No results for "${query}"` : categoryDisplayName ? `No services found in ${categoryDisplayName}` : "No services are currently available."}
                    </p>
                </div>
            ) : null}

            {/* Pagination */}
            {totalPages > 1 && (
                <Pagination currentPage={page} totalPages={totalPages} baseUrl={baseUrl} />
            )}
        </div>
    );
}
