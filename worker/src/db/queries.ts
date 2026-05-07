/**
 * D1 database query helpers.
 *
 * Ports db/database.py operations to D1's prepared statement API.
 * All queries use parameterized statements to prevent SQL injection.
 */

/** Tables that can be queried — safelist to prevent injection in table names. */
const ALLOWED_TABLES = new Set([
  "organizations", "services", "locations", "service_at_locations",
  "taxonomies", "taxonomy_terms", "phones", "addresses", "contacts",
  "schedules", "languages", "programs", "service_areas", "funding",
  "cost_options", "required_documents", "accessibility", "sync_metadata",
]);

function validateTable(table: string): void {
  if (!ALLOWED_TABLES.has(table)) {
    throw new Error(`Invalid table name: ${table}`);
  }
}

/**
 * Upsert a record using INSERT ... ON CONFLICT.
 * Matches the Python upsert_record() pattern with extra_columns.
 */
export async function upsertRecord(
  db: D1Database,
  table: string,
  id: string,
  airtableId: string,
  data: Record<string, unknown>,
  extraColumns: Record<string, string> = {},
): Promise<void> {
  validateTable(table);

  const columns = ["id", "airtable_id", "data"];
  const values: unknown[] = [id, airtableId, JSON.stringify(data)];

  for (const [key, value] of Object.entries(extraColumns)) {
    columns.push(key);
    values.push(value);
  }

  const placeholders = columns.map(() => "?").join(", ");
  const columnStr = columns.join(", ");
  const updates = columns
    .slice(1)
    .map((col) => `${col}=excluded.${col}`)
    .join(", ");

  const query = `INSERT INTO ${table} (${columnStr}) VALUES (${placeholders})
    ON CONFLICT(id) DO UPDATE SET ${updates}, updated_at=datetime('now')`;

  await db.prepare(query).bind(...values).run();
}

/**
 * Get a single record by ID, returning parsed JSON data.
 */
export async function getRecord(
  db: D1Database,
  table: string,
  recordId: string,
): Promise<Record<string, unknown> | null> {
  validateTable(table);
  const result = await db
    .prepare(`SELECT data FROM ${table} WHERE id = ?1 OR airtable_id = ?1`)
    .bind(recordId)
    .first<{ data: string }>();
  if (!result) return null;
  return JSON.parse(result.data);
}

/**
 * Get a record row with all columns (id, airtable_id, data, extra columns).
 */
export async function getRecordRow(
  db: D1Database,
  table: string,
  recordId: string,
): Promise<Record<string, unknown> | null> {
  validateTable(table);
  const result = await db
    .prepare(`SELECT * FROM ${table} WHERE id = ?1 OR airtable_id = ?1`)
    .bind(recordId)
    .first();
  return result as Record<string, unknown> | null;
}

/**
 * Paginated record fetch with optional search and JSON filters.
 * Returns [records, totalCount].
 */
export async function getRecords(
  db: D1Database,
  table: string,
  options: {
    page?: number;
    perPage?: number;
    search?: string;
    searchFields?: string[];
    filters?: Record<string, string>;
    orderBy?: string;
  } = {},
): Promise<[Record<string, unknown>[], number]> {
  validateTable(table);

  const {
    page = 1,
    perPage = 20,
    search,
    searchFields = ["$.name", "$.description"],
    filters,
    orderBy = "json_extract(data, '$.name')",
  } = options;

  const whereClauses: string[] = [];
  const params: unknown[] = [];
  let paramIndex = 1;

  if (filters) {
    for (const [key, value] of Object.entries(filters)) {
      whereClauses.push(`json_extract(data, '$.${key}') = ?${paramIndex}`);
      params.push(value);
      paramIndex++;
    }
  }

  if (search) {
    const searchClauses = searchFields.map((field) => {
      const clause = `json_extract(data, '${field}') LIKE ?${paramIndex}`;
      paramIndex++;
      return clause;
    });
    whereClauses.push(`(${searchClauses.join(" OR ")})`);
    // Push the search param once per field
    for (let i = 0; i < searchFields.length; i++) {
      params.push(`%${search}%`);
    }
  }

  const whereStr = whereClauses.length > 0
    ? ` WHERE ${whereClauses.join(" AND ")}`
    : "";

  // Count query
  const countResult = await db
    .prepare(`SELECT COUNT(*) as cnt FROM ${table}${whereStr}`)
    .bind(...params)
    .first<{ cnt: number }>();
  const total = countResult?.cnt ?? 0;

  // Data query with pagination
  const offset = (page - 1) * perPage;
  params.push(perPage);
  params.push(offset);
  const dataQuery = `SELECT data FROM ${table}${whereStr} ORDER BY ${orderBy} LIMIT ?${paramIndex} OFFSET ?${paramIndex + 1}`;

  const { results } = await db.prepare(dataQuery).bind(...params).all<{ data: string }>();
  const records = results.map((r) => JSON.parse(r.data));
  return [records, total];
}

/**
 * Search services using LIKE on name and description.
 * Replaces FTS5 which is not available in D1.
 */
export async function searchServices(
  db: D1Database,
  query: string,
  options: { page?: number; perPage?: number; statusFilter?: string } = {},
): Promise<[Record<string, unknown>[], number]> {
  const { page = 1, perPage = 20, statusFilter } = options;

  const whereClauses: string[] = [];
  const params: unknown[] = [];
  let paramIndex = 1;

  // Search on name and description
  whereClauses.push(
    `(json_extract(data, '$.name') LIKE ?${paramIndex} OR json_extract(data, '$.description') LIKE ?${paramIndex + 1})`,
  );
  params.push(`%${query}%`, `%${query}%`);
  paramIndex += 2;

  if (statusFilter) {
    whereClauses.push(`json_extract(data, '$.status') = ?${paramIndex}`);
    params.push(statusFilter);
    paramIndex++;
  }

  const whereStr = ` WHERE ${whereClauses.join(" AND ")}`;

  const countResult = await db
    .prepare(`SELECT COUNT(*) as cnt FROM services${whereStr}`)
    .bind(...params)
    .first<{ cnt: number }>();
  const total = countResult?.cnt ?? 0;

  const offset = (page - 1) * perPage;
  params.push(perPage, offset);
  const dataQuery = `SELECT id, airtable_id, organization_id, data FROM services${whereStr} ORDER BY json_extract(data, '$.name') LIMIT ?${paramIndex} OFFSET ?${paramIndex + 1}`;

  const { results } = await db.prepare(dataQuery).bind(...params).all<{
    id: string;
    airtable_id: string;
    organization_id: string;
    data: string;
  }>();

  const records = results.map((r) => ({
    ...JSON.parse(r.data),
    _id: r.id,
    _airtable_id: r.airtable_id,
    _organization_id: r.organization_id,
  }));

  return [records, total];
}

/** Get total record count for a table. */
export async function getTableCount(db: D1Database, table: string): Promise<number> {
  validateTable(table);
  const result = await db
    .prepare(`SELECT COUNT(*) as cnt FROM ${table}`)
    .first<{ cnt: number }>();
  return result?.cnt ?? 0;
}

/** Update sync metadata after a sync run. */
export async function updateSyncMetadata(
  db: D1Database,
  tableName: string,
  recordCount: number,
): Promise<void> {
  await db
    .prepare(
      `INSERT INTO sync_metadata (table_name, last_sync, record_count)
       VALUES (?1, datetime('now'), ?2)
       ON CONFLICT(table_name) DO UPDATE SET
         last_sync=datetime('now'),
         record_count=excluded.record_count`,
    )
    .bind(tableName, recordCount)
    .run();
}
