from fastapi import APIRouter
from typing import Optional

from application_layer import application_layer
from config import get_settings
from data_layer import dependency
from models.hsds import Page, ServiceAtLocation

router = APIRouter(prefix="/service_at_locations", tags=["service_at_locations"])


@router.get("", response_model=ServiceAtLocation)
async def get_service_at_location(sal_id: str):
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

@router.get("/list", response_model=Page)
async def list_service_at_locations(
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
