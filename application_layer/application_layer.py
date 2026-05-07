
from config import Settings
from data_layer.data import DataEntity, Filter
from models.airtable import (
    AddressResponse,
    ContactResponse,
    LocationResponse,
    PhoneResponse,
    ScheduleResponse,
    ServiceAtLocationResponse,
    ServiceResponse,
)
from models.hsds import Location, ServiceAtLocation


def list_service_at_locations(
    service_at_locations_table: DataEntity[ServiceAtLocationResponse],
    services_table: DataEntity[ServiceResponse],
    locations_table: DataEntity[LocationResponse],
    addresses_table: DataEntity[AddressResponse],
    contacts_table: DataEntity[ContactResponse],
    phones_table: DataEntity[PhoneResponse],
    schedule_table: DataEntity[ScheduleResponse],
    settings: Settings,
    page: int = 1,
    per_page: int = 20,
    full: bool = False,
) -> list[ServiceAtLocation]:
    services_at_locations = service_at_locations_table.list()
    services = services_table.list(
        filter=[
            Filter(
                key="status",
                value=settings.published_status_value,
            )
        ]
    )
    published_service_ids = set(svc.id for svc in services)

    results = []
    for sal in services_at_locations:
        if all(sid not in published_service_ids for sid in sal.service_id):
            continue  # Skip if service is not published

        res = _create_service_at_location_result(
            service_at_location_response=sal,
            locations_table=locations_table,
            addresses_table=addresses_table,
            contacts_table=contacts_table,
            phones_table=phones_table,
            schedule_table=schedule_table,
        )
        results.append(res)

    return results
        

def get_service_at_locations(
    sal_id: int,
    service_at_locations_table: DataEntity[ServiceAtLocationResponse],
    locations_table: DataEntity[LocationResponse],
    addresses_table: DataEntity[AddressResponse],
    contacts_table: DataEntity[ContactResponse],
    phones_table: DataEntity[PhoneResponse],
    schedule_table: DataEntity[ScheduleResponse],
) -> ServiceAtLocation | None:
    service_at_locations = service_at_locations_table.get(id=sal_id)
    if not service_at_locations:
        return None
    
    return _create_service_at_location_result(
        service_at_location_response=service_at_locations[0],
        locations_table=locations_table,
        addresses_table=addresses_table,
        contacts_table=contacts_table,
        phones_table=phones_table,
        schedule_table=schedule_table,
    )

def _create_service_at_location_result(
    service_at_location_response: ServiceAtLocationResponse,
    locations_table: DataEntity[LocationResponse],
    addresses_table: DataEntity[AddressResponse],
    contacts_table: DataEntity[ContactResponse],
    phones_table: DataEntity[PhoneResponse],
    schedule_table: DataEntity[ScheduleResponse],
) -> ServiceAtLocation:
    contacts = contacts_table.get_bulk(ids=service_at_location_response.contacts) if service_at_location_response.contacts else None
    phones = phones_table.get_bulk(ids=service_at_location_response.phones) if service_at_location_response.phones else None
    schedules = schedule_table.get_bulk(ids=service_at_location_response.schedules) if service_at_location_response.schedules else None
    
    if not service_at_location_response.locations:
        return ServiceAtLocation(
            id=service_at_location_response.id,
            service_id=service_at_location_response.service_id,
            location=None,
            contacts=contacts,
            phones=phones,
            schedules=schedules,
        )

    location = locations_table.get(id=service_at_location_response.locations[0]) if service_at_location_response and service_at_location_response.locations else None

    if not location:
        return ServiceAtLocation(
            id=service_at_location_response.id,
            service_id=service_at_location_response.service_id,
            location=None,
            contacts=contacts,
            phones=phones,
            schedules=schedules,
        )

    addresses = addresses_table.get_bulk(ids=location.addresses) if location.addresses else None
    accessibilities = location.accessibility if location.accessibility else None
    location_response = Location(
        id=location.id,
        location_type=location.location_type,
        url=location.url,
        name=location.name,
        alternate_name=location.alternate_name,
        description=location.description,
        transportation=location.transportation,
        latitude=location.latitude,
        longitude=location.longitude,
        external_identifier=location.external_identifier,
        external_identifier_type=location.external_identifier_type,
        addresses=addresses,
        phones=phones,
        contacts=contacts,
        accessibility=accessibilities,
        languages=None, # TODO: Add languages to location model and response
        schedules=schedules,
    )

    return ServiceAtLocation(
        id=service_at_location_response.id,
        service_id=service_at_location_response.service_id,
        location=location_response,
        contacts=contacts,
        phones=phones,
        schedules=schedules,
    )
