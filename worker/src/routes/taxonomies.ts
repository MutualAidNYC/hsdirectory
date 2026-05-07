/**
 * Taxonomies and Taxonomy Terms API endpoints.
 *
 * Ports routes/taxonomies.py — now serving from D1 cache.
 */
import { Hono } from "hono";
import type { Env } from "../env";
import { mapTaxonomy, mapTaxonomyTerm, paginate } from "../mapper";

const taxonomies = new Hono<{ Bindings: Env }>();

// ============================================================================
// Taxonomies
// ============================================================================

taxonomies.get("/", async (c) => {
  const db = c.env.DB;
  const page = Math.max(1, Number(c.req.query("page") ?? 1));
  const perPage = Math.min(100, Math.max(1, Number(c.req.query("per_page") ?? 20)));
  const search = c.req.query("search");

  let query = "SELECT id, data FROM taxonomies";
  const params: unknown[] = [];
  let paramIndex = 1;

  if (search) {
    query += ` WHERE (json_extract(data, '$.name') LIKE ?${paramIndex} OR json_extract(data, '$.description') LIKE ?${paramIndex + 1})`;
    params.push(`%${search}%`, `%${search}%`);
    paramIndex += 2;
  }

  const { results } = await db.prepare(query).bind(...params).all<{ id: string; data: string }>();

  const items = results.map((row) => {
    const data = JSON.parse(row.data) as Record<string, unknown>;
    data.id = row.id;
    return mapTaxonomy(data);
  });

  const start = (page - 1) * perPage;
  const pageItems = items.slice(start, start + perPage);
  return c.json(paginate(pageItems, items.length, page, perPage));
});

taxonomies.get("/:id", async (c) => {
  const db = c.env.DB;
  const taxId = c.req.param("id");

  const row = await db
    .prepare("SELECT id, data FROM taxonomies WHERE id = ?1 OR airtable_id = ?1")
    .bind(taxId)
    .first<{ id: string; data: string }>();

  if (!row) return c.json({ detail: "Taxonomy not found" }, 404);

  const data = JSON.parse(row.data) as Record<string, unknown>;
  data.id = row.id;
  return c.json(mapTaxonomy(data));
});

// ============================================================================
// Taxonomy Terms — mounted separately at /taxonomy_terms
// ============================================================================

const taxonomyTerms = new Hono<{ Bindings: Env }>();

taxonomyTerms.get("/", async (c) => {
  const db = c.env.DB;
  const page = Math.max(1, Number(c.req.query("page") ?? 1));
  const perPage = Math.min(100, Math.max(1, Number(c.req.query("per_page") ?? 20)));
  const search = c.req.query("search");
  const taxonomyId = c.req.query("taxonomy_id");

  const whereClauses: string[] = [];
  const params: unknown[] = [];
  let paramIndex = 1;

  if (taxonomyId) {
    whereClauses.push(`taxonomy_id = ?${paramIndex}`);
    params.push(taxonomyId);
    paramIndex++;
  }

  if (search) {
    whereClauses.push(
      `(json_extract(data, '$.name') LIKE ?${paramIndex} OR json_extract(data, '$.description') LIKE ?${paramIndex + 1})`,
    );
    params.push(`%${search}%`, `%${search}%`);
    paramIndex += 2;
  }

  const whereStr = whereClauses.length > 0 ? ` WHERE ${whereClauses.join(" AND ")}` : "";
  const { results } = await db
    .prepare(`SELECT id, taxonomy_id, data FROM taxonomy_terms${whereStr}`)
    .bind(...params)
    .all<{ id: string; taxonomy_id: string; data: string }>();

  const items = [];
  for (const row of results) {
    const data = JSON.parse(row.data) as Record<string, unknown>;
    data.id = row.id;

    // Look up taxonomy detail
    let taxonomy;
    if (row.taxonomy_id) {
      const taxRow = await db
        .prepare("SELECT data FROM taxonomies WHERE id = ?1 OR airtable_id = ?1")
        .bind(row.taxonomy_id)
        .first<{ data: string }>();
      if (taxRow) {
        taxonomy = mapTaxonomy(JSON.parse(taxRow.data) as Record<string, unknown>);
      }
    }

    items.push(mapTaxonomyTerm(data, taxonomy));
  }

  const start = (page - 1) * perPage;
  const pageItems = items.slice(start, start + perPage);
  return c.json(paginate(pageItems, items.length, page, perPage));
});

taxonomyTerms.get("/:id", async (c) => {
  const db = c.env.DB;
  const termId = c.req.param("id");

  const row = await db
    .prepare("SELECT id, taxonomy_id, data FROM taxonomy_terms WHERE id = ?1 OR airtable_id = ?1")
    .bind(termId)
    .first<{ id: string; taxonomy_id: string; data: string }>();

  if (!row) return c.json({ detail: "Taxonomy term not found" }, 404);

  const data = JSON.parse(row.data) as Record<string, unknown>;
  data.id = row.id;

  let taxonomy;
  if (row.taxonomy_id) {
    const taxRow = await db
      .prepare("SELECT data FROM taxonomies WHERE id = ?1 OR airtable_id = ?1")
      .bind(row.taxonomy_id)
      .first<{ data: string }>();
    if (taxRow) {
      taxonomy = mapTaxonomy(JSON.parse(taxRow.data) as Record<string, unknown>);
    }
  }

  return c.json(mapTaxonomyTerm(data, taxonomy));
});

export { taxonomies, taxonomyTerms };
