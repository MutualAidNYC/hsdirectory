"""
Map Services API endpoint.

Serves service data with location info and filter categories for map page.
"""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from utils.haversine import haversine

router = APIRouter(prefix="/map", tags=["map"])


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

    client = get_airtable_client()
    settings = get_settings()

    # Fetch services (filtered by status)
    filter_formula = None
    if settings.published_status_value:
        filter_formula = f"{{status}}='{settings.published_status_value}'"

    services = await client.list_records("services", filter_formula=filter_formula)

    # Fetch addresses and locations for coordinate lookup
    addresses = await client.list_records("addresses")
    locations = await client.list_records("locations")

    # Fetch service_at_location junction records to resolve location for services
    # that don't have a direct `locations` link on the service record itself.
    service_at_locs = await client.list_records("service_at_location")

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

    # Build a lookup: service_airtable_id -> list of location_ids
    # via the service_at_location junction table.
    sal_location_lookup: dict = {}
    for record in service_at_locs:
        fields = record.get("fields", {})
        service_ids = fields.get("services", []) or []
        loc_ids = fields.get("locations", []) or []
        for sid in service_ids:
            if sid not in sal_location_lookup:
                sal_location_lookup[sid] = []
            sal_location_lookup[sid].extend(loc_ids)

    phone_lookup = {}
    for record in phones:
        fields = record.get("fields", {})
        phone_lookup[record["id"]] = fields.get("number", "")
    
    # Collect unique filter values
    need_categories = set()
    community_categories = set()
    
    def _resolve_location(
        loc_id: str,
        location_lookup: dict,
        address_lookup: dict,
    ) -> tuple:
        """Resolve lat/lng/address from a location record ID.

        Returns (latitude, longitude, address_str) or (None, None, None).
        """
        if loc_id not in location_lookup:
            return None, None, None
        loc = location_lookup[loc_id]
        # Extract first linked address string
        addr_str = None
        for aid in loc.get("address_ids", []):
            if aid in address_lookup:
                addr_str = address_lookup[aid].get("formatted")
                break
        if not addr_str:
            addr_str = loc.get("name")

        lat = loc.get("latitude")
        lng = loc.get("longitude")
        if lat is not None and lng is not None:
            return lat, lng, addr_str

        return None, None, addr_str

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

        # Priority 1: locations linked via service_at_location junction table
        # (HSDS-recommended pattern for service→location association)
        sal_loc_ids = sal_location_lookup.get(record["id"], [])
        for loc_id in sal_loc_ids:
            lat, lng, addr = _resolve_location(loc_id, location_lookup, address_lookup)
            if lat and lng:
                latitude, longitude, address = lat, lng, addr
                break

        # Priority 2: locations linked directly on the service record
        if not latitude:
            for loc_id in (fields.get("locations", []) or []):
                lat, lng, addr = _resolve_location(loc_id, location_lookup, address_lookup)
                if lat and lng:
                    latitude, longitude, address = lat, lng, addr
                    break

        # Priority 3: addresses linked directly on the service record
        if not latitude:
            for addr_id in (fields.get("addresses", []) or []):
                if addr_id in address_lookup:
                    addr = address_lookup[addr_id]
                    if not address:
                        address = addr.get("formatted")
                    # Try via linked location
                    for loc_id in addr.get("location_ids", []):
                        if loc_id in location_lookup:
                            loc = location_lookup[loc_id]
                            if loc.get("latitude") and loc.get("longitude"):
                                latitude = float(loc["latitude"])
                                longitude = float(loc["longitude"])
                                break
                    if latitude:
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
