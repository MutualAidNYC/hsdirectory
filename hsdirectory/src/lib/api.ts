/**
 * HSDS API Client
 * 
 * Provides typed access to the ATtoOR HSDS 3.0 API endpoints.
 * All methods handle pagination and error states.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

/**
 * HSDS Service type based on HSDS 3.0 specification
 */
export interface Service {
    id: string;
    name: string;
    description?: string;
    url?: string;
    email?: string;
    status?: string;
    organization_id?: string;
    organization?: Organization;
    service_at_locations?: ServiceAtLocation[];
    // Custom extension fields
    group_name?: string;
    need_focus?: string[];
    community_focus?: string[];
}

/**
 * HSDS Organization type
 */
export interface Organization {
    id: string;
    name: string;
    description?: string;
    url?: string;
    email?: string;
    logo?: string;
    service_count?: number;
    locations?: Location[];
}

/**
 * HSDS Location type
 */
export interface Location {
    id: string;
    name?: string;
    description?: string;
    latitude?: number;
    longitude?: number;
    addresses?: Address[];
}

/**
 * HSDS Address type
 */
export interface Address {
    id: string;
    address_1?: string;
    address_2?: string;
    city?: string;
    state_province?: string;
    postal_code?: string;
    country?: string;
}

/**
 * HSDS ServiceAtLocation linking type
 */
export interface ServiceAtLocation {
    id: string;
    service_id: string;
    location_id: string;
    location?: Location;
}

/**
 * HSDS Taxonomy Term type
 */
export interface TaxonomyTerm {
    id: string;
    name: string;
    description?: string;
    taxonomy_id?: string;
}

/**
 * Paginated response wrapper matching HSDS 3.0 format
 */
export interface PaginatedResponse<T> {
    total_items: number;
    total_pages: number;
    page_number: number;
    size: number;
    first_page: boolean;
    last_page: boolean;
    empty: boolean;
    contents: T[];
}

/**
 * API error type for consistent error handling
 */
export class ApiError extends Error {
    constructor(public status: number, message: string) {
        super(message);
        this.name = 'ApiError';
    }
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
        headers: {
            'Accept': 'application/json',
        },
        next: { revalidate: 60 }, // Cache for 60 seconds
    });

    if (!response.ok) {
        throw new ApiError(response.status, `API error: ${response.statusText}`);
    }

    return response.json();
}

/**
 * Fetch paginated list of services, optionally filtered by search query.
 */
export async function getServices(page: number = 1, size: number = 20, search?: string): Promise<PaginatedResponse<Service>> {
    let url = `/services?page=${page}&per_page=${size}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    return fetchApi<PaginatedResponse<Service>>(url);
}

/**
 * Fetch a single service by ID with full details
 */
export async function getService(id: string): Promise<Service> {
    return fetchApi<Service>(`/services/${id}`);
}

/**
 * Fetch paginated list of organizations
 */
export async function getOrganizations(page: number = 1, size: number = 20): Promise<PaginatedResponse<Organization>> {
    return fetchApi<PaginatedResponse<Organization>>(`/organizations?page=${page}&per_page=${size}`);
}

/**
 * Search organizations by name. Returns the first match or null.
 * Used to resolve group names to org profile links.
 */
export async function searchOrganizationByName(name: string): Promise<Organization | null> {
    try {
        const result = await fetchApi<PaginatedResponse<Organization>>(
            `/organizations?search=${encodeURIComponent(name)}&per_page=1`
        );
        return result.contents?.[0] ?? null;
    } catch {
        return null;
    }
}

/**
 * Fetch a single organization by ID
 */
export async function getOrganization(id: string): Promise<Organization> {
    return fetchApi<Organization>(`/organizations/${id}`);
}

/**
 * Fetch services for a specific organization
 */
export async function getOrganizationServices(
    organizationId: string,
    page: number = 1,
    size: number = 100
): Promise<PaginatedResponse<Service>> {
    return fetchApi<PaginatedResponse<Service>>(`/organizations/${organizationId}/services?page=${page}&per_page=${size}`);
}

/**
 * Fetch taxonomy terms for filtering
 */
export async function getTaxonomyTerms(): Promise<PaginatedResponse<TaxonomyTerm>> {
    return fetchApi<PaginatedResponse<TaxonomyTerm>>('/taxonomy_terms?per_page=100');
}

/**
 * Fetch service at locations for map display
 */
export async function getServiceAtLocations(page: number = 1, size: number = 100): Promise<PaginatedResponse<ServiceAtLocation>> {
    return fetchApi<PaginatedResponse<ServiceAtLocation>>(`/service_at_locations?page=${page}&per_page=${size}`);
}

/**
 * Search services by query string
 * Note: Uses basic filtering - for advanced search, consider adding Meilisearch
 */
export async function searchServices(query: string, page: number = 1): Promise<PaginatedResponse<Service>> {
    // Currently uses basic endpoint - backend would need search param support
    // For MVP, we fetch all and filter client-side, or implement server search
    return getServices(page, 20);
}

/**
 * Geocoded location for map display
 */
export interface GeocodedLocation {
    id: string;
    name?: string;
    address?: string;
    latitude: number;
    longitude: number;
    service_id?: string;
    service_name?: string;
    organization_id?: string;
    organization_name?: string;
}

/**
 * Response from geocoded locations endpoint
 */
export interface GeocodedLocationsResponse {
    total: number;
    locations: GeocodedLocation[];
}

/**
 * Fetch geocoded locations for map display
 */
export async function getGeocodedLocations(limit: number = 500): Promise<GeocodedLocationsResponse> {
    return fetchApi<GeocodedLocationsResponse>(`/locations/geocoded?limit=${limit}`);
}

/**
 * Service data for map display
 */
export interface MapService {
    id: string;
    name: string;
    description?: string;
    address?: string;
    phone?: string;
    url?: string;
    needFocus: string[];
    communityFocus: string[];
    latitude?: number;
    longitude?: number;
}

/**
 * Map data response with services and filter options
 */
export interface MapDataResponse {
    services: MapService[];
    needCategories: string[];
    communityCategories: string[];
}

/**
 * Fetch services data for map page with filter categories
 */
export async function getMapServices(): Promise<MapDataResponse> {
    return fetchApi<MapDataResponse>('/map/services');
}

