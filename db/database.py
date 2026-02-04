"""
SQLite database operations for caching Airtable data.

Provides async database access using aiosqlite for improved performance.
"""
import json
import aiosqlite
from typing import Dict, List, Any, Optional, TypeVar, Type
from pathlib import Path
from contextlib import asynccontextmanager

DATABASE_PATH = Path(__file__).parent.parent / "data" / "hsds_cache.db"


async def init_db():
    """Initialize the database with required tables."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Core tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                organization_id TEXT,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS service_at_locations (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                service_id TEXT,
                location_id TEXT,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS taxonomies (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS taxonomy_terms (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                taxonomy_id TEXT,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Supporting tables
        await db.execute("""
            CREATE TABLE IF NOT EXISTS phones (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS languages (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS service_areas (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS funding (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cost_options (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS required_documents (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS accessibility (
                id TEXT PRIMARY KEY,
                airtable_id TEXT UNIQUE,
                data JSON NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indexes for common queries
        await db.execute("CREATE INDEX IF NOT EXISTS idx_services_org ON services(organization_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sal_service ON service_at_locations(service_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_sal_location ON service_at_locations(location_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_terms_taxonomy ON taxonomy_terms(taxonomy_id)")
        
        # Full-text search for services
        await db.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS services_fts USING fts5(
                id,
                name,
                description,
                content='services',
                content_rowid='rowid'
            )
        """)
        
        # Sync metadata table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                table_name TEXT PRIMARY KEY,
                last_sync TIMESTAMP,
                record_count INTEGER
            )
        """)
        
        await db.commit()


@asynccontextmanager
async def get_db():
    """Get database connection as async context manager."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def upsert_record(table: str, record_id: str, airtable_id: str, data: Dict[str, Any], **extra_columns):
    """Insert or update a record in the database."""
    async with get_db() as db:
        columns = ["id", "airtable_id", "data"]
        values = [record_id, airtable_id, json.dumps(data)]
        
        for key, value in extra_columns.items():
            columns.append(key)
            values.append(value)
        
        placeholders = ", ".join(["?" for _ in values])
        column_str = ", ".join(columns)
        updates = ", ".join([f"{col}=excluded.{col}" for col in columns[1:]])
        
        await db.execute(
            f"""
            INSERT INTO {table} ({column_str}) VALUES ({placeholders})
            ON CONFLICT(id) DO UPDATE SET {updates}, updated_at=CURRENT_TIMESTAMP
            """,
            values
        )
        await db.commit()


async def get_record(table: str, record_id: str) -> Optional[Dict[str, Any]]:
    """Get a single record by ID."""
    async with get_db() as db:
        cursor = await db.execute(
            f"SELECT data FROM {table} WHERE id = ?",
            [record_id]
        )
        row = await cursor.fetchone()
        if row:
            return json.loads(row["data"])
        return None


async def get_records(
    table: str,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    filters: Optional[Dict[str, str]] = None
) -> tuple[List[Dict[str, Any]], int]:
    """Get paginated records with optional filtering."""
    async with get_db() as db:
        # Base query
        base_query = f"SELECT data FROM {table}"
        count_query = f"SELECT COUNT(*) FROM {table}"
        where_clauses = []
        params = []
        
        # Apply filters
        if filters:
            for key, value in filters.items():
                where_clauses.append(f"json_extract(data, '$.{key}') = ?")
                params.append(value)
        
        if where_clauses:
            where_str = " WHERE " + " AND ".join(where_clauses)
            base_query += where_str
            count_query += where_str
        
        # Get total count
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        # Pagination
        offset = (page - 1) * per_page
        base_query += f" ORDER BY json_extract(data, '$.name') LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        cursor = await db.execute(base_query, params)
        rows = await cursor.fetchall()
        
        records = [json.loads(row["data"]) for row in rows]
        return records, total


async def search_services(
    query: str,
    page: int = 1,
    per_page: int = 20
) -> tuple[List[Dict[str, Any]], int]:
    """Full-text search on services."""
    async with get_db() as db:
        # Search FTS table
        search_query = """
            SELECT s.data FROM services s
            JOIN services_fts fts ON s.id = fts.id
            WHERE services_fts MATCH ?
            LIMIT ? OFFSET ?
        """
        
        count_query = """
            SELECT COUNT(*) FROM services s
            JOIN services_fts fts ON s.id = fts.id
            WHERE services_fts MATCH ?
        """
        
        offset = (page - 1) * per_page
        
        cursor = await db.execute(count_query, [query])
        total = (await cursor.fetchone())[0]
        
        cursor = await db.execute(search_query, [query, per_page, offset])
        rows = await cursor.fetchall()
        
        records = [json.loads(row["data"]) for row in rows]
        return records, total


async def get_table_count(table: str) -> int:
    """Get the total number of records in a table."""
    async with get_db() as db:
        cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
        row = await cursor.fetchone()
        return row[0] if row else 0


async def update_sync_metadata(table_name: str, record_count: int):
    """Update sync metadata for a table."""
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO sync_metadata (table_name, last_sync, record_count)
            VALUES (?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(table_name) DO UPDATE SET 
                last_sync=CURRENT_TIMESTAMP,
                record_count=excluded.record_count
            """,
            [table_name, record_count]
        )
        await db.commit()
