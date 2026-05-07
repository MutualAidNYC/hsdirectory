import pytest

from models.hsds import Location, ServiceAtLocation
from routes import service_at_locations


@pytest.fixture
def test_id():
    return "sal1"


@pytest.mark.asyncio
async def test_service_at_locations_get(test_id):
    sal = await service_at_locations.get_service_at_location_updated(
        id=test_id
    )

    assert isinstance(sal, ServiceAtLocation)
    assert isinstance(sal.location, Location)

@pytest.mark.asyncio
async def test_service_at_locations_get_not_found():
    sal = await service_at_locations.get_service_at_location_updated(
        id="nonexistent_id"
    )

    assert sal is None

@pytest.mark.asyncio
async def test_service_at_locations_get_no_location(test_id):
    sal = await service_at_locations.get_service_at_location_updated(
        id=test_id
    )

    assert isinstance(sal, ServiceAtLocation)
    assert sal.id == test_id
    assert sal.location is None

@pytest.mark.asyncio
async def test_service_at_locations_list_service_at_locations():
    all_services_at_locations: list[ServiceAtLocation] = await service_at_locations.list_service_at_locations_updated(
        page=1,
        per_page=10,
        full=True,
    )

    assert isinstance(all_services_at_locations, list)
    assert all(isinstance(item, ServiceAtLocation) for item in all_services_at_locations)
    assert any(isinstance(item.location, Location) for item in all_services_at_locations)
