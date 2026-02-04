"""
Background synchronization of Airtable data to local SQLite cache.

Runs periodic sync to keep local data fresh.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from airtable.client import get_airtable_client
from db.database import upsert_record, update_sync_metadata, init_db
from config import get_settings

logger = logging.getLogger(__name__)


class AirtableSync:
    """Synchronizes Airtable data to local SQLite database."""
    
    # Mapping of Airtable table names to local DB tables
    TABLE_MAPPING = {
        "organizations": "organizations",
        "services": "services",
        "locations": "locations",
        "addresses": "addresses",
        "contacts": "contacts",
        "phones": "phones",
        "schedules": "schedules",
        "languages": "languages",
        "taxonomies": "taxonomies",
        "taxonomy_terms": "taxonomy_terms",
        "programs": "programs",
        "service_areas": "service_areas",
        "service_at_location": "service_at_locations",
        "funding": "funding",
        "cost_option": "cost_options",
        "required_document": "required_documents",
        "accessibility": "accessibility",
    }
    
    def __init__(self):
        self.client = get_airtable_client()
        self._sync_task: Optional[asyncio.Task] = None
        self._should_stop = False
    
    async def sync_table(self, airtable_table: str, local_table: str) -> int:
        """
        Sync a single table from Airtable to local database.
        
        Returns the number of records synced.
        """
        logger.info(f"Syncing table: {airtable_table}")
        
        try:
            records = await self.client.list_records(airtable_table)
            
            for record in records:
                airtable_id = record["id"]
                fields = record.get("fields", {})
                
                # Extract the HSDS ID from the 'id' formula field if present
                hsds_id = fields.get("id", airtable_id)
                
                # Handle extra columns for certain tables
                extra_columns = {}
                
                if local_table == "services":
                    org_links = fields.get("organization", [])
                    if org_links:
                        extra_columns["organization_id"] = org_links[0]
                
                elif local_table == "service_at_locations":
                    service_links = fields.get("services", [])
                    location_links = fields.get("locations", [])
                    if service_links:
                        extra_columns["service_id"] = service_links[0]
                    if location_links:
                        extra_columns["location_id"] = location_links[0]
                
                elif local_table == "taxonomy_terms":
                    taxonomy_links = fields.get("taxonomy", [])
                    if taxonomy_links:
                        extra_columns["taxonomy_id"] = taxonomy_links[0]
                
                await upsert_record(
                    local_table,
                    hsds_id,
                    airtable_id,
                    fields,
                    **extra_columns
                )
            
            await update_sync_metadata(local_table, len(records))
            logger.info(f"Synced {len(records)} records from {airtable_table}")
            return len(records)
            
        except Exception as e:
            logger.error(f"Error syncing {airtable_table}: {e}")
            raise
    
    async def full_sync(self) -> Dict[str, int]:
        """
        Perform a full sync of all tables.
        
        Returns a dict mapping table names to record counts.
        """
        logger.info("Starting full sync...")
        results = {}
        
        for airtable_table, local_table in self.TABLE_MAPPING.items():
            try:
                count = await self.sync_table(airtable_table, local_table)
                results[local_table] = count
            except Exception as e:
                logger.error(f"Failed to sync {airtable_table}: {e}")
                results[local_table] = -1
        
        logger.info(f"Full sync complete: {results}")
        return results
    
    async def start_background_sync(self):
        """Start the background sync loop."""
        settings = get_settings()
        interval_seconds = settings.sync_interval_minutes * 60
        
        logger.info(f"Starting background sync (interval: {settings.sync_interval_minutes} minutes)")
        
        async def sync_loop():
            while not self._should_stop:
                try:
                    await self.full_sync()
                except Exception as e:
                    logger.error(f"Background sync error: {e}")
                
                # Wait for next sync interval
                await asyncio.sleep(interval_seconds)
        
        self._sync_task = asyncio.create_task(sync_loop())
    
    async def stop_background_sync(self):
        """Stop the background sync loop."""
        self._should_stop = True
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
            self._sync_task = None
        logger.info("Background sync stopped")


# Singleton instance
_sync: Optional[AirtableSync] = None


def get_sync() -> AirtableSync:
    """Get or create the sync singleton."""
    global _sync
    if _sync is None:
        _sync = AirtableSync()
    return _sync
