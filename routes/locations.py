"""
Geocoded Locations API endpoint.

Serves location data with coordinates for map rendering.
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/locations", tags=["locations"])


class GeocodedLocation(BaseModel):
    """A location with geocoded coordinates."""
    id: str
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: float
    longitude: float
    service_id: Optional[str] = None
    service_name: Optional[str] = None
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None


class GeocodedLocationsResponse(BaseModel):
    """Response containing all geocoded locations."""
    total: int
    locations: List[GeocodedLocation]


@router.get("/geocoded", response_model=GeocodedLocationsResponse)
async def get_geocoded_locations(
    limit: int = Query(500, ge=1, le=1000, description="Maximum locations to return"),
):
    """
    Get all geocoded locations for map rendering.
    
    Coordinates come from the locations table, written by a geocoding script added
    to Airtable.
    """
    from airtable.client import get_airtable_client
    from config import get_settings
    
    client = get_airtable_client()
    settings = get_settings()
    
    # Fetch locations (which have lat/long directly)
    locations = await client.list_records("locations")
    
    # Fetch organizations to build location -> org mapping
    organizations = await client.list_records("organizations")
    
    # Build org location mapping (orgs have locations field)
    org_by_location: Dict[str, Dict] = {}
    for record in organizations:
        fields = record.get("fields", {})
        org_id = record["id"]
        org_name = fields.get("name")
        # Organizations link to locations
        location_ids = fields.get("locations", [])
        for loc_id in location_ids:
            org_by_location[loc_id] = {
                "id": org_id,
                "name": org_name,
            }
    
    # Fetch services (filtered by status)
    filter_formula = None
    if settings.published_status_value:
        filter_formula = f"{{status}}='{settings.published_status_value}'"
    
    services = await client.list_records("services", filter_formula=filter_formula)
    
    # Build org_id -> first service mapping
    service_by_org: Dict[str, Dict] = {}
    for record in services:
        fields = record.get("fields", {})
        org_ids = fields.get("organization", []) or fields.get("organizations", [])
        for org_id in org_ids:
            if org_id not in service_by_org:
                service_by_org[org_id] = {
                    "id": record["id"],
                    "name": fields.get("name"),
                }
    
    # Fetch addresses; each location's first linked address becomes its display string
    addresses = await client.list_records("addresses")
    address_lookup = {}
    for record in addresses:
        fields = record.get("fields", {})
        parts = [
            fields.get("address_1"),
            fields.get("city"),
            fields.get("state_province"),
            fields.get("postal_code"),
        ]
        address_lookup[record["id"]] = ", ".join(p for p in parts if p)
    
    # Build geocoded locations from locations with coordinates
    geocoded_locations = []
    seen_coords = set()
    
    for record in locations:
        fields = record.get("fields", {})
        loc_id = record["id"]
        
        # Get coordinates from location
        lat = fields.get("latitude")
        lng = fields.get("longitude")

        if lat is None or lng is None:
            continue
        
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            continue
        
        # Skip duplicate coordinates
        coord_key = f"{lat},{lng}"
        if coord_key in seen_coords:
            continue
        seen_coords.add(coord_key)
        
        # Get organization linked to this location
        org_info = org_by_location.get(loc_id, {})
        org_id = org_info.get("id")
        org_name = org_info.get("name")
        
        # Get a service from this organization
        service_info = service_by_org.get(org_id, {}) if org_id else {}
        service_id = service_info.get("id")
        service_name = service_info.get("name")
        
        # Build address string from linked addresses
        address_str = fields.get("name", "")
        address_ids = fields.get("addresses", [])
        if address_ids:
            address_str = address_lookup.get(address_ids[0]) or address_str
        
        geocoded_locations.append(GeocodedLocation(
            id=loc_id,
            name=fields.get("name") or address_str,
            address=address_str or fields.get("name"),
            latitude=lat,
            longitude=lng,
            service_id=service_id,
            service_name=service_name,
            organization_id=org_id,
            organization_name=org_name,
        ))
        
        if len(geocoded_locations) >= limit:
            break
    
    return GeocodedLocationsResponse(
        total=len(geocoded_locations),
        locations=geocoded_locations,
    )
