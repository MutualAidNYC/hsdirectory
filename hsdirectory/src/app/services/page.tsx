import { Metadata } from "next";
import { getMapServices } from "@/lib/api";
import MapPageClient from "./MapPageClient";

export const metadata: Metadata = {
    title: "Services",
    description: "Find community services and resources on an interactive map.",
};

/**
 * Services page — interactive map with filters, search, and proximity sorting.
 */
export default async function ServicesPage() {
    let services: any[] = [];
    let needCategories: string[] = [];
    let communityCategories: string[] = [];
    let error = null;

    try {
        const data = await getMapServices();
        services = data.services;
        needCategories = data.needCategories;
        communityCategories = data.communityCategories;
    } catch (e) {
        error = e instanceof Error ? e.message : "Failed to load services";
        console.error("Failed to fetch services:", e);
    }

    if (error) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4">
                    <p className="text-red-700 dark:text-red-400">{error}</p>
                </div>
            </div>
        );
    }

    return (
        <MapPageClient
            services={services}
            needCategories={needCategories}
            communityCategories={communityCategories}
        />
    );
}
