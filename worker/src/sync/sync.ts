/**
 * Airtable → D1 sync logic.
 *
 * Ports airtable/sync.py. Called by the scheduled handler on cron trigger.
 * Each table sync is isolated — failures in one table don't block others.
 */
import { listRecords } from "./airtable-client";
import { upsertRecord, updateSyncMetadata } from "../db/queries";
import type { Env } from "../env";

/**
 * Mapping: local table → Airtable table name + extra column extractors.
 * From airtable/sync.py TABLE_MAPPING.
 */
interface TableConfig {
  airtableName: string;
  extraColumns?: (fields: Record<string, unknown>, recordId: string) => Record<string, string>;
}

const TABLE_MAPPING: Record<string, TableConfig> = {
  organizations: { airtableName: "organizations" },
  services: {
    airtableName: "services",
    extraColumns: (fields): Record<string, string> => {
      const orgs = (fields.organizations || fields.organization) as string[] | undefined;
      return orgs && orgs.length > 0 ? { organization_id: orgs[0] } : {};
    },
  },
  locations: { airtableName: "locations" },
  addresses: { airtableName: "addresses" },
  contacts: { airtableName: "contacts" },
  phones: { airtableName: "phones" },
  schedules: { airtableName: "schedules" },
  languages: { airtableName: "languages" },
  accessibility: { airtableName: "accessibility" },
  service_at_locations: {
    airtableName: "service_at_location",
    extraColumns: (fields): Record<string, string> => {
      const extras: Record<string, string> = {};
      const services = fields.services as string[] | undefined;
      const locations = fields.locations as string[] | undefined;
      if (services && services.length > 0) extras.service_id = services[0];
      if (locations && locations.length > 0) extras.location_id = locations[0];
      return extras;
    },
  },
  taxonomies: { airtableName: "taxonomies" },
  taxonomy_terms: {
    airtableName: "taxonomy_terms",
    extraColumns: (fields): Record<string, string> => {
      const taxonomy = fields.taxonomy as string[] | undefined;
      return taxonomy && taxonomy.length > 0 ? { taxonomy_id: taxonomy[0] } : {};
    },
  },
  programs: { airtableName: "programs" },
  service_areas: { airtableName: "service_areas" },
  funding: { airtableName: "funding" },
  cost_options: { airtableName: "cost_option" },
  required_documents: { airtableName: "required_document" },
};

/**
 * Sync a single Airtable table to D1.
 * Returns number of records synced.
 */
async function syncTable(
  env: Env,
  localTable: string,
  config: TableConfig,
): Promise<number> {
  const records = await listRecords(
    env.AIRTABLE_API_KEY,
    env.AIRTABLE_BASE_ID,
    config.airtableName,
  );

  let count = 0;
  for (const record of records) {
    const id = record.fields.id as string || record.id;
    const extraColumns = config.extraColumns
      ? config.extraColumns(record.fields, record.id)
      : {};

    await upsertRecord(
      env.DB,
      localTable,
      id,
      record.id,
      record.fields,
      extraColumns,
    );
    count++;
  }

  await updateSyncMetadata(env.DB, localTable, count);
  return count;
}

/**
 * Run a full sync of all tables.
 * Called by the scheduled handler.
 */
export async function runFullSync(env: Env): Promise<Record<string, number>> {
  const results: Record<string, number> = {};

  for (const [localTable, config] of Object.entries(TABLE_MAPPING)) {
    try {
      const count = await syncTable(env, localTable, config);
      results[localTable] = count;
      console.log(`Synced ${localTable}: ${count} records`);
    } catch (err) {
      console.error(`Failed to sync ${localTable}:`, err);
      results[localTable] = -1;
    }
  }

  return results;
}

/**
 * Sync a single table by name.
 * Used by the /sync/table/:table endpoint for incremental seeding.
 */
export async function syncSingleTable(env: Env, tableName: string): Promise<number> {
  const config = TABLE_MAPPING[tableName];
  if (!config) {
    throw new Error(`Unknown table: ${tableName}. Valid tables: ${Object.keys(TABLE_MAPPING).join(", ")}`);
  }
  return syncTable(env, tableName, config);
}
