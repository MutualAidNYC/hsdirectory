/**
 * HSDS API Worker — Main entry point.
 *
 * Hono app with all route groups, CORS, scheduled sync, and MCP server.
 */
import { Hono } from "hono";
import { cors } from "hono/cors";
import type { Env } from "./env";

// Route modules
import { root } from "./routes/root";
import { services } from "./routes/services";
import { organizations } from "./routes/organizations";
import { taxonomies, taxonomyTerms } from "./routes/taxonomies";
import { locations } from "./routes/locations";
import { map } from "./routes/map";
import { chat } from "./chat/handler";

// Sync
import { runFullSync } from "./sync/sync";

// MCP
import { DirectoryMcpAgent } from "./mcp/server";
import { routeAgentRequest } from "agents";

const app = new Hono<{ Bindings: Env }>();

// ============================================================================
// Middleware
// ============================================================================

app.use(
  "*",
  cors({
    origin: "*",
    allowMethods: ["GET", "POST", "OPTIONS"],
    allowHeaders: ["Content-Type", "Accept"],
  }),
);

// ============================================================================
// Routes
// ============================================================================

app.route("/", root);
app.route("/services", services);
app.route("/organizations", organizations);
app.route("/taxonomies", taxonomies);
app.route("/taxonomy_terms", taxonomyTerms);
app.route("/locations", locations);
app.route("/map", map);
app.route("/api/chat", chat);

// ============================================================================
// MCP endpoint — Streamable HTTP at /mcp
// ============================================================================

app.all("/mcp", async (c) => {
  return (routeAgentRequest(c.req.raw, c.env) as unknown) as Response;
});
app.all("/mcp/*", async (c) => {
  return (routeAgentRequest(c.req.raw, c.env) as unknown) as Response;
});

// ============================================================================
// Health / Status endpoints
// ============================================================================

app.get("/health", async (c) => {
  try {
    const result = await c.env.DB.prepare("SELECT COUNT(*) as cnt FROM services").first<{ cnt: number }>();
    return c.json({
      status: "ok",
      services: result?.cnt ?? 0,
      timestamp: new Date().toISOString(),
    });
  } catch {
    return c.json({ status: "error", message: "Database unavailable" }, 503);
  }
});

app.get("/sync/status", async (c) => {
  const { results } = await c.env.DB.prepare("SELECT * FROM sync_metadata ORDER BY table_name").all();
  return c.json({ sync_metadata: results });
});

// ============================================================================
// Sync & Admin endpoints (protected by SYNC_SECRET)
// ============================================================================

/** Guard: require SYNC_SECRET bearer token for admin endpoints. */
function requireSyncAuth(c: { req: { header: (name: string) => string | undefined }; env: Env; json: (body: unknown, status?: number) => Response }): Response | null {
  const secret = c.env.SYNC_SECRET;
  if (!secret) return null; // No secret configured → open (dev mode)
  const auth = c.req.header("Authorization");
  if (auth !== `Bearer ${secret}`) {
    return c.json({ error: "Unauthorized" }, 401);
  }
  return null;
}

// Manual sync trigger (uses waitUntil to avoid CPU timeout)
app.post("/sync/trigger", async (c) => {
  const denied = requireSyncAuth(c);
  if (denied) return denied;
  const env = c.env;
  c.executionCtx.waitUntil(
    runFullSync(env).then((results) => {
      console.log("Manual sync completed:", JSON.stringify(results));
    }),
  );
  return c.json({ status: "sync_started", message: "Sync running in background. Check /sync/status for progress." });
});

// Sync a single table (for incremental seeding)
app.post("/sync/table/:table", async (c) => {
  const denied = requireSyncAuth(c);
  if (denied) return denied;
  const tableName = c.req.param("table");
  const env = c.env;
  try {
    const { syncSingleTable } = await import("./sync/sync");
    const count = await syncSingleTable(env, tableName);
    return c.json({ status: "completed", table: tableName, records: count });
  } catch (err) {
    return c.json({ status: "error", table: tableName, error: String(err) }, 500);
  }
});

// Manual seed geocache from JSON body (fallback/import)
app.post("/sync/geocache", async (c) => {
  const denied = requireSyncAuth(c);
  if (denied) return denied;
  const { entries } = (await c.req.json()) as {
    entries: Record<string, { latitude: number; longitude: number; formatted_address?: string; geocoded_at?: string }>;
  };
  if (!entries) return c.json({ error: "Missing entries" }, 400);

  const db = c.env.DB;
  let count = 0;
  for (const [addressId, geo] of Object.entries(entries)) {
    await db
      .prepare(
        "INSERT OR REPLACE INTO geocache (address_id, latitude, longitude, formatted_address, geocoded_at) VALUES (?1, ?2, ?3, ?4, ?5)",
      )
      .bind(addressId, geo.latitude, geo.longitude, geo.formatted_address || null, geo.geocoded_at || null)
      .run();
    count++;
  }
  return c.json({ status: "completed", records: count });
});

/**
 * Google Geocoding API — geocode all addresses not yet in geocache.
 * Runs async via waitUntil to avoid CPU timeout on free plan.
 */
app.post("/sync/geocode", async (c) => {
  const denied = requireSyncAuth(c);
  if (denied) return denied;
  const apiKey = c.env.GOOGLE_GEOCODING_API_KEY;
  if (!apiKey) return c.json({ error: "GOOGLE_GEOCODING_API_KEY not configured" }, 400);

  const db = c.env.DB;

  // Find addresses not yet geocoded
  const { results: addresses } = await db
    .prepare(
      `SELECT a.id, a.data FROM addresses a
       LEFT JOIN geocache g ON a.id = g.address_id
       WHERE g.address_id IS NULL`,
    )
    .all<{ id: string; data: string }>();

  if (!addresses || addresses.length === 0) {
    return c.json({ status: "completed", message: "All addresses already geocoded", new: 0 });
  }

  // Run geocoding in background (free plan allows 30s CPU in waitUntil)
  c.executionCtx.waitUntil(
    (async () => {
      let geocoded = 0;
      let failed = 0;

      for (const row of addresses) {
        const fields = JSON.parse(row.data) as Record<string, unknown>;
        const parts = [
          fields.address_1,
          fields.city,
          fields.state_province,
          fields.postal_code,
        ].filter(Boolean).map(String);
        const query = parts.join(", ");
        if (!query.trim()) { failed++; continue; }

        try {
          const url = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(query)}&key=${apiKey}`;
          const resp = await fetch(url);
          const data = (await resp.json()) as {
            status: string;
            results: Array<{ geometry: { location: { lat: number; lng: number } }; formatted_address: string }>;
          };

          if (data.status === "OK" && data.results.length > 0) {
            const loc = data.results[0].geometry.location;

            // NYC proximity check: reject results > 200 miles from NYC
            const R = 3958.8;
            const dLat = (loc.lat - 40.7128) * Math.PI / 180;
            const dLon = (loc.lng - (-74.006)) * Math.PI / 180;
            const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(40.7128 * Math.PI / 180) * Math.cos(loc.lat * Math.PI / 180) *
              Math.sin(dLon / 2) ** 2;
            const dist = R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

            if (dist > 200) {
              console.log(`Rejected ${row.id}: ${query.slice(0, 50)} (${dist.toFixed(0)}mi from NYC)`);
              failed++;
              continue;
            }

            await db
              .prepare(
                "INSERT OR REPLACE INTO geocache (address_id, latitude, longitude, formatted_address, geocoded_at) VALUES (?1, ?2, ?3, ?4, ?5)",
              )
              .bind(row.id, loc.lat, loc.lng, data.results[0].formatted_address, new Date().toISOString())
              .run();
            geocoded++;
          } else {
            console.log(`No result for ${row.id}: ${query.slice(0, 50)} (${data.status})`);
            failed++;
          }
        } catch (err) {
          console.error(`Geocode error for ${row.id}:`, err);
          failed++;
        }
      }
      console.log(`Geocoding complete: ${geocoded} geocoded, ${failed} failed out of ${addresses.length}`);
    })(),
  );

  return c.json({
    status: "geocoding_started",
    addresses_to_process: addresses.length,
    message: "Running in background. Check GET /sync/geocache for progress.",
  });
});

// Geocache stats
app.get("/sync/geocache", async (c) => {
  const [cacheResult, addrResult] = await Promise.all([
    c.env.DB.prepare("SELECT COUNT(*) as cnt FROM geocache").first<{ cnt: number }>(),
    c.env.DB.prepare("SELECT COUNT(*) as cnt FROM addresses").first<{ cnt: number }>(),
  ]);
  return c.json({
    geocache_entries: cacheResult?.cnt ?? 0,
    total_addresses: addrResult?.cnt ?? 0,
    coverage: addrResult?.cnt ? `${Math.round(((cacheResult?.cnt ?? 0) / addrResult.cnt) * 100)}%` : "0%",
  });
});

// ============================================================================
// Export
// ============================================================================

export default {
  fetch: app.fetch,

  /** Scheduled handler — runs Airtable sync on cron trigger. */
  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    ctx.waitUntil(
      runFullSync(env).then((results) => {
        console.log("Scheduled sync completed:", JSON.stringify(results));
      }),
    );
  },
};

// Export MCP Agent class for Durable Object binding
export { DirectoryMcpAgent };
