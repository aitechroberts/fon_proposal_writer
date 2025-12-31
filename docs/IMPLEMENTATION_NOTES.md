# FON Advisors Proposal Writer - Implementation Notes

> **Version 2.0** - December 2025

This document describes all changes made to implement the FON Advisors feature enhancements.

---

## Summary of Changes

### 1. Requirement ID Renumbering (1-N)
- **File**: `backend/pipeline/tasks.py`
- **Function**: `generate_and_upload_task()`
- Requirements are renumbered to sequential 1-N just before export
- Replaces LLM-generated IDs with clean sequential numbers

```python
# Renumber requirement IDs to sequential 1-N
for idx, req in enumerate(requirements, start=1):
    req["id"] = str(idx)
```

### 2. Dual Proposal Generation (Cited + Standard)
- **Files**: 
  - `backend/pipeline/tasks.py` - Generates both versions
  - `backend/src/proposal/export_word.py` - Citation stripping function
  - `backend/api/models.py` - Updated response models

**Citation Stripping**:
```python
def strip_citations(text: str) -> str:
    """Remove all bracketed citations from text."""
    if not text:
        return text
    cleaned = re.sub(r'\[[^\]]*\]', '', text)
    cleaned = re.sub(r'  +', ' ', cleaned)
    return cleaned.strip()
```

**Output Files**:
- `{name}_proposal_cited.docx` - Original with citations in [brackets]
- `{name}_proposal.docx` - Citations removed (for final submission)

### 3. PostgreSQL Database Integration

**Architecture Decision**: Database is a **job history store**, not real-time tracker:
- In-memory `jobs_db` dict - Tracks in-progress jobs
- PostgreSQL - Stores completed jobs ONLY after successful blob upload
- Write trigger - Single insert at end of pipeline when status=COMPLETED

**New Files**:
- `backend/db/__init__.py` - Package exports
- `backend/db/database.py` - Async connection pool
- `backend/db/models.py` - SQLAlchemy Job model

**Connection Pooling Configuration**:
```python
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_size=5,         # Adequate for ~15 users
    max_overflow=2,      # Allow 2 extra in bursts
    pool_pre_ping=True,  # Prevents stale connections
)
```

**Database Schema**:
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key (job_id) |
| job_name | VARCHAR(255) | Required job name for tracking |
| created_at | TIMESTAMP | Job creation time |
| completed_at | TIMESTAMP | Completion time |
| requirements_sas_url | TEXT | Compliance matrix URL |
| clean_proposal_sas_url | TEXT | Standard proposal URL |
| cited_proposal_sas_url | TEXT | Cited proposal URL |
| zip_sas_url | TEXT | ZIP bundle URL |
| file_count | INT | Number of requirements extracted |

**Indexes**:
```sql
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_job_name ON jobs(job_name);
```

### 4. Jobs List API Endpoint

**Endpoint**: `GET /api/v1/jobs`

**Query Parameters**:
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
- `search` (string): Search by job name
- `sort_by` (string): Sort field (default: created_at)
- `sort_order` (string): asc or desc (default: desc)

**Response**:
```json
{
  "jobs": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "total_pages": 5
}
```

**All queries are parameterized** to prevent SQL injection.

### 5. FON Advisors Branding

**Brand Colors**:
- Primary Blue: `#3332FF`
- Charcoal: `#323332`

**Files Updated**:
- `frontend-next/theme/theme.ts` - Mantine theme colors
- `frontend-next/app/globals.css` - CSS variables

### 6. Navigation and Page Structure

**New Components**:
- `frontend-next/components/Navigation.tsx` - Top navbar
- `frontend-next/components/JobsTable.tsx` - Paginated jobs table

**Page Structure**:
```
frontend-next/app/
├── layout.tsx          # Includes Navigation
├── page.tsx            # Redirects to /submit
├── submit/
│   └── page.tsx        # Job submission form (job name required)
└── jobs/
    └── page.tsx        # Previous Jobs table
```

### 7. Required Job Name

Job name is now **required** in the Submit Jobs form:
- Frontend validates that job name is provided before submission
- Job name is used for output filenames and tracking
- Shows alert message if job name is missing

---

## Configuration Requirements

### Environment Variables

```bash
# PostgreSQL Database (local Docker Compose)
DATABASE_URL=postgresql://fon:fon_secret@postgres:5432/fon_proposals

# PostgreSQL Database (Azure production)
# DATABASE_URL=postgresql://fonadmin:PASSWORD@proposal-db-fon.postgres.database.azure.com:5432/fon_proposals?sslmode=require

# CORS - Comma-separated list of allowed origins (or "*" for development only)
CORS_ORIGINS=https://proposal-frontend.thankfulflower-cf94ed15.eastus.azurecontainerapps.io

# Optional Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=xxx

# Existing Azure config
AZURE_API_KEY=xxx
AZURE_API_BASE=xxx
AZURE_OPENAI_DEPLOYMENT=xxx
AZURE_STORAGE_CONNECTION_STRING=xxx
```

### Docker Compose

Added PostgreSQL service:

```yaml
postgres:
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: fon
    POSTGRES_PASSWORD: fon_secret
    POSTGRES_DB: fon_proposals
  volumes:
    - postgres_data:/var/lib/postgresql/data
  ports:
    - "5432:5432"
```

---

## CORS Configuration

CORS is configured at **two levels** for defense in depth:

### 1. Application-Level CORS (FastAPI)

The backend uses the `CORS_ORIGINS` environment variable:

```bash
# Production - only allow your frontend domain
CORS_ORIGINS=https://proposal-frontend.thankfulflower-cf94ed15.eastus.azurecontainerapps.io

# Development - allow localhost
CORS_ORIGINS=http://localhost:3000,http://frontend:3000

# NEVER use "*" in production
```

### 2. Azure Container Apps Ingress CORS

Configure CORS at the Azure Container Apps level for additional security:

```bash
# Get your frontend URL first
FRONTEND_URL=$(az containerapp show \
  --name proposal-frontend \
  --resource-group proposal-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)

# Configure CORS on the backend Container App
az containerapp ingress cors update \
  --name proposal-backend \
  --resource-group proposal-rg \
  --allowed-origins "https://$FRONTEND_URL" \
  --allowed-methods GET POST PUT DELETE OPTIONS \
  --allowed-headers "*" \
  --allow-credentials true \
  --max-age 3600

# Verify CORS settings
az containerapp ingress cors show \
  --name proposal-backend \
  --resource-group proposal-rg
```

### 3. Set Backend Environment Variable

Update the backend Container App with the CORS origin:

```bash
az containerapp update \
  --name proposal-backend \
  --resource-group proposal-rg \
  --set-env-vars "CORS_ORIGINS=https://$FRONTEND_URL"
```

### Why Both Levels?

| Level | Purpose |
|-------|---------|
| Azure Container Apps CORS | Network-level enforcement, blocks requests before they reach your app |
| FastAPI CORS Middleware | Application-level enforcement, provides flexibility and logging |

Using both ensures that even if one is misconfigured, the other provides protection.

---

## Deployment Plan

### Azure Container App for Frontend

```bash
# 1. Create Container App
az containerapp create \
  --name proposal-frontend \
  --resource-group proposal-rg \
  --environment proposal-env \
  --image proposalapp.azurecr.io/proposal-frontend:latest \
  --target-port 3000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --env-vars "NEXT_PUBLIC_BACKEND_API_URL=https://proposal-backend.thankfulflower-cf94ed15.eastus.azurecontainerapps.io"

# 2. Configure custom domain (optional)
az containerapp hostname bind \
  --name proposal-frontend \
  --resource-group proposal-rg \
  --hostname proposal.fonadvisors.com
```

### Azure Database for PostgreSQL

```bash
# 1. Create flexible server with Burstable tier
az postgres flexible-server create \
  --name proposal-db-fon \
  --resource-group proposal-rg \
  --location eastus2 \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 16 \
  --admin-user dbadmin \
  --admin-password 'YourSecurePassword!' \
  --public-access 0.0.0.0

# 2. Create database
az postgres flexible-server db create \
  --resource-group proposal-rg \
  --server-name proposal-db-fon \
  --database-name fon_proposals

# 3. Firewall rule for Azure services
az postgres flexible-server firewall-rule create \
  --name proposal-db-fon \
  --resource-group proposal-rg \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# 4. Enable pgBouncer connection pooling (built-in)
az postgres flexible-server parameter set \
  --name proposal-db-fon \
  --resource-group proposal-rg \
  --name pgbouncer.enabled \
  --value on

# 5. Configure backup retention (7 days minimum, free)
az postgres flexible-server update \
  --name proposal-db-fon \
  --resource-group proposal-rg \
  --backup-retention 7
```

**Note**: pgBouncer is Azure's built-in connection pooler - no external setup required!

---

## Azure Blob Lifecycle Policy

Configure data tiering for cost optimization:

```bash
az storage account management-policy create \
  --account-name proposalapp \
  --policy '{
    "rules": [{
      "enabled": true,
      "name": "MoveHotToCool",
      "type": "Lifecycle",
      "definition": {
        "filters": { "blobTypes": ["blockBlob"] },
        "actions": {
          "baseBlob": {
            "tierToCool": { "daysAfterModificationGreaterThan": 7 },
            "tierToArchive": { "daysAfterModificationGreaterThan": 90 },
            "delete": { "daysAfterModificationGreaterThan": 90 }
          }
        }
      }
    }]
  }'
```

---

## Monitoring and Alerting

### Application Insights (Optional)

Add to backend:
```python
# pip install opencensus-ext-azure
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger.addHandler(AzureLogHandler(
    connection_string=settings.applicationinsights_connection_string
))
```

### Error Alert

Configure alert rule to email `cveech@fonadvisors.com` if >10 errors in 1 hour:

```bash
az monitor metrics alert create \
  --name "High-Error-Rate" \
  --resource-group proposal-rg \
  --scopes "/subscriptions/{sub}/resourceGroups/proposal-rg/providers/Microsoft.App/containerApps/proposal-backend" \
  --condition "count exceptions/count > 10" \
  --window-size 1h \
  --action-group "/subscriptions/{sub}/resourceGroups/proposal-rg/providers/microsoft.insights/actionGroups/email-alerts"
```

---

## File Changes Summary

| File | Action | Description |
|------|--------|-------------|
| `docs/IMPLEMENTATION_NOTES.md` | Create | This documentation |
| `docs/RUNBOOKS.md` | Create | Operational procedures |
| `backend/db/__init__.py` | Create | Package init |
| `backend/db/database.py` | Create | Async connection pool |
| `backend/db/models.py` | Create | SQLAlchemy Job model |
| `backend/config.py` | Modify | Add DATABASE_URL |
| `backend/api/main.py` | Modify | DB init on startup |
| `backend/api/routes.py` | Modify | DB write + jobs endpoint |
| `backend/api/models.py` | Modify | Dual proposal URLs |
| `backend/pipeline/tasks.py` | Modify | ID renumbering + dual proposals |
| `backend/pyproject.toml` | Modify | Add asyncpg, sqlalchemy |
| `backend/src/proposal/export_word.py` | Modify | Citation stripping |
| `docker-compose.yml` | Modify | Add PostgreSQL service |
| `frontend-next/theme/theme.ts` | Modify | FON Advisors colors |
| `frontend-next/app/globals.css` | Modify | CSS variables |
| `frontend-next/app/layout.tsx` | Modify | Add Navigation |
| `frontend-next/app/page.tsx` | Modify | Redirect to /submit |
| `frontend-next/app/submit/page.tsx` | Create | Job submission page |
| `frontend-next/app/jobs/page.tsx` | Create | Previous Jobs page |
| `frontend-next/components/Navigation.tsx` | Create | Nav bar component |
| `frontend-next/components/JobsTable.tsx` | Create | Paginated table |
| `frontend-next/components/JobForm.tsx` | Modify | Required job name field |
| `frontend-next/components/ProcessingCard.tsx` | Modify | Validate job name |
| `frontend-next/components/ResultsDownload.tsx` | Modify | Dual proposal buttons |
| `frontend-next/components/Header.tsx` | Modify | FON branding |
| `frontend-next/hooks/useJobs.ts` | Create | Jobs list API hook |
| `frontend-next/lib/types.ts` | Modify | Add new URL fields |

---

## Testing Checklist

- [ ] Submit job and verify ID renumbering in matrix
- [ ] Verify both cited and standard proposals are generated
- [ ] Check database write after successful completion
- [ ] Test Previous Jobs page with pagination
- [ ] Verify search and sorting work correctly
- [ ] Test mobile responsive navigation
- [ ] Verify FON Advisors branding throughout
- [ ] Verify job name is required before submission

---

*Last updated: December 30, 2025*
