
import pytest
from pydantic import BaseModel

from application_layer import application_layer
from config import Settings
from data_layer.data import TestData
from models.airtable import (
    AddressResponse,
    ContactResponse,
    LocationResponse,
    PhoneResponse,
    ScheduleResponse,
    ServiceAtLocationResponse,
    ServiceResponse,
)
from models.hsds import (
    Address,
    Contact,
    Location,
    Phone,
    Schedule,
    ServiceAtLocation,
)


@pytest.fixture
def base_address_response() -> AddressResponse:
    return AddressResponse(
        id="addr1",
        address_1="123 Main St",
        city="New York",
        state_province="NY",
        postal_code="10001",
        country="USA",
    )

@pytest.fixture
def base_contact_response() -> ContactResponse:
    return ContactResponse(
        id="contact1",
        name="Jane Doe",
        title="Director",
        department="Outreach",
        email="foo@abc.com",
    )

@pytest.fixture
def base_phone_response() -> PhoneResponse:
    return PhoneResponse(
        id="phone1",
        number="555-123-4567",
        extension="123",
        type="Office",
        description="Main office line",
    )

@pytest.fixture
def base_schedule_response() -> ScheduleResponse:
    return ScheduleResponse(
        id="schedule1",
        valid_from="2024-01-01T09:00:00Z",
        valid_to="2024-12-31T17:00:00Z",
        dtstart="2024-01-01T09:00:00Z",
        timezone="America/New_York",
        freq="WEEKLY",
        byday="MO,WE,FR",
        description="Open every Monday, Wednesday, and Friday from 9am to 5pm",
        opens_at="09:00:00",
        closes_at="17:00:00",
        schedule_link="https://example.com/schedule",
        attending_type="In-person",
        notes="Closed on holidays",
    )

@pytest.fixture
def base_location_response(base_address_response) -> LocationResponse:
    return LocationResponse(
        id="loc1",
        location_type="Physical",
        url="https://example.com/location",
        name="Main Office",
        alternate_name="Headquarters",
        description="Our main office location",
        transportation="Subway: A, C, E to 42nd St; Bus: M42, M104",
        latitude=40.7128,
        longitude=-74.0060,
        external_identifier="LOC123",
        external_identifier_type="InternalID",
        addresses=[base_address_response.id],
        accessibility=["Wheelchair accessible", "Braille signage"],
    )

@pytest.fixture
def service_at_location_response_with_no_locations(
    base_contact_response,
    base_phone_response,
    base_schedule_response
) -> ServiceAtLocationResponse:
    return ServiceAtLocationResponse(
        id="sal1",
        service_id="svc1",
        locations=None,
        contacts=[base_contact_response.id],
        phones=[base_phone_response.id],
        schedules=[base_schedule_response.id],
    )

@pytest.fixture
def full_service_at_location_response(
    base_location_response,
    base_contact_response,
    base_phone_response,
    base_schedule_response
) -> ServiceAtLocationResponse:
    return ServiceAtLocationResponse(
        id="sal2",
        service_id="svc2",
        locations=[base_location_response.id],
        contacts=[base_contact_response.id],
        phones=[base_phone_response.id],
        schedules=[base_schedule_response.id],
    )

@pytest.fixture
def service_response() -> ServiceResponse:
    return ServiceResponse(
        id="svc1",
        name="Food Assistance",
        description="Provides food assistance to individuals and families in need.",
        organization="org1",
    )

@pytest.fixture
def expected_service_at_location_with_locations_result(
    base_location_response,
    base_contact_response,
    base_phone_response,
    base_schedule_response
) -> ServiceAtLocation:
    return ServiceAtLocation(
        id="sal1",
        service_id="svc1",
        location=Location(
            id=base_location_response.id,
            location_type=base_location_response.location_type,
            url=base_location_response.url,
            name=base_location_response.name,
            alternate_name=base_location_response.alternate_name,
            description=base_location_response.description,
            transportation=base_location_response.transportation,
            latitude=base_location_response.latitude,
            longitude=base_location_response.longitude,
            external_identifier=base_location_response.external_identifier,
            external_identifier_type=base_location_response.external_identifier_type,
            addresses=[
                Address(
                    id=base_location_response.addresses[0],
                    address_1="123 Main St",
                    city="New York",
                    state_province="NY",
                    postal_code="10001",
                    country="USA",
                )
            ],
            accessibility=["Wheelchair accessible", "Braille signage"],
        ),
        contacts=[
            Contact(
                id=base_contact_response.id,
                name=base_contact_response.name,
                title=base_contact_response.title,
                department=base_contact_response.department,
                email=base_contact_response.email,
            )
        ],
        phones=[
            Phone(
                id=base_phone_response.id,
                number=base_phone_response.number,
                extension=base_phone_response.extension,
                type=base_phone_response.type,
                description=base_phone_response.description,
            )
        ],
        schedules=[
            Schedule(
                id=base_schedule_response.id,
                valid_from=base_schedule_response.valid_from,
                valid_to=base_schedule_response.valid_to,
                dtstart=base_schedule_response.dtstart,
                timezone=base_schedule_response.timezone,
                freq=base_schedule_response.freq,
                byday=base_schedule_response.byday,
                description=base_schedule_response.description,
                opens_at=base_schedule_response.opens_at,
                closes_at=base_schedule_response.closes_at,
                schedule_link=base_schedule_response.schedule_link,
                attending_type=base_schedule_response.attending_type,
                notes=base_schedule_response.notes,
            )
        ],
    )

@pytest.fixture
def expected_service_at_location_with_no_locations_result(
    base_contact_response,
    base_phone_response,
    base_schedule_response
) -> ServiceAtLocation:
    return ServiceAtLocation(
        id="sal2",
        service_id="svc2",
        location=None,
        contacts=[
            Contact(
                id=base_contact_response.id,
                name=base_contact_response.name,
                title=base_contact_response.title,
                department=base_contact_response.department,
                email=base_contact_response.email,
            )
        ],
        phones=[
            Phone(
                id=base_phone_response.id,
                number=base_phone_response.number,
                extension=base_phone_response.extension,
                type=base_phone_response.type,
                description=base_phone_response.description,
            )
        ],
        schedules=[
            Schedule(
                id=base_schedule_response.id,
                valid_from=base_schedule_response.valid_from,
                valid_to=base_schedule_response.valid_to,
                dtstart=base_schedule_response.dtstart,
                timezone=base_schedule_response.timezone,
                freq=base_schedule_response.freq,
                byday=base_schedule_response.byday,
                description=base_schedule_response.description,
                opens_at=base_schedule_response.opens_at,
                closes_at=base_schedule_response.closes_at,
                schedule_link=base_schedule_response.schedule_link,
                attending_type=base_schedule_response.attending_type,
                notes=base_schedule_response.notes,
            )
        ],
    )    

def _test_data(
    model_class: type[BaseModel],
    example_id: str,
    example_response: BaseModel,
) -> TestData:
    return TestData(
        model_class=model_class,
        data={
            example_id: example_response
        }
    )

@pytest.fixture
def test_service_at_location_data_with_no_locations(
    service_at_location_response_with_no_locations: ServiceAtLocationResponse,
) -> TestData[ServiceAtLocationResponse]:
    return _test_data(
        model_class=ServiceAtLocationResponse,
        example_id=service_at_location_response_with_no_locations.id,
        example_response=service_at_location_response_with_no_locations,
    )

@pytest.fixture
def test_service_at_location_data_with_locations(
    full_service_at_location_response: ServiceAtLocationResponse,
) -> TestData[ServiceAtLocationResponse]:
    return _test_data(
        model_class=ServiceAtLocationResponse,
        example_id=full_service_at_location_response.id,
        example_response=full_service_at_location_response,
    )

@pytest.fixture
def test_services_data(
    service_response: ServiceResponse,
) -> TestData[ServiceResponse]:
    return _test_data(
        model_class=ServiceResponse,
        example_id=service_response.id,
        example_response=service_response,
    )

@pytest.fixture
def test_locations_data(
    base_location_response: LocationResponse,
) -> TestData[LocationResponse]:
    return _test_data(
        model_class=LocationResponse,
        example_id=base_location_response.id,
        example_response=base_location_response,
    )

@pytest.fixture
def test_addresses_data(
    base_address_response: AddressResponse,
) -> TestData[AddressResponse]:
    return _test_data(
        model_class=AddressResponse,
        example_id=base_address_response.id,
        example_response=base_address_response,
    )

@pytest.fixture
def test_contacts_data(
    base_contact_response: ContactResponse,
) -> TestData[ContactResponse]:
    return _test_data(
        model_class=ContactResponse,
        example_id=base_contact_response.id,
        example_response=base_contact_response,
    )

@pytest.fixture
def test_phones_data(
    base_phone_response: PhoneResponse,
) -> TestData[PhoneResponse]:
    return _test_data(
        model_class=PhoneResponse,
        example_id=base_phone_response.id,
        example_response=base_phone_response,
    )

@pytest.fixture
def test_schedules_data(
    base_schedule_response: ScheduleResponse,
) -> TestData[ScheduleResponse]:
    return _test_data(
        model_class=ScheduleResponse,
        example_id=base_schedule_response.id,
        example_response=base_schedule_response,
    )

@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        airtable_api_key="fake_api_key",
        airtable_base_id="fake_base_id",
        airtable_service_at_locations_table_name="Service at Locations",
        airtable_services_table_name="Services",
        airtable_locations_table_name="Locations",
        airtable_addresses_table_name="Addresses",
        airtable_contacts_table_name="Contacts",
        airtable_phones_table_name="Phones",
        airtable_schedules_table_name="Schedules",
    )

def test_list_service_at_locations_returns_only_published_services(
    test_service_at_location_data_with_locations: TestData,
    test_services_data: TestData,
    test_locations_data: TestData,
    test_addresses_data: TestData,
    test_contacts_data: TestData,
    test_phones_data: TestData,
    test_schedules_data: TestData,
    test_settings: Settings,
    expected_service_at_location_with_locations_result: ServiceAtLocation,
    expected_service_at_location_with_no_locations_result: ServiceAtLocation,
):
    services = application_layer.list_service_at_locations(
        service_at_locations_table=test_service_at_location_data_with_locations,
        services_table=test_services_data,
        locations_table=test_locations_data,
        addresses_table=test_addresses_data,
        contacts_table=test_contacts_data,
        phones_table=test_phones_data,
        schedule_table=test_schedules_data,
        settings=test_settings,
        full=True,
    )

    assert len(services) == 1
    assert any(
        svc.id == expected_service_at_location_with_no_locations_result.service_id
        for svc in services
    )
    assert all(
        svc.id != expected_service_at_location_with_locations_result.service_id
        for svc in services
    )



def test_get_service_at_locations_returns_service_at_location_with_no_locations(
    test_service_at_location_data_with_no_locations: TestData,
    test_locations_data: TestData,
    test_addresses_data: TestData,
    test_contacts_data: TestData,
    test_phones_data: TestData,
    test_schedules_data: TestData,
    expected_service_at_location_with_no_locations_result: ServiceAtLocation,
):
    result = application_layer.get_service_at_locations(
        sal_id=test_service_at_location_data_with_no_locations,
        service_at_locations_table=test_service_at_location_data_with_no_locations,
        locations_table=test_locations_data,
        addresses_table=test_addresses_data,
        contacts_table=test_contacts_data,
        phones_table=test_phones_data,
        schedule_table=test_schedules_data,
    )

    assert result.model_dump() == expected_service_at_location_with_no_locations_result.model_dump()


def test_get_service_at_locations_returns_service_at_location_when_location_id_is_not_found(
    test_service_at_location_data_with_locations: TestData,
    test_locations_data: TestData,
    test_addresses_data: TestData,
    test_contacts_data: TestData,
    test_phones_data: TestData,
    test_schedules_data: TestData,
    expected_service_at_location_with_locations_result: ServiceAtLocation,
):
    result = application_layer.get_service_at_locations(
        sal_id=test_service_at_location_data_with_locations,
        service_at_locations_table=test_service_at_location_data_with_locations,
        locations_table=test_locations_data,
        addresses_table=test_addresses_data,
        contacts_table=test_contacts_data,
        phones_table=test_phones_data,
        schedule_table=test_schedules_data,
    )

    assert result.model_dump() == expected_service_at_location_with_locations_result.model_dump()

def test_get_service_at_locations_returns_none_when_service_at_location_id_is_not_found(
    test_service_at_location_data_with_locations: TestData,
    test_locations_data: TestData,
    test_addresses_data: TestData,
    test_contacts_data: TestData,
    test_phones_data: TestData,
    test_schedules_data: TestData,
    expected_service_at_location_with_no_locations_result: ServiceAtLocation,
):
    result = application_layer.get_service_at_locations(
        sal_id="nonexistent_id",
        service_at_locations_table=test_service_at_location_data_with_locations,
        locations_table=test_locations_data,
        addresses_table=test_addresses_data,
        contacts_table=test_contacts_data,
        phones_table=test_phones_data,
        schedule_table=test_schedules_data,
    )

    assert result.model_dump() == expected_service_at_location_with_no_locations_result.model_dump()