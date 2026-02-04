# Airtable to HSDS API

A FastAPI application that bridges Airtable data to the [Human Services Data Specification (HSDS)](https://docs.openreferral.org/) API format, compliant with [UK Open Referral](https://openreferraluk.org/) standards.

## Features

- **HSDS 3.0 Compliant** - Implements the full HSDS specification
- **UK Open Referral (ORUK) Profile** - Meets ORUK validation requirements
- **Airtable Integration** - Syncs data from Airtable bases
- **Background Sync** - Automatic periodic data synchronization
- **SQLite Cache** - Fast local caching for improved performance
- **Interactive Docs** - Auto-generated Swagger UI at `/docs`

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/sarapis/at-to-hsds.git
cd at-to-hsds
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

Copy the example environment file and add your Airtable credentials:

```bash
cp .env.example .env
```

Edit `.env` with your values:
- `AIRTABLE_API_KEY` - Your Airtable Personal Access Token
- `AIRTABLE_BASE_ID` - Your Airtable Base ID

### 3. Run

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

Access:
- API: http://localhost:8080/
- Docs: http://localhost:8080/docs
- OpenAPI: http://localhost:8080/openapi.json

## API Endpoints

### Required (HSDS Core)
| Endpoint | Description |
|----------|-------------|
| `GET /` | API metadata (version, profile) |
| `GET /services` | List services with pagination |
| `GET /services/{id}` | Get service details |

### Optional
| Endpoint | Description |
|----------|-------------|
| `GET /organizations` | List organizations |
| `GET /organizations/{id}` | Get organization details |
| `GET /taxonomies` | List taxonomies |
| `GET /taxonomy_terms` | List taxonomy terms |
| `GET /service_at_locations` | Service-location links |

## Airtable Schema

Your Airtable base should include tables matching HSDS entities:
- organizations
- services
- locations
- addresses
- phones
- contacts
- taxonomy_terms
- And other HSDS entities as needed

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `AIRTABLE_API_KEY` | (required) | Airtable Personal Access Token |
| `AIRTABLE_BASE_ID` | (required) | Airtable Base ID |
| `SYNC_INTERVAL_MINUTES` | 15 | Background sync interval |
| `HOST` | 0.0.0.0 | Server host |
| `PORT` | 8080 | Server port |

## License

MIT License

## Links

- [HSDS Specification](https://docs.openreferral.org/)
- [UK Open Referral](https://openreferraluk.org/)
- [ORUK Validator](https://openreferraluk.org/developers/validator)
