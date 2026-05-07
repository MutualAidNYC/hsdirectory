/**
 * Airtable → HSDS field mapper.
 *
 * Ports transform/mapper.py to TypeScript.
 * Pure functions that transform raw JSON data objects into typed HSDS shapes.
 */
import type {
  Phone, Address, Language, Accessibility, Schedule, Contact,
  ServiceArea, Program, Funding, CostOption, RequiredDocument,
  Taxonomy, TaxonomyTerm, Location, OrganizationSummary, Organization,
  ServiceAtLocation, ServiceSummary, Service, Page,
} from "./types";

// ============================================================================
// Utility helpers
// ============================================================================

export function safeFloat(value: unknown): number | undefined {
  if (value == null) return undefined;
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) return undefined;
    const n = Number(trimmed);
    return Number.isNaN(n) ? undefined : n;
  }
  if (typeof value === "number") return value;
  return undefined;
}

export function safeInt(value: unknown): number | undefined {
  if (value == null) return undefined;
  const n = Number(value);
  return Number.isNaN(n) ? undefined : Math.floor(n);
}

export function firstOrNone<T>(list: T[] | undefined | null): T | undefined {
  return list && list.length > 0 ? list[0] : undefined;
}

export function joinList(list: unknown[] | undefined | null): string | undefined {
  if (!list || list.length === 0) return undefined;
  return list.map(String).join(", ");
}

/**
 * Remove undefined/null values from an object (ORUK compliance —
 * optional fields without values should be omitted).
 */
export function stripNulls<T extends Record<string, unknown>>(obj: T): Partial<T> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value !== undefined && value !== null) {
      result[key] = value;
    }
  }
  return result as Partial<T>;
}

// ============================================================================
// Map functions — each mirrors a Python map_* method
// ============================================================================

export function mapPhone(data: Record<string, unknown>): Phone {
  return stripNulls({
    id: (data.id as string) || "",
    number: (data.number as string) || "",
    extension: data.extension as string | undefined,
    type: data.type as string | undefined,
    description: data.description as string | undefined,
  }) as Phone;
}

export function mapAddress(data: Record<string, unknown>): Address {
  let addressType = data.address_type;
  if (Array.isArray(addressType)) addressType = firstOrNone(addressType);

  return stripNulls({
    id: (data.id as string) || "",
    address_1: data.address_1 as string | undefined,
    address_2: data.address_2 as string | undefined,
    city: data.city as string | undefined,
    state_province: data.state_province as string | undefined,
    postal_code: data.postal_code as string | undefined,
    region: data.region as string | undefined,
    country: data.country as string | undefined,
    address_type: addressType as string | undefined,
    attention: data.attention as string | undefined,
  }) as Address;
}

export function mapLanguage(data: Record<string, unknown>): Language {
  return stripNulls({
    id: (data.id as string) || "",
    name: data.name as string | undefined,
    code: data.code as string | undefined,
    note: data.note as string | undefined,
  }) as Language;
}

export function mapAccessibility(data: Record<string, unknown>): Accessibility {
  return stripNulls({
    id: (data.id as string) || "",
    description: data.description as string | undefined,
    details: data.details as string | undefined,
    url: data.url as string | undefined,
  }) as Accessibility;
}

export function mapSchedule(data: Record<string, unknown>): Schedule {
  let byday = data.byday;
  if (Array.isArray(byday)) byday = byday.join(",");

  return stripNulls({
    id: (data.id as string) || "",
    valid_from: data.valid_from as string | undefined,
    valid_to: data.valid_to as string | undefined,
    dtstart: data.dtstart as string | undefined,
    timezone: data.timezone as string | undefined,
    until: data.until as string | undefined,
    count: data.count as string | undefined,
    wkst: data.wkst as string | undefined,
    freq: data.freq as string | undefined,
    interval: data.interval as string | undefined,
    byday: byday as string | undefined,
    byweekno: data.byweekno as string | undefined,
    bymonthday: data.bymonthday as string | undefined,
    byyearday: data.byyearday as string | undefined,
    description: data.description as string | undefined,
    opens_at: data.opens_at as string | undefined,
    closes_at: data.closes_at as string | undefined,
    schedule_link: data.schedule_link as string | undefined,
    attending_type: data.attending_type as string | undefined,
    notes: data.notes as string | undefined,
  }) as Schedule;
}

export function mapContact(
  data: Record<string, unknown>,
  phones?: Phone[],
): Contact {
  return stripNulls({
    id: (data.id as string) || "",
    name: data.name as string | undefined,
    title: data.title as string | undefined,
    department: data.department as string | undefined,
    email: data.email as string | undefined,
    phones: phones && phones.length > 0 ? phones : undefined,
  }) as Contact;
}

export function mapServiceArea(data: Record<string, unknown>): ServiceArea {
  return stripNulls({
    id: (data.id as string) || "",
    name: data.name as string | undefined,
    description: data.description as string | undefined,
    extent: data.extent as string | undefined,
    extent_type: data.extent_type as string | undefined,
    uri: data.uri as string | undefined,
  }) as ServiceArea;
}

export function mapProgram(data: Record<string, unknown>): Program {
  return stripNulls({
    id: (data.id as string) || "",
    name: (data.name as string) || "",
    alternate_name: data.alternate_name as string | undefined,
    description: data.description as string | undefined,
  }) as Program;
}

export function mapFunding(data: Record<string, unknown>): Funding {
  return stripNulls({
    id: (data.id as string) || "",
    source: data.source as string | undefined,
  }) as Funding;
}

export function mapCostOption(data: Record<string, unknown>): CostOption {
  return stripNulls({
    id: (data.id as string) || "",
    option: data.option as string | undefined,
    currency: data.currency as string | undefined,
    amount: safeFloat(data.amount),
    amount_description: data.amount_description as string | undefined,
    valid_from: data.valid_from as string | undefined,
    valid_to: data.valid_to as string | undefined,
  }) as CostOption;
}

export function mapRequiredDocument(data: Record<string, unknown>): RequiredDocument {
  return stripNulls({
    id: (data.id as string) || "",
    document: data.document as string | undefined,
    uri: data.uri as string | undefined,
  }) as RequiredDocument;
}

export function mapTaxonomy(data: Record<string, unknown>): Taxonomy {
  return stripNulls({
    id: (data.id as string) || "",
    name: (data.name as string) || "",
    description: data.description as string | undefined,
    uri: data.uri as string | undefined,
    version: data.version as string | undefined,
  }) as Taxonomy;
}

export function mapTaxonomyTerm(
  data: Record<string, unknown>,
  taxonomy?: Taxonomy,
): TaxonomyTerm {
  return stripNulls({
    id: (data.id as string) || "",
    name: (data.name as string) || "",
    code: data.code as string | undefined,
    description: data.description as string | undefined,
    parent_id: firstOrNone(data.parent as string[] | undefined),
    taxonomy: firstOrNone(data.taxonomy as string[] | undefined),
    taxonomy_detail: taxonomy,
    language: data.language as string | undefined,
    term_uri: data.term_uri as string | undefined,
  }) as TaxonomyTerm;
}

export function mapLocation(
  data: Record<string, unknown>,
  opts?: {
    addresses?: Address[];
    phones?: Phone[];
    contacts?: Contact[];
    accessibility?: Accessibility[];
    languages?: Language[];
    schedules?: Schedule[];
  },
): Location {
  let locationType = data.location_type;
  if (Array.isArray(locationType)) locationType = firstOrNone(locationType);

  return stripNulls({
    id: (data.id as string) || "",
    location_type: locationType as string | undefined,
    url: data.url as string | undefined,
    name: data.name as string | undefined,
    alternate_name: data.alternate_name as string | undefined,
    description: data.description as string | undefined,
    transportation: data.transportation as string | undefined,
    latitude: safeFloat(data.latitude),
    longitude: safeFloat(data.longitude),
    external_identifier: data.external_identifier as string | undefined,
    external_identifier_type: data.external_identifier_type as string | undefined,
    addresses: opts?.addresses && opts.addresses.length > 0 ? opts.addresses : undefined,
    phones: opts?.phones && opts.phones.length > 0 ? opts.phones : undefined,
    contacts: opts?.contacts && opts.contacts.length > 0 ? opts.contacts : undefined,
    accessibility: opts?.accessibility && opts.accessibility.length > 0 ? opts.accessibility : undefined,
    languages: opts?.languages && opts.languages.length > 0 ? opts.languages : undefined,
    schedules: opts?.schedules && opts.schedules.length > 0 ? opts.schedules : undefined,
  }) as Location;
}

export function mapOrganizationSummary(data: Record<string, unknown>): OrganizationSummary {
  return stripNulls({
    id: (data.id as string) || "",
    name: (data.name as string) || "",
    alternate_name: data.alternate_name as string | undefined,
    description: data.description as string | undefined,
    email: data.email as string | undefined,
    website: data.website as string | undefined,
    logo: data.logo as string | undefined,
    uri: data.uri as string | undefined,
  }) as OrganizationSummary;
}

export function mapOrganization(
  data: Record<string, unknown>,
  opts?: {
    phones?: Phone[];
    contacts?: Contact[];
    locations?: Location[];
    programs?: Program[];
    funding?: Funding[];
  },
): Organization {
  return stripNulls({
    id: (data.id as string) || "",
    name: (data.name as string) || "",
    alternate_name: data.alternate_name as string | undefined,
    description: data.description as string | undefined,
    email: data.email as string | undefined,
    website: data.website as string | undefined,
    year_incorporated: safeInt(data.year_incorporated),
    legal_status: data.legal_status as string | undefined,
    logo: data.logo as string | undefined,
    uri: data.uri as string | undefined,
    parent_organization_id: firstOrNone(data.organization as string[] | undefined),
    phones: opts?.phones && opts.phones.length > 0 ? opts.phones : undefined,
    contacts: opts?.contacts && opts.contacts.length > 0 ? opts.contacts : undefined,
    locations: opts?.locations && opts.locations.length > 0 ? opts.locations : undefined,
    programs: opts?.programs && opts.programs.length > 0 ? opts.programs : undefined,
    funding: opts?.funding && opts.funding.length > 0 ? opts.funding : undefined,
  }) as Organization;
}

export function mapServiceAtLocation(
  data: Record<string, unknown>,
  opts?: {
    location?: Location;
    phones?: Phone[];
    contacts?: Contact[];
    schedules?: Schedule[];
    service_areas?: ServiceArea[];
  },
): ServiceAtLocation {
  return stripNulls({
    id: (data.id as string) || "",
    service_id: firstOrNone(data.services as string[] | undefined),
    description: data.description as string | undefined,
    location: opts?.location,
    phones: opts?.phones && opts.phones.length > 0 ? opts.phones : undefined,
    contacts: opts?.contacts && opts.contacts.length > 0 ? opts.contacts : undefined,
    schedules: opts?.schedules && opts.schedules.length > 0 ? opts.schedules : undefined,
    service_areas: opts?.service_areas && opts.service_areas.length > 0 ? opts.service_areas : undefined,
  }) as ServiceAtLocation;
}

export function mapServiceSummary(
  data: Record<string, unknown>,
  organizationId: string,
  organization?: OrganizationSummary,
): ServiceSummary {
  return stripNulls({
    id: (data.id as string) || "",
    organization_id: organizationId,
    name: (data.name as string) || "",
    status: (data.status as string) || "active",
    alternate_name: data.alternate_name as string | undefined,
    description: data.description as string | undefined,
    url: data.url as string | undefined,
    email: data.email as string | undefined,
    last_modified: data.lastUpdated as string | undefined,
    organization,
    need_focus: (data.needFocus as string[]) || [],
    community_focus: (data.communityFocus as string[]) || [],
  }) as ServiceSummary;
}

export function mapService(
  data: Record<string, unknown>,
  organizationId: string,
  opts?: {
    organization?: OrganizationSummary;
    program?: Program;
    phones?: Phone[];
    contacts?: Contact[];
    schedules?: Schedule[];
    service_areas?: ServiceArea[];
    service_at_locations?: ServiceAtLocation[];
    languages?: Language[];
    funding?: Funding[];
    cost_options?: CostOption[];
    required_documents?: RequiredDocument[];
  },
): Service {
  const groupNameList = data.groupName as string[] | undefined;
  const groupName = groupNameList && groupNameList.length > 0 ? groupNameList[0] : undefined;

  return stripNulls({
    id: (data.id as string) || "",
    organization_id: organizationId,
    name: (data.name as string) || "",
    status: (data.status as string) || "active",
    alternate_name: data.alternate_name as string | undefined,
    description: data.description as string | undefined,
    url: data.url as string | undefined,
    email: data.email as string | undefined,
    interpretation_services: data.interpretation_services as string | undefined,
    application_process: data.application_process as string | undefined,
    fees_description: data.fees_description as string | undefined,
    accreditations: data.accreditations as string | undefined,
    eligibility_description: data.eligibility_description as string | undefined,
    minimum_age: safeInt(data.minimum_age),
    maximum_age: safeInt(data.maximum_age),
    assured_date: data.assured_date as string | undefined,
    assurer_email: data.assurer_email as string | undefined,
    alert: data.alert as string | undefined,
    last_modified: data.lastUpdated as string | undefined,
    organization: opts?.organization,
    program: opts?.program,
    phones: opts?.phones && opts.phones.length > 0 ? opts.phones : undefined,
    contacts: opts?.contacts && opts.contacts.length > 0 ? opts.contacts : undefined,
    schedules: opts?.schedules && opts.schedules.length > 0 ? opts.schedules : undefined,
    service_areas: opts?.service_areas && opts.service_areas.length > 0 ? opts.service_areas : undefined,
    service_at_locations: opts?.service_at_locations && opts.service_at_locations.length > 0 ? opts.service_at_locations : undefined,
    languages: opts?.languages && opts.languages.length > 0 ? opts.languages : undefined,
    funding: opts?.funding && opts.funding.length > 0 ? opts.funding : undefined,
    cost_options: opts?.cost_options && opts.cost_options.length > 0 ? opts.cost_options : undefined,
    required_documents: opts?.required_documents && opts.required_documents.length > 0 ? opts.required_documents : undefined,
    group_name: groupName,
    need_focus: data.needFocus as string[] | undefined,
    community_focus: data.communityFocus as string[] | undefined,
  }) as Service;
}

// ============================================================================
// Pagination helper
// ============================================================================

/**
 * Create a paginated Page response from total count and current page items.
 */
export function paginate<T>(
  items: T[],
  totalItems: number,
  page: number,
  perPage: number,
): Page<T> {
  const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
  return {
    total_items: totalItems,
    total_pages: totalPages,
    page_number: page,
    size: items.length,
    first_page: page === 1,
    last_page: page >= totalPages,
    empty: items.length === 0,
    contents: items,
  };
}
