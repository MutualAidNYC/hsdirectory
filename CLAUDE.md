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
- **Hosting**: Hetzner (see Antigravity Hub for connection details)

## Repositories & URLs

- **API**: `https://github.com/MutualAidNYC/hsdirectory` (Live: `https://services.wegov.nyc/api/`)
- **Frontend**: `https://github.com/MutualAidNYC/hsdirectory` (Live: `https://services.wegov.nyc`)

## Environment Variables (Critical)

- `NEXT_PUBLIC_API_URL`: Must be set at **build time** for the browser bundles (e.g. `https://services.wegov.nyc/api`).
- `INTERNAL_API_URL`: Must be set at **run time** in the systemd service environment. This prevents SSR loopback timeouts by routing server-side fetches directly to the backend instead of through the public proxy.

## Development & Deployment Process

1. **Develop Locally** 
   - Start the local API server and test sync logic
2. **Build for Production (Frontend)**
   - Run with inline env override (do NOT edit `.env.local`):
     ```bash
     NEXT_PUBLIC_API_URL=https://services.wegov.nyc/api npm run build
     ```
3. **Deploy to Production**
   - Tar the full `.next` build output and deploy to the production server
   - See Antigravity Hub workspace for host details and deploy target paths
   - Restart the frontend systemd service after deploying
4. **Push to GitHub**
   - Commit code to ensure source control is up to date

## Gotchas

- **Next.js Chunking**: Never deploy individual compiled `page.js` files. Turbopack generates tightly-coupled hashed chunks. You must deploy the full `.next` build.
- **Nginx Proxy Pass**: The Nginx config must strip the `/api/` prefix when proxying to FastAPI (trailing slash on `proxy_pass` directive).
- **Airtable Syncs**: Requires Airtable HSDS Schema base ID for fetching data. Restarting the API service triggers an expensive full sync.

