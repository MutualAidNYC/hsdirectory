"""
Service at Locations API endpoints.

OPTIONAL endpoints per HSDS specification.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from models.hsds import ServiceAtLocation, Page
from airtable.client import get_airtable_client
from transform.mapper import HSDSMapper
from config import get_settings
from data_layer import dependency
from application_layer import application_layer

router = APIRouter(prefix="/service_at_locations", tags=["service_at_locations"])


@router.get("", response_model=Page)
async def list_service_at_locations(
    search: Optional[str] = Query(None, description="Full text search"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    taxonomy_term_id: Optional[str] = Query(None, description="Filter by taxonomy term"),
    taxonomy_id: Optional[str] = Query(None, description="Filter by taxonomy"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    modified_after: Optional[str] = Query(None, description="Filter by modification date"),
    full: bool = Query(False, description="Return fully nested data"),
    postcode: Optional[str] = Query(None, description="Filter by postcode/zipcode proximity"),
    proximity: Optional[int] = Query(None, description="Proximity radius in meters"),
):
    """
    List service_at_locations with pagination and filtering.
    
    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    settings = get_settings()
    
    records = await client.list_records("service_at_location")
    
    # If filtering by published status, get IDs of published services
    published_service_ids = None
    if settings.published_status_value:
        filter_formula = f"{{status}}='{settings.published_status_value}'"
        published_services = await client.list_records("services", filter_formula=filter_formula)
        published_service_ids = set(svc["id"] for svc in published_services)
    
    # Map to HSDS models
    results = []
    for record in records:
        fields = record.get("fields", {})
        
        # Skip if service is not published
        if published_service_ids is not None:
            service_ids = fields.get("services", [])
            if not any(sid in published_service_ids for sid in service_ids):
                continue
        
        if full:
            sal = await _get_full_service_at_location(record["id"], fields, mapper, client)
            results.append(sal.model_dump())
        else:
            # Return minimal data
            sal = mapper.map_service_at_location(fields)
            results.append(sal.model_dump())
    
    return mapper.paginate(results, page, per_page)


async def list_service_at_locations_updated(
    search: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    taxonomy_term_id: Optional[str] = None,
    taxonomy_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    modified_after: Optional[str] = None,
    full: bool = False,
    postcode: Optional[str] = None,
    proximity: Optional[int] = None,
) -> Page:
    service_at_locations_table = dependency.get_service_at_locations_table()
    services_table = dependency.get_service_table()
    location_table = dependency.get_locations_table()
    addresses_table = dependency.get_addresses_table()
    contacts_table = dependency.get_contacts_table()
    phones_table = dependency.get_phones_table()
    schedule_table = dependency.get_schedule_table()
    accessibilities_table = dependency.get_accessibility_table()
    settings = get_settings()

    return application_layer.list_service_at_locations(
        service_at_locations_table=service_at_locations_table,
        services_table=services_table,
        locations_table=location_table,
        addresses_table=addresses_table,
        accessibilities_table=accessibilities_table,
        contacts_table=contacts_table,
        phones_table=phones_table,
        schedule_table=schedule_table,
        settings=settings,
        page=page,
        per_page=per_page,
        full=full,
    )

@router.get("/{sal_id}", response_model=ServiceAtLocation)
async def get_service_at_location(sal_id: str):
    """
    Get a single service_at_location with all related data.
    
    OPTIONAL endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    
    records = await client.list_records(
        "service_at_location",
        filter_formula=f"OR({{id}}='{sal_id}', RECORD_ID()='{sal_id}')"
    )
    
    if not records:
        raise HTTPException(status_code=404, detail="Service at location not found")
    
    record = records[0]
    fields = record.get("fields", {})
    
    return await _get_full_service_at_location(record["id"], fields, mapper, client)

async def get_service_at_location_updated(sal_id: str):
    service_at_location_table = dependency.get_service_at_locations_table()
    addresses_table = dependency.get_addresses_table()
    contacts_table = dependency.get_contacts_table()
    phones_table = dependency.get_phones_table()
    schedule_table = dependency.get_schedule_table()
    locations_table = dependency.get_locations_table()
    accessibility_table = dependency.get_accessibility_table()

    return application_layer.get_service_at_locations(
        sal_id=sal_id,
        service_at_locations_table=service_at_location_table,
        addresses_table=addresses_table,
        contacts_table=contacts_table,
        phones_table=phones_table,
        schedule_table=schedule_table,
        locations_table=locations_table,
        accessibilities_table=accessibility_table,
    )


async def _get_full_service_at_location(
    airtable_id: str,
    fields: dict,
    mapper: HSDSMapper,
    client
) -> ServiceAtLocation:
    """Helper to build a fully nested service_at_location."""
    
    # Fetch location
    location = None
    loc_ids = fields.get("locations", [])
    if loc_ids:
        loc_record = await client.get_record("locations", loc_ids[0])
        if loc_record:
            loc_fields = loc_record.get("fields", {})
            
            # Fetch addresses
            addresses = []
            addr_ids = loc_fields.get("addresses", [])
            if addr_ids:
                addr_records = await client.get_linked_records("addresses", addr_ids)
                addresses = [mapper.map_address(r.get("fields", {})) for r in addr_records]
            
            # Fetch accessibility
            accessibility = []
            acc_ids = loc_fields.get("accessibility", [])
            if acc_ids:
                acc_records = await client.get_linked_records("accessibility", acc_ids)
                accessibility = [mapper.map_accessibility(r.get("fields", {})) for r in acc_records]
            
            location = mapper.map_location(
                loc_fields,
                addresses=addresses,
                accessibility=accessibility
            )
    
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
    
    # Fetch schedules
    schedules = []
    schedule_ids = fields.get("schedules", [])
    if schedule_ids:
        schedule_records = await client.get_linked_records("schedules", schedule_ids)
        schedules = [mapper.map_schedule(r.get("fields", {})) for r in schedule_records]
    
    return mapper.map_service_at_location(
        fields,
        location=location,
        phones=phones,
        contacts=contacts,
        schedules=schedules,
    )
