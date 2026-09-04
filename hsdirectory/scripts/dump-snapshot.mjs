/**
 * Dump the dataset from a locally running API into src/data/snapshot.json.
 *
 * Usage, from hsdirectory/, with the API up:
 *   node scripts/dump-snapshot.mjs [http://localhost:8080]
 *
 * Scaffolding to provide a temporary snapshot for the frontend while we build out the deploy solution.
 * Note: This is not a long-term solution, and will be replaced with a proper deployed api.
 */
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.argv[2] || process.env.API_URL || "http://localhost:8080";
const OUT = join(dirname(fileURLToPath(import.meta.url)), "..", "src", "data", "snapshot.json");
const CONCURRENCY = 3;

async function get(path) {
  const res = await fetch(`${BASE}${path}`, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${path}`);
  return res.json();
}

/** Walk a paginated endpoint and return every item. */
async function getAll(path, perPage = 100) {
  const out = [];
  for (let page = 1; ; page++) {
    const sep = path.includes("?") ? "&" : "?";
    const res = await get(`${path}${sep}page=${page}&per_page=${perPage}`);
    out.push(...(res.contents ?? []));
    if (res.last_page || !res.contents?.length) break;
  }
  return out;
}

/** Bounded concurrency: the org endpoints fan out to Airtable, which is rate limited. */
async function mapLimit(items, fn, label) {
  const out = new Array(items.length);
  let i = 0;
  let done = 0;
  await Promise.all(
    Array.from({ length: CONCURRENCY }, async () => {
      while (i < items.length) {
        const idx = i++;
        out[idx] = await fn(items[idx]);
        if (++done % 25 === 0 || done === items.length) {
          process.stdout.write(`\r  ${label}: ${done}/${items.length}`);
        }
      }
    })
  );
  process.stdout.write("\n");
  return out;
}

console.log(`Dumping from ${BASE}`);

console.log("- /map/services");
const mapServices = await get("/map/services");

console.log("- /services");
const services = await getAll("/services");
const serviceDetail = {};
for (const [n, detail] of (
  await mapLimit(services, (s) => get(`/services/${s.id}`).catch(() => null), "service detail")
).entries()) {
  if (detail) serviceDetail[services[n].id] = detail;
}

console.log("- /organizations");
const organizations = await getAll("/organizations");
const organizationDetail = {};
const organizationServices = {};
await mapLimit(
  organizations,
  async (o) => {
    const [detail, svcs] = await Promise.all([
      get(`/organizations/${o.id}`).catch(() => null),
      get(`/organizations/${o.id}/services?page=1&per_page=100`).catch(() => null),
    ]);
    if (detail) organizationDetail[o.id] = detail;
    if (svcs) organizationServices[o.id] = svcs.contents ?? [];
  },
  "organization detail"
);

const snapshot = {
  generatedAt: new Date().toISOString(),
  source: BASE,
  mapServices,
  services,
  serviceDetail,
  organizations,
  organizationDetail,
  organizationServices,
};

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify(snapshot));
const mb = (Buffer.byteLength(JSON.stringify(snapshot)) / 1e6).toFixed(2);
console.log(
  `\nWrote ${OUT}\n  ${services.length} services, ${organizations.length} organizations, ${mb} MB`
);
