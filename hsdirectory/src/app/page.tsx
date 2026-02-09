import Link from "next/link";
import { SearchBar } from "@/components/ui/SearchBar";
import { getServices, getOrganizations, getMapServices } from "@/lib/api";

/**
 * Map taxonomy term names to display icons.
 * Falls back to a generic icon for unmapped terms.
 */
const CATEGORY_ICONS: Record<string, string> = {
  "Food": "🍎",
  "Housing": "🏠",
  "Legal": "⚖️",
  "Medical": "🏥",
  "Education": "📚",
  "Jobs": "💼",
  "Money": "💰",
  "Mental & Behavioral Health": "🧠",
  "Safety from Violence": "🛡️",
  "Clothing": "👕",
  "Social Service Guidance": "🤝",
  "Childcare and Pregnancy": "👶",
  "Eldercare": "👵",
  "Exercise and Wellness": "🏃",
  "Fun and Leisure": "🎭",
  "Internet and Technology": "💻",
  "Petcare": "🐾",
  "Delivery/Transport": "🚗",
  "Disaster Response": "🚨",
  "Mutual Aid Organizing": "✊",
  "Personal Protective Equipment": "😷",
  "Socializing": "💬",
  "Additional Resource Libraries": "📖",
};

/**
 * Rotating color palette for category cards.
 */
const COLOR_PALETTE = [
  "bg-green-100 dark:bg-green-900/30",
  "bg-blue-100 dark:bg-blue-900/30",
  "bg-purple-100 dark:bg-purple-900/30",
  "bg-red-100 dark:bg-red-900/30",
  "bg-yellow-100 dark:bg-yellow-900/30",
  "bg-indigo-100 dark:bg-indigo-900/30",
  "bg-emerald-100 dark:bg-emerald-900/30",
  "bg-teal-100 dark:bg-teal-900/30",
  "bg-orange-100 dark:bg-orange-900/30",
  "bg-pink-100 dark:bg-pink-900/30",
  "bg-cyan-100 dark:bg-cyan-900/30",
  "bg-amber-100 dark:bg-amber-900/30",
];

/** Terms to exclude from the homepage grid. */
const EXCLUDED_TERMS = new Set(["-Not Listed", "Not Listed"]);

/**
 * Homepage with hero search and dynamically populated service categories
 * derived from taxonomy terms that have at least one connected service.
 */
export default async function Home() {
  let stats = { services: 0, organizations: 0 };
  let categories: string[] = [];

  try {
    const [servicesRes, orgsRes, mapData] = await Promise.all([
      getServices(1, 1),
      getOrganizations(1, 1),
      getMapServices(),
    ]);
    stats = {
      services: servicesRes.total_items || 0,
      organizations: orgsRes.total_items || 0,
    };
    categories = (mapData.needCategories || []).filter(
      (c: string) => !EXCLUDED_TERMS.has(c)
    );
  } catch (error) {
    console.error("Failed to fetch homepage data:", error);
  }

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 py-24 px-4">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
        <div className="container mx-auto relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
              Find Community Services &amp; Resources
            </h1>
            <p className="text-xl text-blue-100 mb-10">
              Search our directory of {stats.services.toLocaleString()} services
              from {stats.organizations.toLocaleString()} organizations
            </p>
            <SearchBar placeholder="What service are you looking for?" />
          </div>
        </div>
      </section>

      {/* Quick Links */}
      <section className="py-12 px-4 bg-gray-50 dark:bg-gray-900">
        <div className="container mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link
              href="/services"
              className="group flex items-center gap-4 p-6 rounded-xl bg-white dark:bg-gray-800 
                border border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600">
                  Browse Services
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Explore all available services
                </p>
              </div>
            </Link>

            <Link
              href="/organizations"
              className="group flex items-center gap-4 p-6 rounded-xl bg-white dark:bg-gray-800 
                border border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600">
                  Organizations
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  View service providers
                </p>
              </div>
            </Link>

            <Link
              href="/services"
              className="group flex items-center gap-4 p-6 rounded-xl bg-white dark:bg-gray-800 
                border border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:shadow-md transition-all"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600">
                  Map View
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Find services near you
                </p>
              </div>
            </Link>
          </div>
        </div>
      </section>

      {/* Service Categories — dynamically populated from taxonomy terms */}
      {categories.length > 0 && (
        <section className="py-16 px-4">
          <div className="container mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Browse by Category
              </h2>
              <Link
                href="/services"
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 font-medium"
              >
                View all services →
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {categories.map((category, index) => (
                <Link
                  key={category}
                  href={`/services?category=${encodeURIComponent(category)}`}
                  className="group flex flex-col items-center p-6 rounded-xl bg-white dark:bg-gray-800 
                    border border-gray-200 dark:border-gray-700 hover:border-blue-300 hover:shadow-md transition-all"
                >
                  <span className={`text-3xl mb-3 flex items-center justify-center w-12 h-12 rounded-full ${COLOR_PALETTE[index % COLOR_PALETTE.length]}`}>
                    {CATEGORY_ICONS[category] || "📋"}
                  </span>
                  <span className="text-sm font-medium text-center text-gray-900 dark:text-white group-hover:text-blue-600">
                    {category}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
