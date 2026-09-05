/**
 * Serves API responses from the committed snapshot instead of a live backend,
 * so the dev site works on Vercel with no hosted API.
 *
 * Scaffolding with an expiry. To remove: delete this file, src/data/snapshot.json,
 * scripts/dump-snapshot.mjs, and the USE_SNAPSHOT branch in api.ts.
 */
import snapshotJson from "@/data/snapshot.json";

interface Named {
    name?: string;
    description?: string;
}

/** Typed explicitly rather than inferred, so regenerating the JSON can't change the types. */
interface SnapshotData {
    generatedAt: string;
    source: string;
    mapServices: unknown;
    services: Named[];
    serviceDetail: Record<string, unknown>;
    organizations: Named[];
    organizationDetail: Record<string, unknown>;
    organizationServices: Record<string, unknown[]>;
}

const data = snapshotJson as unknown as SnapshotData;

interface Page<T> {
    total_items: number;
    total_pages: number;
    page_number: number;
    size: number;
    first_page: boolean;
    last_page: boolean;
    empty: boolean;
    contents: T[];
}

function paginate<T>(items: T[], page: number, perPage: number): Page<T> {
    const totalPages = Math.max(1, Math.ceil(items.length / perPage));
    const start = (page - 1) * perPage;
    const contents = items.slice(start, start + perPage);
    return {
        total_items: items.length,
        total_pages: totalPages,
        page_number: page,
        size: contents.length,
        first_page: page === 1,
        last_page: page >= totalPages,
        empty: contents.length === 0,
        contents,
    };
}

/** Mirrors the backend's search: substring over name and description. */
function search<T extends Named>(items: T[], term: string): T[] {
    const q = term.toLowerCase();
    return items.filter(
        (i) =>
            (i.name ?? "").toLowerCase().includes(q) ||
            (i.description ?? "").toLowerCase().includes(q)
    );
}

export class SnapshotMiss extends Error {}

export function resolveFromSnapshot<T>(endpoint: string): T {
    const [path, qs] = endpoint.split("?");
    const params = new URLSearchParams(qs ?? "");
    const page = Number(params.get("page") ?? 1);
    const perPage = Number(params.get("per_page") ?? 20);
    const term = params.get("search");

    if (path === "/map/services") return data.mapServices as T;

    if (path === "/services") {
        return paginate(term ? search(data.services, term) : data.services, page, perPage) as T;
    }

    if (path === "/organizations") {
        return paginate(term ? search(data.organizations, term) : data.organizations, page, perPage) as T;
    }

    const orgServices = path.match(/^\/organizations\/([^/]+)\/services$/);
    if (orgServices) {
        return paginate(data.organizationServices[orgServices[1]] ?? [], page, perPage) as T;
    }

    const service = path.match(/^\/services\/([^/]+)$/);
    if (service) {
        const found = data.serviceDetail[service[1]];
        if (!found) throw new SnapshotMiss(`no snapshot entry for ${path}`);
        return found as T;
    }

    const org = path.match(/^\/organizations\/([^/]+)$/);
    if (org) {
        const found = data.organizationDetail[org[1]];
        if (!found) throw new SnapshotMiss(`no snapshot entry for ${path}`);
        return found as T;
    }

    throw new SnapshotMiss(`no snapshot route for ${path}`);
}
