import { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getService, getMapServices, searchOrganizationByName } from "@/lib/api";
import ServiceLocationMap from "./ServiceLocationMap";

interface ServiceDetailPageProps {
    params: Promise<{ id: string }>;
}

/**
 * Generate dynamic metadata for service detail page.
 */
export async function generateMetadata({ params }: ServiceDetailPageProps): Promise<Metadata> {
    const { id } = await params;
    try {
        const service = await getService(id);
        return {
            title: service.name,
            description: service.description || `Details about ${service.name}`,
        };
    } catch {
        return {
            title: "Service Not Found",
        };
    }
}

/**
 * Service detail page showing full service information.
 *
 * Coordinates are resolved from two sources:
 * 1. HSDS service_at_locations (if the service has linked locations with coords)
 * 2. Geocoded map data (/map/services) as a fallback
 */
export default async function ServiceDetailPage({ params }: ServiceDetailPageProps) {
    const { id } = await params;

    let service;
    try {
        service = await getService(id);
    } catch (error) {
        console.error("Failed to fetch service:", error);
        notFound();
    }

    // Resolve map coordinates from HSDS locations or geocoded map data.
    let mapCoords: { latitude: number; longitude: number; name: string; address?: string } | null = null;

    // Source 1: HSDS service_at_locations
    if (service.service_at_locations?.length > 0) {
        const locWithCoords = service.service_at_locations.find(
            (sal: any) => sal.location?.latitude && sal.location?.longitude
        );
        if (locWithCoords?.location) {
            const addr = locWithCoords.location.addresses?.[0];
            mapCoords = {
                latitude: locWithCoords.location.latitude,
                longitude: locWithCoords.location.longitude,
                name: locWithCoords.location.name || service.name,
                address: addr
                    ? [addr.address_1, addr.city, addr.state_province, addr.postal_code]
                        .filter(Boolean)
                        .join(", ")
                    : undefined,
            };
        }
    }

    // Source 2: Geocoded map data (resolves Airtable location links)
    if (!mapCoords) {
        try {
            const mapData = await getMapServices();
            const mapService = mapData.services.find((s: any) => s.id === id);
            if (mapService?.latitude && mapService?.longitude) {
                mapCoords = {
                    latitude: mapService.latitude,
                    longitude: mapService.longitude,
                    name: service.name,
                    address: mapService.address || undefined,
                };
            }
        } catch {
            // Non-critical — page still renders without the map
        }
    }

    // Resolve organization ID from group name for profile linking.
    // Services often have organization_id=null but a groupName lookup field.
    let resolvedOrgId: string | null = null;
    const orgId = service.organization_id;
    if (orgId && orgId !== 'unknown' && orgId !== 'None') {
        resolvedOrgId = orgId;
    } else if (service.group_name) {
        try {
            const org = await searchOrganizationByName(service.group_name);
            if (org?.id) resolvedOrgId = org.id;
        } catch {
            // Non-critical
        }
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Breadcrumb */}
            <nav className="mb-6 text-sm">
                <ol className="flex items-center gap-2 text-gray-500 dark:text-gray-400">
                    <li>
                        <Link href="/" className="hover:text-gray-700 dark:hover:text-gray-300">
                            Home
                        </Link>
                    </li>
                    <li>/</li>
                    <li>
                        <Link href="/services" className="hover:text-gray-700 dark:hover:text-gray-300">
                            Services
                        </Link>
                    </li>
                    <li>/</li>
                    <li className="text-gray-900 dark:text-white font-medium truncate">
                        {service.name}
                    </li>
                </ol>
            </nav>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Header */}
                    <div>
                        <div className="flex items-start justify-between gap-4 mb-4">
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                {service.name}
                            </h1>
                            {service.status && (
                                <span className={`shrink-0 rounded-full px-3 py-1 text-sm font-medium
                  ${service.status === 'active' || service.status === 'Published'
                                        ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                        : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                                    }`}
                                >
                                    {service.status === 'Published' ? 'Active' : service.status}
                                </span>
                            )}
                        </div>

                        {/* Group/Organization Name - linked to org profile */}
                        {(service.group_name || service.organization) && (
                            <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">
                                <span className="font-medium">Group:</span>{' '}
                                {resolvedOrgId ? (
                                    <Link
                                        href={`/organizations/${resolvedOrgId}`}
                                        className="text-blue-600 hover:text-blue-700 dark:text-blue-400 hover:underline"
                                    >
                                        {service.group_name || service.organization?.name}
                                    </Link>
                                ) : (
                                    <span>{service.group_name || service.organization?.name}</span>
                                )}
                            </p>
                        )}

                        {/* Service Categories */}
                        {service.need_focus?.length > 0 && (
                            <div className="mb-4">
                                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
                                    Service Categories
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {service.need_focus.map((need: string, index: number) => (
                                        <Link
                                            key={`need-${index}`}
                                            href={`/services?category=${encodeURIComponent(need)}`}
                                            className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                                        >
                                            {need}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Community Focus */}
                        {service.community_focus?.length > 0 && (
                            <div className="mb-4">
                                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 uppercase tracking-wide">
                                    Community Focus
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {service.community_focus.map((community: string, index: number) => (
                                        <Link
                                            key={`community-${index}`}
                                            href={`/services?community=${encodeURIComponent(community)}`}
                                            className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors"
                                        >
                                            {community}
                                        </Link>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Description */}
                    {service.description && (
                        <section>
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                                About This Service
                            </h2>
                            <div className="prose dark:prose-invert max-w-none">
                                <p className="text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                                    {service.description}
                                </p>
                            </div>
                        </section>
                    )}

                    {/* Locations */}
                    {service.service_at_locations?.length > 0 && (
                        <section>
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                                Locations
                            </h2>
                            <div className="space-y-4">
                                {service.service_at_locations.map((sal: any) => (
                                    <div
                                        key={sal.id}
                                        className="rounded-lg border border-gray-200 dark:border-gray-700 p-4"
                                    >
                                        {sal.location && (
                                            <>
                                                {sal.location.name && (
                                                    <h3 className="font-medium text-gray-900 dark:text-white mb-2">
                                                        {sal.location.name}
                                                    </h3>
                                                )}
                                                {sal.location.addresses?.length > 0 && (
                                                    <div className="text-gray-600 dark:text-gray-300">
                                                        {sal.location.addresses.map((addr: any) => (
                                                            <p key={addr.id}>
                                                                {[addr.address_1, addr.address_2, addr.city, addr.state_province, addr.postal_code]
                                                                    .filter(Boolean)
                                                                    .join(", ")}
                                                            </p>
                                                        ))}
                                                    </div>
                                                )}
                                            </>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}
                </div>

                {/* Sidebar */}
                <div className="lg:col-span-1">
                    <div className="sticky top-24 space-y-6">
                        {/* Map Card - show if service has geocoded coordinates */}
                        {mapCoords && (
                            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
                                <ServiceLocationMap
                                    latitude={mapCoords.latitude}
                                    longitude={mapCoords.longitude}
                                    name={mapCoords.name}
                                />
                                {mapCoords.address && (
                                    <div className="p-4 border-t border-gray-200 dark:border-gray-700">
                                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                                            {mapCoords.address}
                                        </p>
                                        <a
                                            href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(mapCoords.address)}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                                        >
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                                            </svg>
                                            Get Directions
                                        </a>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Contact Card */}
                        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
                            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">
                                Contact Information
                            </h3>

                            <div className="space-y-4">
                                {service.url && (
                                    <a
                                        href={service.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-3 text-blue-600 hover:text-blue-700 dark:text-blue-400"
                                    >
                                        <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                                        </svg>
                                        <span className="truncate">Visit Website</span>
                                    </a>
                                )}

                                {service.email && (
                                    <a
                                        href={`mailto:${service.email}`}
                                        className="flex items-center gap-3 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
                                    >
                                        <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                        </svg>
                                        <span className="truncate">{service.email}</span>
                                    </a>
                                )}

                                {!service.url && !service.email && (
                                    <p className="text-gray-500 dark:text-gray-400 text-sm">
                                        No contact information available.
                                    </p>
                                )}
                            </div>
                        </div>

                        {/* Back Button */}
                        <Link
                            href="/services"
                            className="flex items-center justify-center gap-2 w-full py-3 px-4 rounded-lg 
                border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300
                hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                        >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                            </svg>
                            Back to Map
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    );
}
