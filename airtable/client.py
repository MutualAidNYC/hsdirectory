"""
Async Airtable API client.

Provides methods to fetch records from Airtable with pagination
and rate limiting support.
"""
import asyncio
import httpx
from typing import Dict, List, Any, Optional
from config import get_settings


class AirtableClient:
    """Async client for Airtable REST API."""
    
    BASE_URL = "https://api.airtable.com/v0"
    
    # Table name to ID mapping (from Airtable schema)
    TABLE_IDS = {
        "organizations": "tblSAotCxT28qpz5C",
        "services": "tblUV34ri18xDgs64",
        "locations": "tbljfrAgraVmN3k4C",
        "addresses": "tblj0cRXNX6cUvXl4",
        "contacts": "tblMUwgSsxSL0W248",
        "phones": "tblkIMjWC53SogK0g",
        "attributes": "tblQganalHMqv3MrU",
        "service_areas": "tblzmk5213aL7eelv",
        "languages": "tblok7nshfDBjyygQ",
        "taxonomies": "tblA73lY0HxIRTgJn",
        "taxonomy_terms": "tblTBQcmbYH3xJK75",
        "programs": "tbllCNEooPY1hEcnp",
        "schedules": "tblB1KshhZl3Kw2vs",
        "accessibility": "tblH5JHr0byFcYgWH",
        "service_at_location": "tbl6DuXeIQcMAf0lv",
        "funding": "tblk0lisFgbbzMJbl",
        "required_document": "tblYlYs5qlwUafkor",
        "cost_option": "tblw7TjA0R9MCETuT",
        "organization_identifier": "tblQRetpihQaV76Af",
    }
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.airtable_api_key
        self.base_id = settings.airtable_base_id
        self._rate_limit_delay = 0.2  # 5 requests per second
        self._last_request_time = 0
    
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._rate_limit_delay:
            await asyncio.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def list_records(
        self,
        table_name: str,
        fields: Optional[List[str]] = None,
        filter_formula: Optional[str] = None,
        max_records: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all records from a table with pagination.
        
        Args:
            table_name: Name of the Airtable table
            fields: Optional list of field names to return
            filter_formula: Optional Airtable formula for filtering
            max_records: Maximum number of records to return
            
        Returns:
            List of record dictionaries with id and fields
        """
        table_id = self.TABLE_IDS.get(table_name, table_name)
        url = f"{self.BASE_URL}/{self.base_id}/{table_id}"
        
        all_records = []
        offset = None
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                await self._rate_limit()
                
                params = {}
                if fields:
                    params["fields[]"] = fields
                if filter_formula:
                    params["filterByFormula"] = filter_formula
                if offset:
                    params["offset"] = offset
                if max_records:
                    params["maxRecords"] = max_records
                
                response = await client.get(
                    url,
                    headers=self._get_headers(),
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                records = data.get("records", [])
                all_records.extend(records)
                
                offset = data.get("offset")
                if not offset:
                    break
                
                if max_records and len(all_records) >= max_records:
                    break
        
        return all_records
    
    async def get_record(
        self,
        table_name: str,
        record_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a single record by ID.
        
        Args:
            table_name: Name of the Airtable table
            record_id: Airtable record ID
            
        Returns:
            Record dict or None if not found
        """
        table_id = self.TABLE_IDS.get(table_name, table_name)
        url = f"{self.BASE_URL}/{self.base_id}/{table_id}/{record_id}"
        
        await self._rate_limit()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    url,
                    headers=self._get_headers()
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise
    
    async def get_linked_records(
        self,
        table_name: str,
        record_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple linked records by their IDs.
        
        Args:
            table_name: Name of the Airtable table
            record_ids: List of Airtable record IDs
            
        Returns:
            List of record dicts
        """
        if not record_ids:
            return []
        
        # Build filter formula for multiple IDs
        id_conditions = [f"RECORD_ID()='{rid}'" for rid in record_ids]
        formula = f"OR({','.join(id_conditions)})"
        
        return await self.list_records(table_name, filter_formula=formula)


# Singleton instance
_client: Optional[AirtableClient] = None


def get_airtable_client() -> AirtableClient:
    """Get or create the Airtable client singleton."""
    global _client
    if _client is None:
        _client = AirtableClient()
    return _client
