# ATtoOR

> Airtable-to-Open Referral — FastAPI HSDS 3.0 backend with SQLite cache

## Live Project Data

```
get_workspace_detail("ATtoOR")   → services, URLs, repos, recent commits
list_tasks(workspace="ATtoOR")   → open tasks
search_knowledge(topic="ATtoOR") → hsds_integration KI
```

## Tech Stack

- **Backend**: FastAPI (Python)
- **Data**: SQLite caching layer syncing from Airtable
- **Frontend**: Next.js (App Router, Server Components)
- **Hosting**: Hetzner utilities (178.156.245.46) - API on port 8300, Frontend on port 3100

## Repositories & URLs

- **API**: `https://github.com/MutualAidNYC/hsdirectory` (Live: `https://services.wegov.nyc/api/`)
- **Frontend**: `https://github.com/MutualAidNYC/hsdirectory` (Live: `https://services.wegov.nyc`)

## Environment Variables (Critical)

- `NEXT_PUBLIC_API_URL`: Must be set at **build time** for the browser bundles (e.g. `https://services.wegov.nyc/api`).
- `INTERNAL_API_URL`: Must be set at **run time** (e.g. in systemd `manyc-web.service`) to `http://127.0.0.1:8300`. This prevents SSR loopback timeouts by routing server-side fetches directly to FastAPI instead of through the public internet.

## Development & Deployment Process

> [!WARNING]
> The production server does **not** have a git repository initialized. Deployment is done via `scp`.

1. **Develop Locally** 
   - Start the local API server and test sync logic
2. **Build for Production (Frontend)**
   - Run with inline env override (do NOT edit `.env.local`):
     ```bash
     NEXT_PUBLIC_API_URL=https://services.wegov.nyc/api npm run build
     ```
3. **Deploy to Production via SCP**
   - Tar the build output: `tar -czf next-build.tar.gz .next/server/ .next/static/ .next/BUILD_ID ...`
   - `scp` the tarball to `root@178.156.245.46:/opt/mutualaid/frontend`
   - Extract and `systemctl restart manyc-web.service`
4. **Push to GitHub**
   - Commit code to ensure source control is up to date

## Gotchas

- **Next.js Chunking**: Never `scp` individual compiled `page.js` files. Turbopack generates tightly-coupled hashed chunks. You must deploy the full `.next` build.
- **Nginx Proxy Pass**: The Nginx config must strip the `/api/` prefix when proxying to FastAPI. Use `proxy_pass http://172.17.0.1:8300/;` (note the trailing slash).
- **Airtable Syncs**: Requires Airtable HSDS Schema base ID for fetching data. Restarting `manyc-api` triggers an expensive full sync.
