import Link from "next/link";
import { SearchBar } from "@/components/ui/SearchBar";
import { getServices, getOrganizations, getMapServices } from "@/lib/api";


/** Terms to exclude from the homepage grid. */
const EXCLUDED_TERMS = new Set(["-Not Listed", "Not Listed"]);

/**
 * Homepage based on mutualaid.nyc.
 */
export default async function Home() {
  let stats = { resources: 0, groups: 0 };
  let categories: { name: string; icon?: string | null }[] = [];

  try {
    const [servicesRes, orgsRes, mapData] = await Promise.all([
      getServices(1, 1),
      getOrganizations(1, 1),
      getMapServices(),
    ]);
    stats = {
      resources: servicesRes.total_items || 0,
      groups: orgsRes.total_items || 0,
    };
    categories = (mapData.needCategories || [])
    .filter((c: any) => !EXCLUDED_TERMS.has(c.name));
  } catch (error) {
    console.error("Failed to fetch homepage data:", error);
  }

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="pt-10 pb-12 md:py-30 px-4 bg-[var(--background)]">
        <div className="container mx-auto">
          <div className="max-w-5xl mx-auto text-center">
            <h1 className="font-black text-4xl md:text-6xl text-[var(--secondary)] mb-6">
              Community Resources Library
            </h1>
          </div>
          <div className="max-w-3xl mb-10 mx-auto">
            <p className="text-2xl font-bold text-[var(--primary)] mb-4">
              Our community-sourced, volunteer-curated library is a collection of the many resources available to New Yorkers.
            </p>
          </div>
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-xl mb-5">
              Search our directory of {stats.resources.toLocaleString()} resources
              from {stats.groups.toLocaleString()} groups
            </p>
          </div>
          <div className="flex justify-center">
            <SearchBar placeholder="Search resources..." />
          </div>
          <div className="flex justify-center gap-4 mt-10">
            <a href="https://mutualaid.nyc/submit-a-resource/" className="btn btn-primary">
              Submit a resource
            </a>
            <a href="https://mutualaid.nyc/suggest-a-change/" className="btn btn-primary">
              Suggest a change
            </a>
          </div>
        </div>
      </section>

      {/* Resource Categories  */}
      {categories.length > 0 && (
        <section className="pt-10 pb-16 px-4 bg-[var(--section-alt)]">
          <div className="container mx-auto">
            <div className="flex items-center justify-between mb-8">
              <h2 className="font-display text-2xl font-bold text-[var(--foreground)]">
                Browse By Category
              </h2>
              <Link
                href="/services"
                className="text-[var(--primary)] hover:text-[var(--primary-hover)] font-medium transition-colors underline hover:no-underline"
              >
                View all resources →
              </Link>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {categories.map((category) => {
                return (
                  <Link
                    key={category.name}
                    href={`/services?category=${encodeURIComponent(category.name)}`}
                    className="group flex items-center gap-3 p-5 rounded-2xl bg-card-bg border border-[var(--card-border)] hover:shadow-md transition-all"
                  >
                    <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center">
                      {category.icon ? (
                        <img
                          src={category.icon}
                          alt=""
                          className="w-full h-full object-contain"
                          loading="lazy"
                        />
                      ) : (
                        <span className="w-6 h-6 rounded-full bg-black/10 block" />
                      )}
                    </span>
                    <span className="text-sm font-semibold text-foreground">
                      {category.name}
                    </span>
                  </Link>
                );
              })}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
