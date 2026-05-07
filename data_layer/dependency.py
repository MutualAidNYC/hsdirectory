from data_layer.airtable import AirtableData
from models.airtable import (
    AddressResponse,
    ContactResponse,
    LocationResponse,
    PhoneResponse,
    ScheduleResponse,
    ServiceAtLocationResponse,
    ServiceResponse,
)


def get_service_table() -> AirtableData:
    return AirtableData(model_class=ServiceResponse)

def get_service_at_locations_table() -> AirtableData:
    return AirtableData(
        model_class=ServiceAtLocationResponse,
        id_columns=['{id}','RECORD_ID()']
    )

def get_locations_table() -> AirtableData:
    return AirtableData(model_class=LocationResponse)

def get_addresses_table() -> AirtableData:
    return AirtableData(model_class=AddressResponse)

def get_contacts_table() -> AirtableData:
    return AirtableData(model_class=ContactResponse)

def get_phones_table() -> AirtableData:
    return AirtableData(model_class=PhoneResponse)

def get_schedule_table() -> AirtableData:
    return AirtableData(model_class=ScheduleResponse)