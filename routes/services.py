"""
Services API endpoints.

REQUIRED endpoints per HSDS specification.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from models.hsds import Service, ServiceSummary, Page
from airtable.client import get_airtable_client
from transform.mapper import HSDSMapper

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=Page)
async def list_services(
    search: Optional[str] = Query(None, description="Full text search"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Results per page"),
    taxonomy_term_id: Optional[str] = Query(None, description="Filter by taxonomy term"),
    taxonomy_id: Optional[str] = Query(None, description="Filter by taxonomy"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    modified_after: Optional[str] = Query(None, description="Filter by modification date"),
    minimal: bool = Query(False, description="Return only ID and modified_date"),
    full: bool = Query(False, description="Return fully nested services"),
):
    """
    List services with pagination and filtering.
    
    REQUIRED endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    
    # Build filter formula if needed
    conditions = []
    if organization_id:
        conditions.append(f"FIND('{organization_id}', ARRAYJOIN({{organization}}, ',')) > 0")
    if taxonomy_term_id:
        conditions.append(f"FIND('{taxonomy_term_id}', ARRAYJOIN({{taxonomy_terms}}, ',')) > 0")
    
    filter_formula = None
    if conditions:
        filter_formula = f"AND({', '.join(conditions)})" if len(conditions) > 1 else conditions[0]
    
    # Fetch services from Airtable
    records = await client.list_records("services", filter_formula=filter_formula)
    
    # Apply search filter locally if provided
    if search:
        search_lower = search.lower()
        records = [
            r for r in records
            if search_lower in (r.get("fields", {}).get("name", "") or "").lower()
            or search_lower in (r.get("fields", {}).get("description", "") or "").lower()
        ]
    
    # Map to HSDS models
    services = []
    for record in records:
        fields = record.get("fields", {})
        
        # Fetch organization summary if organization linked
        org_summary = None
        org_ids = fields.get("organization", [])
        if org_ids:
            org_record = await client.get_record("organizations", org_ids[0])
            if org_record:
                org_summary = mapper.map_organization_summary(org_record.get("fields", {}))
        
        # Fetch program if linked
        program = None
        program_ids = fields.get("programs", [])
        if program_ids:
            prog_record = await client.get_record("programs", program_ids[0])
            if prog_record:
                program = mapper.map_program(prog_record.get("fields", {}))
        
        if minimal:
            # Return minimal data
            services.append({
                "id": fields.get("id", record["id"]),
                "last_modified": fields.get("lastUpdated")
            })
        elif full:
            # Return full nested service
            service = await _get_full_service(record["id"], fields, mapper, client)
            services.append(service.model_dump())
        else:
            # Return service summary - extract organization_id (ORUK required)
            org_id = org_ids[0] if org_ids else "unknown"
            summary = mapper.map_service_summary(
                fields,
                organization_id=org_id,
                organization=org_summary,
                program=program
            )
            services.append(summary.model_dump())
    
    # Paginate results
    return mapper.paginate(services, page, per_page)


@router.get("/{service_id}", response_model=Service)
async def get_service(service_id: str):
    """
    Get a single service with all related data.
    
    REQUIRED endpoint per HSDS specification.
    """
    client = get_airtable_client()
    mapper = HSDSMapper()
    
    # Search for service by HSDS ID or Airtable ID
    records = await client.list_records(
        "services",
        filter_formula=f"OR({{id}}='{service_id}', RECORD_ID()='{service_id}')"
    )
    
    if not records:
        raise HTTPException(status_code=404, detail="Service not found")
    
    record = records[0]
    fields = record.get("fields", {})
    
    return await _get_full_service(record["id"], fields, mapper, client)


async def _get_full_service(
    airtable_id: str,
    fields: dict,
    mapper: HSDSMapper,
    client
) -> Service:
    """Helper to build a fully nested service."""
    
    # Fetch organization
    org_summary = None
    org_ids = fields.get("organization", [])
    if org_ids:
        org_record = await client.get_record("organizations", org_ids[0])
        if org_record:
            org_summary = mapper.map_organization_summary(org_record.get("fields", {}))
    
    # Fetch program
    program = None
    program_ids = fields.get("programs", [])
    if program_ids:
        prog_record = await client.get_record("programs", program_ids[0])
        if prog_record:
            program = mapper.map_program(prog_record.get("fields", {}))
    
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
    
    # Fetch languages
    languages = []
    language_ids = fields.get("languages", [])
    if language_ids:
        language_records = await client.get_linked_records("languages", language_ids)
        languages = [mapper.map_language(r.get("fields", {})) for r in language_records]
    
    # Fetch service areas
    service_areas = []
    area_ids = fields.get("service_areas", [])
    if area_ids:
        area_records = await client.get_linked_records("service_areas", area_ids)
        service_areas = [mapper.map_service_area(r.get("fields", {})) for r in area_records]
    
    # Fetch service_at_locations with nested location data
    service_at_locations = []
    sal_ids = fields.get("service_at_location", [])
    if sal_ids:
        sal_records = await client.get_linked_records("service_at_location", sal_ids)
        for sal_record in sal_records:
            sal_fields = sal_record.get("fields", {})
            
            # Fetch the location for this service_at_location
            location = None
            loc_ids = sal_fields.get("locations", [])
            if loc_ids:
                loc_record = await client.get_record("locations", loc_ids[0])
                if loc_record:
                    loc_fields = loc_record.get("fields", {})
                    
                    # Fetch addresses for location
                    addresses = []
                    addr_ids = loc_fields.get("addresses", [])
                    if addr_ids:
                        addr_records = await client.get_linked_records("addresses", addr_ids)
                        addresses = [mapper.map_address(r.get("fields", {})) for r in addr_records]
                    
                    location = mapper.map_location(loc_fields, addresses=addresses)
            
            sal = mapper.map_service_at_location(sal_fields, location=location)
            service_at_locations.append(sal)
    
    # Fetch funding
    funding = []
    funding_ids = fields.get("funding", [])
    if funding_ids:
        funding_records = await client.get_linked_records("funding", funding_ids)
        funding = [mapper.map_funding(r.get("fields", {})) for r in funding_records]
    
    # Fetch cost options
    cost_options = []
    cost_ids = fields.get("cost_options", [])
    if cost_ids:
        cost_records = await client.get_linked_records("cost_option", cost_ids)
        cost_options = [mapper.map_cost_option(r.get("fields", {})) for r in cost_records]
    
    # Fetch required documents
    required_documents = []
    doc_ids = fields.get("required_documents", [])
    if doc_ids:
        doc_records = await client.get_linked_records("required_document", doc_ids)
        required_documents = [mapper.map_required_document(r.get("fields", {})) for r in doc_records]
    
    # Get organization_id (ORUK required field)
    org_id = org_ids[0] if org_ids else "unknown"
    
    return mapper.map_service(
        fields,
        organization_id=org_id,
        organization=org_summary,
        program=program,
        phones=phones,
        contacts=contacts,
        schedules=schedules,
        service_areas=service_areas,
        service_at_locations=service_at_locations,
        languages=languages,
        funding=funding,
        cost_options=cost_options,
        required_documents=required_documents,
    )
