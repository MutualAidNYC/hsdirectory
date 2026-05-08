import pytest

from data_layer.airtable import AirtableData, Filter, Table
from models.airtable import ServiceAtLocationResponse


@pytest.fixture
def airtable_client() -> AirtableData[ServiceAtLocationResponse]:
    return AirtableData(
        model_class=ServiceAtLocationResponse,
        table=Table(name='service_at_location')
    )

@pytest.mark.integration
def test_airtable_integration_list(airtable_client: AirtableData[ServiceAtLocationResponse]):
    results = airtable_client.list()
    assert results is not None
    assert isinstance(results, list)
    assert len(results) > 0

@pytest.mark.integration
def test_airtable_integration_get(airtable_client: AirtableData[ServiceAtLocationResponse]):
    records = airtable_client.get(id='recdCdKEoExUm5bjs')
    assert records is not None
    assert isinstance(records, ServiceAtLocationResponse)

@pytest.mark.integration
def test_airtable_integration_list_with_filters(
    airtable_client: AirtableData[ServiceAtLocationResponse]
):
    filters = [Filter(key='id', value='recdCdKEoExUm5bjs')]
    results = airtable_client.list(filters=filters)
    assert results is not None
    assert isinstance(results, list)
    assert all(isinstance(record, ServiceAtLocationResponse) for record in results)

@pytest.mark.integration
def test_airtable_bulk_get(airtable_client: AirtableData[ServiceAtLocationResponse]):
    ids = ['recdCdKEoExUm5bjs']
    records = airtable_client.get_bulk(ids=ids)
    assert records is not None
    assert isinstance(records, list)
    assert len(records) == len(ids)
    
    for record in records:
        assert isinstance(record, ServiceAtLocationResponse)
        assert record.id in ids