

from pydantic import BaseModel


class OrganizationResponse(BaseModel):
    id: str
    name: str
    alternate_name: str | None = None
    description: str | None = None
    email: str | None = None
    website: str | None = None
    year_incorporated: int | None = None
    legal_status: str | None = None
    logo: str | None = None
    uri: str | None = None
    parent_organization_id: str | None = None
    phones: list[str] | None = None
    contacts: list[str] | None = None
    locations: list[str] | None = None
    programs: list[str] | None = None
    funding: list[str] | None = None
    organization_identifiers: list[str] | None = None


class ServiceResponse(BaseModel):
    """Full service details - ORUK compliant with required fields."""
    id: str
    name: str
    organizations: list[str] | None = None
    status: str = "active"  # Required by ORUK
    alternate_name: str | None = None
    description: str | None = None
    url: str | None = None
    email: str | None = None
    interpretation_services: str | None = None
    application_process: str | None = None
    fees_description: str | None = None
    accreditations: str | None = None
    eligibility_description: str | None = None
    minimum_age: int | None = None
    maximum_age: int | None = None
    assured_date: str | None = None
    assurer_email: str | None = None
    alert: str | None = None
    last_modified: str | None = None
    
    # Related objects
    organization: str | None = None
    phones: list[str] | None = None
    contacts: list[str] | None = None
    schedules: list[str] | None = None
    service_areas: list[str] | None = None
    service_at_locations: list[str] | None = None
    languages: list[str] | None = None
    funding: list[str] | None = None
    cost_options: list[str] | None = None
    required_documents: list[str] | None = None
    
    # Custom extension fields (non-HSDS standard)
    group_name: str | None = None  # Organization/group name from Airtable
    need_focus: list[str] | None = None  # Need categories
    community_focus: list[str] | None = None  # Target communities


class ServiceAtLocationResponse(BaseModel):
    id: str
    service_id: str | None = None
    locations: list[str] | None = None
    phones: list[str] | None = None
    contacts: list[str] | None = None
    schedules: list[str] | None = None


class LocationResponse(BaseModel):
    id: str
    location_type: str | None = None
    url: str | None = None
    name: str | None = None
    alternate_name: str | None = None
    description: str | None = None
    transportation: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    external_identifier: str | None = None
    external_identifier_type: str | None = None
    addresses: list[str] | None = None
    accessibility: list[str] | None = None

class AddressResponse(BaseModel):
    """Address details."""
    id: str
    address_1: str | None = None
    address_2: str | None = None
    city: str | None = None
    state_province: str | None = None
    postal_code: str | None = None
    region: str | None = None
    country: str | None = None
    address_type: str | None = None
    attention: str | None = None


class AccessibilityResponse(BaseModel):
    """Accessibility details."""
    id: str
    description: str | None = None
    details: str | None = None
    url: str | None = None

class ContactResponse(BaseModel):
    """Contact person details."""
    id: str
    name: str | None = None
    title: str | None = None
    department: str | None = None
    email: str | None = None


class PhoneResponse(BaseModel):
    """Phone number details."""
    id: str
    number: str
    extension: str | None = None
    type: str | None = None
    description: str | None = None

class ScheduleResponse(BaseModel):
    """Schedule information using RFC 5545 RRULE format."""
    id: str
    valid_from: str | None = None
    valid_to: str | None = None
    dtstart: str | None = None
    timezone: str | None = None
    until: str | None = None
    count: str | None = None
    wkst: str | None = None
    freq: str | None = None
    interval: str | None = None
    byday: str | None = None
    byweekno: str | None = None
    bymonthday: str | None = None
    byyearday: str | None = None
    description: str | None = None
    opens_at: str | None = None
    closes_at: str | None = None
    schedule_link: str | None = None
    attending_type: str | None = None
    notes: str | None = None

