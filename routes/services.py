"""
HSDS Services endpoints.

Serves service data from the SQLite cache (synced from Airtable).
"""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from models.hsds import Page, Service, ServiceSummary
from db.database import get_records, get_record, search_services, get_db
from transform.mapper import HSDSMapper
from config import get_settings
import json

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
    Serves data from SQLite cache for fast performance.
    """
    mapper = HSDSMapper()
    settings = get_settings()
    
    async with get_db() as db:
        # Build query based on filters
        base_query = "SELECT id, airtable_id, organization_id, data FROM services"
        count_query = "SELECT COUNT(*) FROM services"
        where_clauses = []
        params = []
        
        # Filter by published status if configured
        if settings.published_status_value:
            where_clauses.append("json_extract(data, '$.status') = ?")
            params.append(settings.published_status_value)
        
        # Filter by organization_id
        if organization_id:
            where_clauses.append("organization_id = ?")
            params.append(organization_id)
        
        # Text search on name and description
        if search:
            where_clauses.append(
                "(json_extract(data, '$.name') LIKE ? OR json_extract(data, '$.description') LIKE ?)"
            )
            params.extend([f"%{search}%", f"%{search}%"])
        
        # Apply WHERE clauses
        if where_clauses:
            where_str = " WHERE " + " AND ".join(where_clauses)
            base_query += where_str
            count_query += where_str
        
        # Get total count
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        # Add pagination
        offset = (page - 1) * per_page
        base_query += " ORDER BY json_extract(data, '$.name') LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        # Fetch records
        cursor = await db.execute(base_query, params)
        rows = await cursor.fetchall()
        
        # Map to HSDS models
        services = []
        for row in rows:
            record_id = row[0]
            airtable_id = row[1]
            org_id = row[2] or "unknown"
            data = json.loads(row[3])
            
            # Add the ID to the data dict
            data["id"] = record_id
            
            if minimal:
                services.append({
                    "id": record_id,
                    "last_modified": data.get("lastUpdated")
                })
            elif full:
                # For full mode, get related data from cache
                service = await _get_full_service_from_cache(db, record_id, data, org_id, mapper)
                services.append(service.model_dump())
            else:
                # Get organization summary from cache if available
                org_summary = None
                if org_id != "unknown":
                    org_cursor = await db.execute(
                        "SELECT data FROM organizations WHERE id = ? OR airtable_id = ?",
                        [org_id, org_id]
                    )
                    org_row = await org_cursor.fetchone()
                    if org_row:
                        org_data = json.loads(org_row[0])
                        org_summary = mapper.map_organization_summary(org_data)
                
                # Map service summary
                summary = mapper.map_service_summary(
                    data,
                    organization_id=org_id,
                    organization=org_summary,
                    program=None
                )
                services.append(summary.model_dump())
        
        # Return paginated response
        total_pages = (total + per_page - 1) // per_page
        return Page(
            total_items=total,
            total_pages=total_pages,
            page_number=page,
            size=per_page,
            first_page=(page == 1),
            last_page=(page >= total_pages),
            empty=(len(services) == 0),
            contents=services
        )


@router.get("/{service_id}", response_model=Service)
async def get_service(service_id: str):
    """
    Get a single service with all related data.
    
    REQUIRED endpoint per HSDS specification.
    Serves data from SQLite cache.
    """
    mapper = HSDSMapper()
    settings = get_settings()
    
    async with get_db() as db:
        # Search for service by HSDS ID or Airtable ID
        cursor = await db.execute(
            "SELECT id, airtable_id, organization_id, data FROM services WHERE id = ? OR airtable_id = ?",
            [service_id, service_id]
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Service not found")
        
        record_id = row[0]
        airtable_id = row[1]
        org_id = row[2] or "unknown"
        data = json.loads(row[3])
        data["id"] = record_id
        
        # Check published status if configured
        if settings.published_status_value:
            if data.get("status") != settings.published_status_value:
                raise HTTPException(status_code=404, detail="Service not found")
        
        return await _get_full_service_from_cache(db, record_id, data, org_id, mapper)


async def _get_full_service_from_cache(db, service_id: str, data: dict, org_id: str, mapper: HSDSMapper) -> Service:
    """Build a full Service object from cached data."""
    
    # Get organization
    organization = None
    if org_id != "unknown":
        cursor = await db.execute(
            "SELECT data FROM organizations WHERE id = ? OR airtable_id = ?",
            [org_id, org_id]
        )
        org_row = await cursor.fetchone()
        if org_row:
            org_data = json.loads(org_row[0])
            org_data["id"] = org_id
            organization = mapper.map_organization(org_data)
    
    # Get service_at_locations
    cursor = await db.execute(
        "SELECT id, location_id, data FROM service_at_locations WHERE service_id = ?",
        [service_id]
    )
    sal_rows = await cursor.fetchall()
    
    service_at_locations = []
    for sal_row in sal_rows:
        sal_id = sal_row[0]
        location_id = sal_row[1]
        sal_data = json.loads(sal_row[2])
        sal_data["id"] = sal_id
        
        # Get location
        location = None
        if location_id:
            loc_cursor = await db.execute(
                "SELECT data FROM locations WHERE id = ? OR airtable_id = ?",
                [location_id, location_id]
            )
            loc_row = await loc_cursor.fetchone()
            if loc_row:
                loc_data = json.loads(loc_row[0])
                loc_data["id"] = location_id
                
                # Get address for location
                addresses = []
                addr_ids = loc_data.get("addresses", [])
                if addr_ids:
                    for addr_id in addr_ids[:1]:  # Get first address
                        addr_cursor = await db.execute(
                            "SELECT data FROM addresses WHERE id = ? OR airtable_id = ?",
                            [addr_id, addr_id]
                        )
                        addr_row = await addr_cursor.fetchone()
                        if addr_row:
                            addr_data = json.loads(addr_row[0])
                            addr_data["id"] = addr_id
                            addresses.append(mapper.map_address(addr_data))
                
                location = mapper.map_location(loc_data, addresses=addresses)
        
        sal = mapper.map_service_at_location(sal_data, location=location)
        service_at_locations.append(sal)
    
    # Get phones linked to service
    phones = []
    phone_ids = data.get("phones", [])
    for phone_id in phone_ids[:5]:  # Limit to 5
        cursor = await db.execute(
            "SELECT data FROM phones WHERE id = ? OR airtable_id = ?",
            [phone_id, phone_id]
        )
        phone_row = await cursor.fetchone()
        if phone_row:
            phone_data = json.loads(phone_row[0])
            phone_data["id"] = phone_id
            phones.append(mapper.map_phone(phone_data))
    
    # Get contacts
    contacts = []
    contact_ids = data.get("contacts", [])
    for contact_id in contact_ids[:5]:
        cursor = await db.execute(
            "SELECT data FROM contacts WHERE id = ? OR airtable_id = ?",
            [contact_id, contact_id]
        )
        contact_row = await cursor.fetchone()
        if contact_row:
            contact_data = json.loads(contact_row[0])
            contact_data["id"] = contact_id
            contacts.append(mapper.map_contact(contact_data))
    
    # Get languages
    languages = []
    lang_ids = data.get("languages", [])
    for lang_id in lang_ids[:10]:
        cursor = await db.execute(
            "SELECT data FROM languages WHERE id = ? OR airtable_id = ?",
            [lang_id, lang_id]
        )
        lang_row = await cursor.fetchone()
        if lang_row:
            lang_data = json.loads(lang_row[0])
            lang_data["id"] = lang_id
            languages.append(mapper.map_language(lang_data))
    
    # Map the full service
    return mapper.map_service(
        data,
        organization_id=org_id,
        organization=organization,
        phones=phones,
        contacts=contacts,
        languages=languages,
        service_at_locations=service_at_locations,
    )
