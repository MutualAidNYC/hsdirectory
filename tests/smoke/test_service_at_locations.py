import pytest

from models.hsds import Page, ServiceAtLocation
from routes_updated import service_at_locations

@pytest.fixture
def test_id() -> str:
    return "recdCdKEoExUm5bjs"

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_service_at_locations_get(test_id: str):
    sal = await service_at_locations.get_service_at_location(
        sal_id=test_id
    )

    assert isinstance(sal, ServiceAtLocation)

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_service_at_locations_get_not_found():
    sal = await service_at_locations.get_service_at_location(
        sal_id="nonexistent_id"
    )

    assert sal is None

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_service_at_locations_get_no_location(test_id: str):
    sal = await service_at_locations.get_service_at_location(
        sal_id=test_id
    )

    assert isinstance(sal, ServiceAtLocation)
    assert sal.id == test_id
    assert sal.location is None

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_service_at_locations_list_service_at_locations():
    all_services_at_locations: list[ServiceAtLocation] = \
        await service_at_locations.list_service_at_locations(
            page=1,
            per_page=10,
            full=True,
        )

    assert isinstance(all_services_at_locations, Page)
    assert all(
        isinstance(item, ServiceAtLocation) for item in all_services_at_locations.contents
    )
