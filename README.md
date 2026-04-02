# Mutual Aid NYC HSDirectory

A FastAPI application that syncs data from an [Airtable](https://airtable.com) base and serves it through an [HSDS 3.0](https://docs.openreferral.org/) compliant REST API. Includes a Next.js search frontend with interactive maps.

Built for [Open Referral](https://openreferral.org/) and compatible with the [UK Open Referral (ORUK)](https://openreferraluk.org/) validator.

## Architecture

```
┌─────────────┐      sync every 15min      ┌──────────────┐
│   Airtable  │ ──────────────────────────▶ │  SQLite DB   │
│   (source)  │                             │  (cache)     │
└─────────────┘                             └──────┬───────┘
                                                   │
                                            ┌──────┴───────┐
                                            │   FastAPI     │
                                            │  HSDS 3.0 API │
                                            │  :8080        │
                                            └──────┬───────┘
                                                   │
                                          ┌────────┴────────┐
                                          │   Next.js       │
                                          │  HSDirectory    │
                                          │  :3000          │
                                          └─────────────────┘
```

**How it works:**
1. On startup, the API pulls all records from your Airtable base into a local SQLite database
2. A background task re-syncs every 15 minutes (configurable)
3. The API serves HSDS-formatted data from the fast local cache
4. The frontend queries the API and renders services, organizations, and a map

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for the frontend)
- An **Airtable** account with a base structured for HSDS data
- An **Airtable Personal Access Token** strictly limited to the `data.records:read` scope. **Do not use a full-access API Key.**

---

## Quick Start (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/MutualAidNYC/hsdirectory.git
cd hsdirectory
```

### 2. Set up the API (Python backend)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your Airtable credentials:

```env
# Required — get these from https://airtable.com/create/tokens
AIRTABLE_API_KEY=pat...your_personal_access_token
AIRTABLE_BASE_ID=app...your_base_id

# Optional
SYNC_INTERVAL_MINUTES=15    # How often to re-sync (default: 15)
HOST=0.0.0.0                # Server host (default: 0.0.0.0)
PORT=8080                   # Server port (default: 8080)
```

> **Finding your Base ID:** Open your Airtable base in a browser. The URL will be `https://airtable.com/appXXXXXXXXX/...` — the `appXXXXXXXXX` part is your Base ID.

### 4. Start the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

On first launch, the API will sync all tables from Airtable (this takes 30-60 seconds depending on your data size). You'll see logs like:

```
INFO - Starting HSDS API...
INFO - Database initialized
INFO - Running initial Airtable sync...
INFO - Syncing table: organizations
INFO - Synced 42 records from organizations
...
INFO - Initial sync complete
```

**Verify:** Visit http://localhost:8080/docs to see the interactive API documentation.

### 5. Set up the frontend (Next.js)

```bash
cd hsdirectory

# Install dependencies
npm install

# Configure the API URL
cp .env.local.example .env.local
# Or create manually:
echo "NEXT_PUBLIC_API_URL=http://localhost:8080" > .env.local

# Start the dev server
npm run dev
```

**Verify:** Visit http://localhost:3000 to see the directory frontend.

---

## Airtable Base Setup

Your Airtable base needs tables matching the HSDS schema. The API expects these table names (it maps them by internal Airtable Table IDs defined in `airtable/client.py`):

| Airtable Table | HSDS Entity | Required? |
|---------------|-------------|-----------|
| `organizations` | Organizations | **Yes** |
| `services` | Services | **Yes** |
| `locations` | Locations | **Yes** |
| `addresses` | Addresses | **Yes** |
| `contacts` | Contacts | No |
| `phones` | Phones | No |
| `schedules` | Schedules | No |
| `languages` | Languages | No |
| `taxonomies` | Taxonomies | No |
| `taxonomy_terms` | Taxonomy Terms | No |
| `programs` | Programs | No |
| `service_areas` | Service Areas | No |
| `service_at_location` | Service-Location links | No |
| `funding` | Funding | No |
| `cost_option` | Cost Options | No |
| `required_document` | Required Documents | No |
| `accessibility` | Accessibility | No |

### Connecting to your own Airtable base

The Airtable Table IDs in `airtable/client.py` are specific to the original base. To connect your own base:

1. Open your Airtable base
2. Go to **Help → API documentation** (or visit `https://airtable.com/appYOUR_BASE_ID/api/docs`)
3. Note the Table IDs for each table (they look like `tblXXXXXXXXXX`)
4. Update the `TABLE_IDS` dictionary in `airtable/client.py`:

```python
TABLE_IDS = {
    "organizations": "tblYOUR_ORG_TABLE_ID",
    "services": "tblYOUR_SVC_TABLE_ID",
    "locations": "tblYOUR_LOC_TABLE_ID",
    # ... etc
}
```

### Field mapping

Each Airtable table should have an `id` formula field that generates a consistent HSDS-compatible ID. The mapper in `transform/mapper.py` handles the field name translation between Airtable and HSDS.

Key fields per table:

- **services**: `name`, `description`, `url`, `email`, `status`, `organization` (linked), `locations` (linked)
- **organizations**: `name`, `description`, `url`, `email`, `logo`
- **locations**: `name`, `latitude`, `longitude`, `addresses` (linked)
- **addresses**: `address_1`, `city`, `state_province`, `postal_code`

---

## API Endpoints

### Core (HSDS Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API metadata (version, profile, OpenAPI URL) |
| `GET` | `/services` | Paginated service list (supports `?search=`, `?per_page=`, `?page=`) |
| `GET` | `/services/{id}` | Full service detail with nested relations |

### Additional

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/organizations` | Paginated organization list (supports `?search=`) |
| `GET` | `/organizations/{id}` | Organization detail with services, contacts, locations |
| `GET` | `/organizations/{id}/services` | Services for a specific organization |
| `GET` | `/taxonomies` | List taxonomies |
| `GET` | `/taxonomy_terms` | List taxonomy terms |
| `GET` | `/service_at_locations` | Service-location links |
| `GET` | `/locations/geocoded` | Geocoded locations for map rendering |
| `GET` | `/map/services` | Services with coordinates and filter categories |

### Documentation

| URL | Description |
|-----|-------------|
| `/docs` | Swagger UI (interactive) |
| `/redoc` | ReDoc (reference) |
| `/openapi.json` | OpenAPI 3.0 schema |

---

## Configuration Reference

All configuration is via environment variables (loaded from `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `AIRTABLE_API_KEY` | *(required)* | Airtable Personal Access Token (Must be Read-Only) |
| `AIRTABLE_BASE_ID` | *(required)* | Airtable Base ID (`appXXXXXXXXX`) |
| `SYNC_INTERVAL_MINUTES` | `15` | Minutes between background syncs |
| `HOST` | `0.0.0.0` | API server bind address |
| `PORT` | `8080` | API server port |
| `PUBLISHED_STATUS_VALUE` | `Published` | Only show services with this status (empty = show all) |
| `FILTER_ORGS_WITHOUT_PUBLISHED_SERVICES` | `true` | Hide orgs with no published services |

Frontend environment (in `hsdirectory/.env.local`):

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8080` | URL of the HSDS API |
| `NEXT_PUBLIC_APP_NAME` | `HSDirectory` | Application display name |

---

## Production Deployment

### Option A: Systemd Services (Ubuntu/Debian)

This is the simplest production deployment for a single server.

#### 1. Server setup

```bash
# On your server (Ubuntu 22.04+ recommended)
sudo apt update && sudo apt install -y python3-venv python3-pip nginx nodejs npm

# Create a dedicated, unprivileged system user for security
sudo useradd -r -s /bin/false hsds_user

# Create application directory
sudo mkdir -p /opt/mutualaid
sudo chown $USER:$USER /opt/mutualaid
```

#### 2. Deploy code

```bash
# Clone or copy the code
cd /opt/mutualaid
git clone https://github.com/MutualAidNYC/hsdirectory.git .
cd backend

# Python setup
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Add your Airtable credentials

# Frontend setup
cd hsdirectory
npm install --production
echo "NEXT_PUBLIC_API_URL=https://yourdomain.com" > .env.local
npm run build
```

#### 3. Create systemd services

**API service** (`/etc/systemd/system/manyc-api.service`):

```ini
[Unit]
Description=Mutual Aid NYC API
After=network.target

[Service]
Type=simple
User=hsds_user
WorkingDirectory=/opt/mutualaid/backend
ExecStart=/opt/mutualaid/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8300
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

**Frontend service** (`/etc/systemd/system/manyc-web.service`):

```ini
[Unit]
Description=Mutual Aid NYC Web
After=network.target

[Service]
Type=simple
User=hsds_user
WorkingDirectory=/opt/mutualaid/frontend
ExecStart=/usr/bin/node /opt/mutualaid/frontend/node_modules/.bin/next start -p 3100
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=3100

[Install]
WantedBy=multi-user.target
```

```bash
# Transfer ownership to our secure service user
sudo chown -R hsds_user:hsds_user /opt/mutualaid

sudo systemctl daemon-reload
sudo systemctl enable manyc-api manyc-web
sudo systemctl start manyc-api manyc-web
```

#### 4. Configure Nginx reverse proxy

Create `/etc/nginx/sites-available/hsds`:

```nginx
# Optional but recommended to prevent CPU exhaustion on wildcard SQLite searches
# limit_req_zone $binary_remote_addr zone=hsds_api_limit:10m rate=5r/s;

server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        # limit_req zone=hsds_api_limit burst=10 nodelay;
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API direct access (docs, openapi, services, etc.)
    location ~ ^/(docs|redoc|openapi\.json|services|organizations|taxonomies|taxonomy_terms|service_at_locations|locations|map)(/|$) {
        proxy_pass http://127.0.0.1:8300;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -sf /etc/nginx/sites-available/hsds /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

#### 5. SSL with Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Option B: Docker Compose

Create a `docker-compose.yml` in the project root:

```yaml
version: "3.8"
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    env_file: .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ./hsdirectory
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8080
    depends_on:
      - api
    restart: unless-stopped
```

**API Dockerfile** (project root):

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p data
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Frontend Dockerfile** (`hsdirectory/Dockerfile`):

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
docker compose up -d --build
```

---

## Project Structure

```
at-to-hsds/
├── main.py                    # FastAPI app entry point + lifespan handler
├── config.py                  # Pydantic settings (loads from .env)
├── requirements.txt           # Python dependencies
├── .env.example               # Template for environment variables
│
├── airtable/                  # Airtable integration
│   ├── client.py              # Async HTTP client with pagination + rate limiting
│   └── sync.py                # Background sync loop (Airtable → SQLite)
│
├── db/
│   └── database.py            # SQLite schema + CRUD operations (aiosqlite)
│
├── transform/
│   └── mapper.py              # Airtable fields → HSDS Pydantic models
│
├── models/
│   └── hsds.py                # HSDS 3.0 Pydantic models + response types
│
├── routes/                    # FastAPI route handlers
│   ├── root.py                # GET / (API metadata)
│   ├── services.py            # GET /services, /services/{id}
│   ├── organizations.py       # GET /organizations, /organizations/{id}
│   ├── taxonomies.py          # GET /taxonomies, /taxonomy_terms
│   ├── service_at_locations.py
│   ├── locations.py           # GET /locations/geocoded
│   └── map.py                 # GET /map/services
│
├── hsdirectory/               # Next.js frontend
│   ├── src/
│   │   ├── app/               # App router pages
│   │   │   ├── page.tsx       # Home (category grid)
│   │   │   ├── services/      # Service list + detail + map
│   │   │   └── organizations/ # Org list + detail
│   │   ├── components/        # Reusable UI components
│   │   └── lib/
│   │       └── api.ts         # Typed API client
│   └── package.json
│
├── LICENSE                    # MIT
└── CONTRIBUTING.md
```

---

## Troubleshooting

### API won't start

- **Missing `.env`**: Copy `.env.example` to `.env` and fill in your Airtable credentials
- **Invalid Airtable PAT**: Ensure your token has `data.records:read` scope on the correct base
- **Port conflict**: Change `PORT` in `.env` or use `--port` flag

### No data after startup

- Check the console logs for sync errors
- Verify your `AIRTABLE_BASE_ID` matches your actual base
- Ensure the Table IDs in `airtable/client.py` match your base (see [Connecting to your own base](#connecting-to-your-own-airtable-base))

### Frontend can't reach API

- Ensure the API is running on the URL specified in `NEXT_PUBLIC_API_URL`
- Check CORS — the API allows all origins by default (`allow_origins=["*"]`)
- In production, both services must be accessible to the browser

### Map shows no pins

- Services need linked `locations` with `latitude`/`longitude` fields in Airtable
- The geocoding cache (`geocache.json`) is built on first sync — wait for sync to complete

---

## Standards Compliance

- [HSDS 3.0 Specification](https://docs.openreferral.org/en/latest/hsds/api_reference.html)
- [UK Open Referral Profile](https://openreferraluk.org/)
- [ORUK Validator](https://openreferraluk.org/developers/validator) compatible

## Contributing

We welcome contributions! To get started:
1. **Fork** the repository and clone it to your local machine.
2. **Follow the Quick Start setup** above to get your local development environment running.
3. **Commit** your changes on a feature branch.
4. **Open a Pull Request** against our `main` branch.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines.

## License

[MIT](LICENSE)
