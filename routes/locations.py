"""
Geocoded Locations API endpoint.

Serves location data with coordinates for map rendering.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/locations", tags=["locations"])

GEOCACHE_FILE = Path(__file__).parent.parent / "geocache.json"


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


def load_geocache() -> Dict[str, Dict[str, Any]]:
    """Load geocache from file."""
    if GEOCACHE_FILE.exists():
        try:
            with open(GEOCACHE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


@router.get("/geocoded", response_model=GeocodedLocationsResponse)
async def get_geocoded_locations(
    limit: int = Query(500, ge=1, le=1000, description="Maximum locations to return"),
):
    """
    Get all geocoded locations for map rendering.
    
    Uses coordinates from locations table (which have lat/long directly)
    and falls back to geocache for addresses without location coords.
    """
    from airtable.client import get_airtable_client
    from config import get_settings
    
    client = get_airtable_client()
    settings = get_settings()
    geocache = load_geocache()
    
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
    
    # Fetch addresses for fallback geocache
    addresses = await client.list_records("addresses")
    address_lookup = {}
    for record in addresses:
        fields = record.get("fields", {})
        address_lookup[record["id"]] = {
            "address_1": fields.get("address_1"),
            "city": fields.get("city"),
            "state_province": fields.get("state_province"),
            "postal_code": fields.get("postal_code"),
            "location_ids": fields.get("location", []),
        }
    
    # Build geocoded locations from locations with coordinates
    geocoded_locations = []
    seen_coords = set()
    
    for record in locations:
        fields = record.get("fields", {})
        loc_id = record["id"]
        
        # Get coordinates from location
        lat = fields.get("latitude")
        lng = fields.get("longitude")
        
        if not lat or not lng:
            # Try to get from x-latitude/x-longitude
            lat = fields.get("x-latitude")
            lng = fields.get("x-longitude")
        
        if not lat or not lng:
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
        if address_ids and address_ids[0] in address_lookup:
            addr = address_lookup[address_ids[0]]
            parts = [addr.get("address_1", ""), addr.get("city", ""), addr.get("state_province", ""), addr.get("postal_code", "")]
            address_str = ", ".join(p for p in parts if p)
        
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
    
    # If we don't have enough from locations, add from geocache
    if len(geocoded_locations) < limit:
        for addr_id, geocode in geocache.items():
            if addr_id not in address_lookup:
                continue
            
            # Skip duplicate coordinates
            coord_key = f"{geocode['latitude']},{geocode['longitude']}"
            if coord_key in seen_coords:
                continue
            seen_coords.add(coord_key)
            
            geocoded_locations.append(GeocodedLocation(
                id=addr_id,
                name=geocode.get("formatted_address"),
                address=geocode.get("formatted_address"),
                latitude=geocode["latitude"],
                longitude=geocode["longitude"],
                service_id=None,
                service_name=None,
                organization_id=None,
                organization_name=None,
            ))
            
            if len(geocoded_locations) >= limit:
                break
    
    return GeocodedLocationsResponse(
        total=len(geocoded_locations),
        locations=geocoded_locations,
    )
