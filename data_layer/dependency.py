from data_layer.airtable import AirtableData, Table
from models.airtable import (
    AccessibilityResponse,
    AddressResponse,
    ContactResponse,
    LocationResponse,
    PhoneResponse,
    ScheduleResponse,
    ServiceAtLocationResponse,
    ServiceResponse,
)


def get_service_table() -> AirtableData:
    return AirtableData(
        model_class=ServiceResponse, table=Table(name="services")
    )

def get_service_at_locations_table() -> AirtableData:
    return AirtableData(
        model_class=ServiceAtLocationResponse,
        table=Table(name="service_at_location"),
        id_columns=['{id}','RECORD_ID()']
    )

def get_locations_table() -> AirtableData:
    return AirtableData(
        model_class=LocationResponse,
        table=Table(name="locations"),
    )

def get_addresses_table() -> AirtableData:
    return AirtableData(
        model_class=AddressResponse,
        table=Table(name="addresses"),
    )

def get_contacts_table() -> AirtableData:
    return AirtableData(
        model_class=ContactResponse,
        table=Table(name="contacts")
    )

def get_phones_table() -> AirtableData:
    return AirtableData(
        model_class=PhoneResponse,
        table=Table(name="phones")
    )

def get_schedule_table() -> AirtableData:
    return AirtableData(
        model_class=ScheduleResponse,
        table=Table(name="schedules")
    )

def get_accessibility_table() -> AirtableData:
    return AirtableData(
        model_class=AccessibilityResponse,
        table=Table(name="accessibility")
    )