"""
Organizations API endpoints.

OPTIONAL endpoints per HSDS specification.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from models.hsds import Organization, Page
from airtable.client import get_airtable_client
from transform.mapper import HSDSMapper
from config import get_settings

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=Page)
async def list_organizations(
    search: Optional[str] = Query(None, description="Full text search"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    taxonomy_term_id: Optional[str] = Query(None, description="Filter by taxonomy term"),
    taxonomy_id: Optional[str] = Query(None, description="Filter by taxonomy"),
    full_service: bool = Query(False, description="Include full service info"),
    full: bool = Query(False, description="Return fully nested organizations"),
):
    """
    List organizations with pagination and filtering.

    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    settings = get_settings()

    # Fetch organizations from Airtable
    records = await client.list_records("organizations")

    # Get published services to: 1) filter orgs, 2) count services per org
    org_service_counts = {}
    orgs_with_published_services = set()

    if settings.published_status_value:
        filter_formula = f"{{status}}='{settings.published_status_value}'"
        published_services = await client.list_records("services", filter_formula=filter_formula)

        # Count services per organization (using 'organizations' field - it's plural in Airtable)
        for svc in published_services:
            org_ids = svc.get("fields", {}).get("organizations", [])
            for org_id in org_ids:
                orgs_with_published_services.add(org_id)
                org_service_counts[org_id] = org_service_counts.get(org_id, 0) + 1

    # Apply search filter locally
    if search:
        search_lower = search.lower()
        records = [
            r for r in records
            if search_lower in (r.get("fields", {}).get("name", "") or "").lower()
            or search_lower in (r.get("fields", {}).get("description", "") or "").lower()
        ]

    # Map to HSDS models
    organizations = []
    for record in records:
        fields = record.get("fields", {})
        airtable_id = record["id"]

        # Skip if org has no published services (when filtering enabled)
        if settings.filter_orgs_without_published_services and settings.published_status_value:
            if airtable_id not in orgs_with_published_services:
                continue

        if full:
            org = await _get_full_organization(airtable_id, fields, mapper, client)
            org_dict = org.model_dump()
        else:
            # Return organization summary
            summary = mapper.map_organization_summary(fields)
            org_dict = summary.model_dump()

        # Add service count to response
        org_dict["service_count"] = org_service_counts.get(airtable_id, 0)
        organizations.append(org_dict)

    # Sort by name (case-insensitive)
    organizations.sort(key=lambda x: (x.get("name") or "").lower())

    return mapper.paginate(organizations, page, per_page)


@router.get("/{organization_id}/services", response_model=Page)
async def get_organization_services(
    organization_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """
    Get services for a specific organization.

    Returns services that are linked to this organization via Airtable's 'organizations' field.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    settings = get_settings()

    # Get published services
    filter_formula = None
    if settings.published_status_value:
        filter_formula = f"{{status}}='{settings.published_status_value}'"

    all_services = await client.list_records("services", filter_formula=filter_formula)

    # Filter to services that have this org in their organizations list
    matching_services = []
    for svc in all_services:
        fields = svc.get("fields", {})
        org_ids = fields.get("organizations", [])
        if organization_id in org_ids:
            # Map to service summary
            summary = mapper.map_service_summary(
                fields,
                organization_id=organization_id,
            )
            matching_services.append(summary.model_dump())

    return mapper.paginate(matching_services, page, per_page)


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: str,
    full_service: bool = Query(False, description="Include full service info"),
):
    """
    Get a single organization with all related data.

    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()

    # Search for organization by HSDS ID or Airtable ID
    records = await client.list_records(
        "organizations",
        filter_formula=f"OR({{id}}='{organization_id}', RECORD_ID()='{organization_id}')"
    )

    if not records:
        raise HTTPException(status_code=404, detail="Organization not found")

    record = records[0]
    fields = record.get("fields", {})
    airtable_id = record["id"]

    # Note: We don't filter orgs on the detail page - if org exists, show it
    # The list page already filters to only orgs with published services

    return await _get_full_organization(airtable_id, fields, mapper, client)


async def _get_full_organization(
    airtable_id: str,
    fields: dict,
    mapper: HSDSMapper,
    client
) -> Organization:
    """Helper to build a fully nested organization."""

    # Fetch phones
    phones = []
    phone_ids = fields.get("phones", [])
    if phone_ids:
        phone_records = await client.get_linked_records("phones", phone_ids)
        phones = [mapper.map_phone(r.get("fields", {})) for r in phone_records]

    # Fetch contacts
    contacts = []
    contact_ids = fields.get("contacts", [])
    if contact_ids:
        contact_records = await client.get_linked_records("contacts", contact_ids)
        contacts = [mapper.map_contact(r.get("fields", {})) for r in contact_records]

    # Fetch locations
    locations = []
    location_ids = fields.get("locations", [])
    if location_ids:
        location_records = await client.get_linked_records("locations", location_ids)
        for loc_record in location_records:
            loc_fields = loc_record.get("fields", {})

            # Fetch addresses for location
            addresses = []
            addr_ids = loc_fields.get("addresses", [])
            if addr_ids:
                addr_records = await client.get_linked_records("addresses", addr_ids)
                addresses = [mapper.map_address(r.get("fields", {})) for r in addr_records]

            location = mapper.map_location(loc_fields, addresses=addresses)
            locations.append(location)

    # Fetch programs
    programs = []
    program_ids = fields.get("programs", [])
    if program_ids:
        program_records = await client.get_linked_records("programs", program_ids)
        programs = [mapper.map_program(r.get("fields", {})) for r in program_records]

    # Fetch funding
    funding = []
    funding_ids = fields.get("funding", [])
    if funding_ids:
        funding_records = await client.get_linked_records("funding", funding_ids)
        funding = [mapper.map_funding(r.get("fields", {})) for r in funding_records]

    return mapper.map_organization(
        fields,
        phones=phones,
        contacts=contacts,
        locations=locations,
        programs=programs,
        funding=funding,
    )
