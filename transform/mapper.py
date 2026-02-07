"""
Data transformation from Airtable records to HSDS models.

Maps Airtable field names to HSDS schema fields.
"""
from typing import Dict, Any, List, Optional
from models.hsds import (
    Organization, OrganizationSummary, Service, ServiceSummary,
    Location, ServiceAtLocation, Taxonomy, TaxonomyTerm,
    Phone, Address, Contact, Schedule, Language, ServiceArea,
    Program, Funding, CostOption, RequiredDocument, Accessibility,
    Page
)


def safe_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""
    if value is None:
        return None
    try:
        # Handle string values (from multilineText fields)
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> Optional[int]:
    """Safely convert a value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def first_or_none(lst: Optional[List]) -> Optional[Any]:
    """Get first element of list or None."""
    if lst and len(lst) > 0:
        return lst[0]
    return None


def join_list(lst: Optional[List]) -> Optional[str]:
    """Join list elements with comma."""
    if lst:
        return ", ".join(str(x) for x in lst)
    return None


class HSDSMapper:
    """Maps Airtable records to HSDS Pydantic models."""
    
    def __init__(self, record_cache: Dict[str, Dict[str, Any]] = None):
        """
        Initialize mapper with optional record cache.
        
        The cache maps table names to dicts of record_id -> fields,
        used for resolving linked records.
        """
        self.cache = record_cache or {}
    
    def map_phone(self, data: Dict[str, Any]) -> Phone:
        """Map Airtable phone record to HSDS Phone."""
        return Phone(
            id=data.get("id", ""),
            number=data.get("number", ""),
            extension=data.get("extension"),
            type=data.get("type"),
            description=data.get("description"),
        )
    
    def map_address(self, data: Dict[str, Any]) -> Address:
        """Map Airtable address record to HSDS Address."""
        # Handle address_type as list or string
        address_type = data.get("address_type")
        if isinstance(address_type, list):
            address_type = first_or_none(address_type)
        
        return Address(
            id=data.get("id", ""),
            address_1=data.get("address_1"),
            address_2=data.get("address_2"),
            city=data.get("city"),
            state_province=data.get("state_province"),
            postal_code=data.get("postal_code"),
            region=data.get("region"),
            country=data.get("country"),
            address_type=address_type,
            attention=data.get("attention"),
        )
    
    def map_language(self, data: Dict[str, Any]) -> Language:
        """Map Airtable language record to HSDS Language."""
        return Language(
            id=data.get("id", ""),
            name=data.get("name"),
            code=data.get("code"),
            note=data.get("note"),
        )
    
    def map_accessibility(self, data: Dict[str, Any]) -> Accessibility:
        """Map Airtable accessibility record to HSDS Accessibility."""
        return Accessibility(
            id=data.get("id", ""),
            description=data.get("description"),
            details=data.get("details"),
            url=data.get("url"),
        )
    
    def map_schedule(self, data: Dict[str, Any]) -> Schedule:
        """Map Airtable schedule record to HSDS Schedule."""
        # Handle byday as list
        byday = data.get("byday")
        if isinstance(byday, list):
            byday = ",".join(byday)
        
        return Schedule(
            id=data.get("id", ""),
            valid_from=data.get("valid_from"),
            valid_to=data.get("valid_to"),
            dtstart=data.get("dtstart"),
            timezone=data.get("timezone"),
            until=data.get("until"),
            count=data.get("count"),
            wkst=data.get("wkst"),
            freq=data.get("freq"),
            interval=data.get("interval"),
            byday=byday,
            byweekno=data.get("byweekno"),
            bymonthday=data.get("bymonthday"),
            byyearday=data.get("byyearday"),
            description=data.get("description"),
            opens_at=data.get("opens_at"),
            closes_at=data.get("closes_at"),
            schedule_link=data.get("schedule_link"),
            attending_type=data.get("attending_type"),
            notes=data.get("notes"),
        )
    
    def map_contact(self, data: Dict[str, Any], phones: List[Phone] = None) -> Contact:
        """Map Airtable contact record to HSDS Contact."""
        return Contact(
            id=data.get("id", ""),
            name=data.get("name"),
            title=data.get("title"),
            department=data.get("department"),
            email=data.get("email"),
            phones=phones,
        )
    
    def map_service_area(self, data: Dict[str, Any]) -> ServiceArea:
        """Map Airtable service_area record to HSDS ServiceArea."""
        return ServiceArea(
            id=data.get("id", ""),
            name=data.get("name"),
            description=data.get("description"),
            extent=data.get("extent"),
            extent_type=data.get("extent_type"),
            uri=data.get("uri"),
        )
    
    def map_program(self, data: Dict[str, Any]) -> Program:
        """Map Airtable program record to HSDS Program."""
        return Program(
            id=data.get("id", ""),
            name=data.get("name", ""),
            alternate_name=data.get("alternate_name"),
            description=data.get("description"),
        )
    
    def map_funding(self, data: Dict[str, Any]) -> Funding:
        """Map Airtable funding record to HSDS Funding."""
        return Funding(
            id=data.get("id", ""),
            source=data.get("source"),
        )
    
    def map_cost_option(self, data: Dict[str, Any]) -> CostOption:
        """Map Airtable cost_option record to HSDS CostOption."""
        return CostOption(
            id=data.get("id", ""),
            option=data.get("option"),
            currency=data.get("currency"),
            amount=safe_float(data.get("amount")),
            amount_description=data.get("amount_description"),
            valid_from=data.get("valid_from"),
            valid_to=data.get("valid_to"),
        )
    
    def map_required_document(self, data: Dict[str, Any]) -> RequiredDocument:
        """Map Airtable required_document record to HSDS RequiredDocument."""
        return RequiredDocument(
            id=data.get("id", ""),
            document=data.get("document"),
            uri=data.get("uri"),
        )
    
    def map_taxonomy(self, data: Dict[str, Any]) -> Taxonomy:
        """Map Airtable taxonomy record to HSDS Taxonomy."""
        return Taxonomy(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description"),
            uri=data.get("uri"),
            version=data.get("version"),
        )
    
    def map_taxonomy_term(self, data: Dict[str, Any], taxonomy: Taxonomy = None) -> TaxonomyTerm:
        """Map Airtable taxonomy_term record to HSDS TaxonomyTerm."""
        return TaxonomyTerm(
            id=data.get("id", ""),
            name=data.get("name", ""),
            code=data.get("code"),
            description=data.get("description"),
            parent_id=first_or_none(data.get("parent")),
            taxonomy=first_or_none(data.get("taxonomy")),
            taxonomy_detail=taxonomy,
            language=data.get("language"),
            term_uri=data.get("term_uri"),
        )
    
    def map_location(
        self,
        data: Dict[str, Any],
        addresses: List[Address] = None,
        phones: List[Phone] = None,
        contacts: List[Contact] = None,
        accessibility: List[Accessibility] = None,
        languages: List[Language] = None,
        schedules: List[Schedule] = None,
    ) -> Location:
        """Map Airtable location record to HSDS Location."""
        # Handle location_type as list
        location_type = data.get("location_type")
        if isinstance(location_type, list):
            location_type = first_or_none(location_type)
        
        return Location(
            id=data.get("id", ""),
            location_type=location_type,
            url=data.get("url"),
            name=data.get("name"),
            alternate_name=data.get("alternate_name"),
            description=data.get("description"),
            transportation=data.get("transportation"),
            latitude=safe_float(data.get("latitude")),
            longitude=safe_float(data.get("longitude")),
            external_identifier=data.get("external_identifier"),
            external_identifier_type=data.get("external_identifier_type"),
            addresses=addresses,
            phones=phones,
            contacts=contacts,
            accessibility=accessibility,
            languages=languages,
            schedules=schedules,
        )
    
    def map_organization_summary(self, data: Dict[str, Any]) -> OrganizationSummary:
        """Map Airtable organization to minimal HSDS summary."""
        return OrganizationSummary(
            id=data.get("id", ""),
            name=data.get("name", ""),
            alternate_name=data.get("alternate_name"),
            description=data.get("description"),
            email=data.get("email"),
            website=data.get("website"),
            logo=data.get("logo"),
            uri=data.get("uri"),
        )
    
    def map_organization(
        self,
        data: Dict[str, Any],
        phones: List[Phone] = None,
        contacts: List[Contact] = None,
        locations: List[Location] = None,
        programs: List[Program] = None,
        funding: List[Funding] = None,
    ) -> Organization:
        """Map Airtable organization record to full HSDS Organization."""
        return Organization(
            id=data.get("id", ""),
            name=data.get("name", ""),
            alternate_name=data.get("alternate_name"),
            description=data.get("description"),
            email=data.get("email"),
            website=data.get("website"),
            year_incorporated=safe_int(data.get("year_incorporated")),
            legal_status=data.get("legal_status"),
            logo=data.get("logo"),
            uri=data.get("uri"),
            parent_organization_id=first_or_none(data.get("organization")),
            phones=phones,
            contacts=contacts,
            locations=locations,
            programs=programs,
            funding=funding,
        )
    
    def map_service_at_location(
        self,
        data: Dict[str, Any],
        location: Location = None,
        phones: List[Phone] = None,
        contacts: List[Contact] = None,
        schedules: List[Schedule] = None,
        service_areas: List[ServiceArea] = None,
    ) -> ServiceAtLocation:
        """Map Airtable service_at_location record to HSDS ServiceAtLocation."""
        return ServiceAtLocation(
            id=data.get("id", ""),
            service_id=first_or_none(data.get("services")),
            description=data.get("description"),
            location=location,
            phones=phones,
            contacts=contacts,
            schedules=schedules,
            service_areas=service_areas,
        )
    
    def map_service_summary(
        self,
        data: Dict[str, Any],
        organization_id: str,
        organization: OrganizationSummary = None,
        program: Program = None,
    ) -> ServiceSummary:
        """Map Airtable service to minimal HSDS summary (ORUK compliant)."""
        return ServiceSummary(
            id=data.get("id", ""),
            organization_id=organization_id,  # Required by ORUK
            name=data.get("name", ""),
            status=data.get("status") or "active",  # Required by ORUK
            alternate_name=data.get("alternate_name"),
            description=data.get("description"),
            url=data.get("url"),
            email=data.get("email"),
            last_modified=data.get("lastUpdated"),
            organization=organization,
            program=program,
            # Taxonomy fields from Airtable (camelCase in Airtable)
            need_focus=data.get("needFocus") or [],
            community_focus=data.get("communityFocus") or [],
        )
    
    def map_service(
        self,
        data: Dict[str, Any],
        organization_id: str,
        organization: OrganizationSummary = None,
        program: Program = None,
        phones: List[Phone] = None,
        contacts: List[Contact] = None,
        schedules: List[Schedule] = None,
        service_areas: List[ServiceArea] = None,
        service_at_locations: List[ServiceAtLocation] = None,
        languages: List[Language] = None,
        funding: List[Funding] = None,
        cost_options: List[CostOption] = None,
        required_documents: List[RequiredDocument] = None,
    ) -> Service:
        """Map Airtable service record to full HSDS Service (ORUK compliant)."""
        # Extract group name from Airtable's groupName field (lookup field returns list)
        group_name_list = data.get("groupName", [])
        group_name = group_name_list[0] if group_name_list else None
        
        return Service(
            id=data.get("id", ""),
            organization_id=organization_id,  # Required by ORUK
            name=data.get("name", ""),
            status=data.get("status") or "active",  # Required by ORUK
            alternate_name=data.get("alternate_name"),
            description=data.get("description"),
            url=data.get("url"),
            email=data.get("email"),
            interpretation_services=data.get("interpretation_services"),
            application_process=data.get("application_process"),
            fees_description=data.get("fees_description"),
            accreditations=data.get("accreditations"),
            eligibility_description=data.get("eligibility_description"),
            minimum_age=safe_int(data.get("minimum_age")),
            maximum_age=safe_int(data.get("maximum_age")),
            assured_date=data.get("assured_date"),
            assurer_email=data.get("assurer_email"),
            alert=data.get("alert"),
            last_modified=data.get("lastUpdated"),
            organization=organization,
            program=program,
            phones=phones,
            contacts=contacts,
            schedules=schedules,
            service_areas=service_areas,
            service_at_locations=service_at_locations,
            languages=languages,
            funding=funding,
            cost_options=cost_options,
            required_documents=required_documents,
            # Custom extension fields
            group_name=group_name,
            need_focus=data.get("needFocus"),
            community_focus=data.get("communityFocus"),
        )
    
    @staticmethod
    def paginate(items: List, page: int, per_page: int) -> Page:
        """Create a paginated response."""
        total_items = len(items)
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        
        start = (page - 1) * per_page
        end = start + per_page
        page_items = items[start:end]
        
        return Page(
            total_items=total_items,
            total_pages=total_pages,
            page_number=page,
            size=len(page_items),
            first_page=(page == 1),
            last_page=(page >= total_pages),
            empty=(len(page_items) == 0),
            contents=page_items,
        )
