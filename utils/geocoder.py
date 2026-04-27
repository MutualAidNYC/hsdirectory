"""
Geocoding utility for HSDS addresses.

Uses OpenStreetMap Nominatim API (free, no key required).
Results are cached to avoid redundant API calls.

Usage:
    python utils/geocoder.py
"""
import asyncio
import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Nominatim API settings
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "HSDirectory/1.0 (https://github.com/openreferral)"
RATE_LIMIT_SECONDS = 1.0  # Nominatim requires max 1 request/second

# Cache file path
CACHE_FILE = Path(__file__).parent.parent / "geocache.json"


class Geocoder:
    """Geocodes addresses using Nominatim with caching."""
    
    def __init__(self, cache_file: Path = CACHE_FILE):
        self.cache_file = cache_file
        self.cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
        self._last_request_time = 0.0
    
    def _load_cache(self):
        """Load geocode cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached geocodes")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save geocode cache to file."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} geocodes to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    # Regex patterns for secondary unit designators to strip from address_1.
    # These confuse Nominatim and cause geocoding failures.
    # NOTE: Patterns must NOT over-strip — they only match when a clear secondary
    # unit keyword is present (Suite, Floor, Apt, etc.) followed by a designator.
    _UNIT_PATTERNS = [
        # "Suite 639", "Ste. 1B", "Apt 5", "Unit 2", "Room 3", "# 32", "#32"
        r",?\s+(Suite|Ste\.?|Apt\.?|Unit|Room|Rm\.?)\s+[\w\-/]+\s*",
        r",?\s+#\s*[\w\-/]+\s*",
        # "3rd Floor", "2nd Fl.", "31st Floor" — ordinal MUST be followed by Floor/Fl.
        # Strip the ordinal + Floor + anything that follows (e.g. "of Sterling Bank")
        r",?\s+\d+(st|nd|rd|th)\s+Floor.*",
        r",?\s+\d+(st|nd|rd|th)\s+Fl\.?.*",
        # "Ground Floor of Sterling Bank" — strip Ground Floor + trailing text
        r",?\s+Ground\s+Floor.*",
        r",?\s+Basement.*",
        # P.O. Box (rest of string), also when at start: "P.O. Box 3179"
        r"(,\s*|\s*)P\.?O\.?\s+Box\s+\d+.*",
    ]

    def _normalize_address_line(self, address_1: str) -> str:
        """Strip floor/suite/unit info from an address line before geocoding.

        Why: Nominatim often fails on addresses like "25 Flatbush Ave, 3rd Floor"
        but succeeds on "25 Flatbush Ave". Stripping secondary designators improves
        hit rate significantly.
        """
        import re
        result = address_1
        for pattern in self._UNIT_PATTERNS:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()
        # Remove trailing comma
        result = result.rstrip(",").strip()
        return result

    def _format_address(self, address: Dict[str, Any]) -> str:
        """Format address dict into a geocoding query string.

        Normalizes address_1 to strip secondary unit designators that break Nominatim.
        """
        parts = []
        if address.get("address_1"):
            parts.append(self._normalize_address_line(address["address_1"]))
        if address.get("city"):
            parts.append(address["city"])
        if address.get("state_province"):
            parts.append(address["state_province"])
        if address.get("postal_code"):
            parts.append(address["postal_code"])
        if address.get("country"):
            parts.append(address["country"])
        return ", ".join(p for p in parts if p)
    
    async def _rate_limit(self):
        """Enforce rate limiting for Nominatim API."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < RATE_LIMIT_SECONDS:
            await asyncio.sleep(RATE_LIMIT_SECONDS - elapsed)
        self._last_request_time = time.time()
    
    async def geocode_address(
        self,
        address_id: str,
        address: Dict[str, Any],
        client: httpx.AsyncClient
    ) -> Optional[Dict[str, Any]]:
        """
        Geocode a single address.
        
        Returns dict with latitude, longitude, formatted_address, geocoded_at.
        Returns None if geocoding fails.
        """
        # Check cache first
        if address_id in self.cache:
            return self.cache[address_id]
        
        # Format the address query
        query = self._format_address(address)
        if not query.strip():
            logger.warning(f"Empty address for {address_id}")
            return None
        
        # Rate limit
        await self._rate_limit()
        
        try:
            response = await client.get(
                NOMINATIM_URL,
                params={
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 0,
                },
                headers={"User-Agent": USER_AGENT},
            )
            response.raise_for_status()
            results = response.json()
            
            if results:
                result = results[0]
                lat = float(result["lat"])
                lon = float(result["lon"])

                # Sanity check: reject results >200 miles from NYC.
                # Addresses like "100 Pearl St, 19th Floor" without city context
                # can resolve to wrong locations worldwide.
                from utils.haversine import haversine as _haversine
                dist_from_nyc = _haversine(lat, lon, 40.7128, -74.0060)
                if dist_from_nyc > 200:
                    logger.warning(
                        f"Rejecting geocode for {address_id}: {query[:50]} "
                        f"({dist_from_nyc:.0f} miles from NYC)"
                    )
                    return None

                geocoded = {
                    "latitude": lat,
                    "longitude": lon,
                    "formatted_address": query,
                    "geocoded_at": datetime.utcnow().isoformat(),
                }
                self.cache[address_id] = geocoded
                logger.info(f"Geocoded {address_id}: {query[:50]}...")
                return geocoded
            else:
                logger.warning(f"No results for {address_id}: {query[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"Geocoding error for {address_id}: {e}")
            return None
    
    async def geocode_batch(
        self,
        addresses: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Geocode a batch of addresses.
        
        Each address dict should have 'id' and address fields.
        Returns dict mapping address_id to geocode result.
        """
        results = {}
        total = len(addresses)
        cached = 0
        geocoded = 0
        failed = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i, addr in enumerate(addresses, 1):
                addr_id = addr.get("id", f"addr_{i}")
                
                # Check cache
                if addr_id in self.cache:
                    results[addr_id] = self.cache[addr_id]
                    cached += 1
                    continue
                
                result = await self.geocode_address(addr_id, addr, client)
                if result:
                    results[addr_id] = result
                    geocoded += 1
                else:
                    failed += 1
                
                # Progress log every 10 addresses
                if i % 10 == 0 or i == total:
                    logger.info(
                        f"Progress: {i}/{total} "
                        f"(cached: {cached}, geocoded: {geocoded}, failed: {failed})"
                    )
        
        # Save cache after batch
        self._save_cache()
        
        logger.info(
            f"Batch complete: {total} addresses "
            f"(cached: {cached}, geocoded: {geocoded}, failed: {failed})"
        )
        return results


async def main():
    """Main entry point for geocoding all addresses from API."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from airtable.client import get_airtable_client
    
    logger.info("Starting geocoding process...")
    
    # Fetch addresses from Airtable
    client = get_airtable_client()
    addresses = await client.list_records("addresses")
    
    if not addresses:
        logger.warning("No addresses found")
        return
    
    logger.info(f"Found {len(addresses)} addresses to geocode")
    
    # Convert to list of address dicts
    address_list = []
    for record in addresses:
        fields = record.get("fields", {})
        fields["id"] = record["id"]
        address_list.append(fields)
    
    # Geocode
    geocoder = Geocoder()
    results = await geocoder.geocode_batch(address_list)
    
    logger.info(f"Geocoding complete. {len(results)} addresses geocoded.")


if __name__ == "__main__":
    asyncio.run(main())
