"""
Map Services API endpoint.

Serves service data with location info and filter categories for map page.
"""
import math
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel

router = APIRouter(prefix="/map", tags=["map"])

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in miles between two points on the earth."""
    R = 3959.0 # miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c



class MapService(BaseModel):
    """Service data for map display."""
    id: str
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    needFocus: List[str] = []
    communityFocus: List[str] = []
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    organization_name: Optional[str] = None


class CategoryDetail(BaseModel):
    """Detailed category info for map filters."""
    name: str
    icon: Optional[str] = None


class MapDataResponse(BaseModel):
    """Full map data response with services and filter options."""
    services: List[MapService]
    needCategories: List[CategoryDetail]
    communityCategories: List[CategoryDetail]


@router.get("/services", response_model=MapDataResponse)
async def get_map_services():
    """
    Get services with location data and filter categories for map page.
    """
    from airtable.client import get_airtable_client
    from config import get_settings
    import json
    from pathlib import Path
    
    client = get_airtable_client()
    settings = get_settings()

    # Load geocache
    geocache = {}
    cache_path = Path(__file__).parent.parent / "geocache.json"
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                geocache = json.load(f)
        except Exception:
            pass
    
    # Fetch services (filtered by status)
    filter_formula = None
    if settings.published_status_value:
        filter_formula = f"{{status}}='{settings.published_status_value}'"
    
    services = await client.list_records("services", filter_formula=filter_formula)
    
    # Fetch addresses and locations for coordinate lookup
    addresses = await client.list_records("addresses")
    locations = await client.list_records("locations")
    
    # Fetch phones and organizations
    phones = await client.list_records("phones")
    organizations = await client.list_records("organizations")
    tax_terms = await client.list_records("taxonomy_terms")
    
    # Build lookups
    org_lookup = {}
    for record in organizations:
        fields = record.get("fields", {})
        org_lookup[record["id"]] = fields.get("name", "")

    icon_lookup = {}
    for record in tax_terms:
        fields = record.get("fields", {})
        name = fields.get("name")
        icon_url = None
        icon_dark = fields.get("x-icon_dark", [])
        if icon_dark and isinstance(icon_dark, list) and len(icon_dark) > 0:
            icon_url = icon_dark[0].get("url")
        if name and icon_url:
            icon_lookup[name] = icon_url

    location_lookup = {}
    for record in locations:
        fields = record.get("fields", {})
        location_lookup[record["id"]] = {
            "name": fields.get("name"),
            "latitude": fields.get("latitude"),
            "longitude": fields.get("longitude"),
            "address_ids": fields.get("addresses", []),
        }
    
    address_lookup = {}
    for record in addresses:
        fields = record.get("fields", {})
        addr_parts = [
            fields.get("address_1", ""),
            fields.get("city", ""),
            fields.get("state_province", ""),
            fields.get("postal_code", ""),
        ]
        address_lookup[record["id"]] = {
            "formatted": ", ".join(p for p in addr_parts if p),
            "location_ids": fields.get("location", []),
        }
    
    phone_lookup = {}
    for record in phones:
        fields = record.get("fields", {})
        phone_lookup[record["id"]] = fields.get("number", "")
    
    # Collect unique filter values
    need_categories = set()
    community_categories = set()
    
    # Build service list
    map_services = []
    
    for record in services:
        fields = record.get("fields", {})
        
        # Get filter values
        need_focus = fields.get("needFocus", []) or []
        community_focus = fields.get("communityFocus", []) or []
        
        if isinstance(need_focus, list):
            need_categories.update(need_focus)
        if isinstance(community_focus, list):
            community_categories.update(community_focus)
        
        # Get location info
        latitude = None
        longitude = None
        address = None
        
        # Try to get location from service_at_location or locations
        location_ids = fields.get("locations", []) or []
        for loc_id in location_ids:
            if loc_id in location_lookup:
                loc = location_lookup[loc_id]
                # Extract first linked address
                for addr_id in loc.get("address_ids", []):
                    if addr_id in address_lookup:
                        address = address_lookup[addr_id].get("formatted")
                        break
                if not address:
                    address = loc.get("name")
                    
                if loc.get("latitude") and loc.get("longitude"):
                    latitude = float(loc["latitude"])
                    longitude = float(loc["longitude"])
                    break
                else:
                    # Fallback to geocache for the linked address
                    for addr_id in loc.get("address_ids", []):
                        if addr_id in geocache:
                            geo = geocache[addr_id]
                            if geo and "latitude" in geo and "longitude" in geo:
                                latitude = float(geo["latitude"])
                                longitude = float(geo["longitude"])
                                break
                    if latitude:
                        break
        
        # Fallback to first address with location
        if not latitude:
            address_ids = fields.get("addresses", []) or []
            for addr_id in address_ids:
                if addr_id in address_lookup:
                    addr = address_lookup[addr_id]
                    if not address:
                        address = addr.get("formatted")
                    # Try to get coords from linked location
                    for loc_id in addr.get("location_ids", []):
                        if loc_id in location_lookup:
                            loc = location_lookup[loc_id]
                            if loc.get("latitude") and loc.get("longitude"):
                                latitude = float(loc["latitude"])
                                longitude = float(loc["longitude"])
                                break
                    if latitude:
                        break
                    
                    # Try fallback to geocache
                    if addr_id in geocache:
                        geo = geocache[addr_id]
                        if geo and "latitude" in geo and "longitude" in geo:
                            latitude = float(geo["latitude"])
                            longitude = float(geo["longitude"])
                            break
        # Distance filter (50 miles from NYC)
        if latitude is not None and longitude is not None:
            if haversine(latitude, longitude, 40.7128, -74.0060) > 50.0:
                latitude = None
                longitude = None
        
        # Get phone
        phone = None
        phone_ids = fields.get("phones", []) or []
        for phone_id in phone_ids:
            if phone_id in phone_lookup:
                phone = phone_lookup[phone_id]
                break
        # Get org name
        org_name = None
        org_ids = fields.get("organizations", []) or []
        for org_id in org_ids:
            if org_id in org_lookup:
                org_name = org_lookup[org_id]
                break

        map_services.append(MapService(
            id=record["id"],
            name=fields.get("name", "Unnamed Service"),
            description=fields.get("description"),
            address=address,
            phone=phone,
            url=fields.get("url"),
            needFocus=need_focus if isinstance(need_focus, list) else [],
            communityFocus=community_focus if isinstance(community_focus, list) else [],
            latitude=latitude,
            longitude=longitude,
            organization_name=org_name,
        ))
    
    return MapDataResponse(
        services=map_services,
        needCategories=[
            {"name": c, "icon": icon_lookup.get(c)} 
            for c in sorted(need_categories)
        ],
        communityCategories=[
            {"name": c, "icon": icon_lookup.get(c)} 
            for c in sorted(community_categories)
        ],
    )
