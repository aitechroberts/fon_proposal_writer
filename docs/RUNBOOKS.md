# Operational Runbooks - FON Advisors Proposal Writer

> **Purpose**: Step-by-step instructions for diagnosing and resolving common issues.

---

## 1. Job Stuck in Running State

### Symptoms
- Job shows "running" status for >30 minutes
- Progress percentage not advancing

### Diagnosis
```bash
az containerapp logs show -n proposal-backend -g proposal-rg --tail 100
```

### Resolution
- **Timeout**: Increase container timeout to 600s
- **Memory**: `az containerapp update -n proposal-backend -g proposal-rg --memory 4Gi`
- **Stuck**: Ask user to resubmit (in-memory state only)

---

## 2. Database Connection Issues

### Diagnosis
```bash
az postgres flexible-server show -n proposal-db-fon -g proposal-rg --query state
psql "$DATABASE_URL" -c "SELECT 1"
```

### Resolution
```bash
# If server stopped
az postgres flexible-server start -n proposal-db-fon -g proposal-rg

# If firewall blocking
az postgres flexible-server firewall-rule create \
  -g proposal-rg -s proposal-db-fon -n AllowAzureServices \
  --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0
```

---

## 3. High Error Rate Alert

**Trigger**: Email to `cveech@fonadvisors.com` when >10 errors in 1 hour.

### Diagnosis
- Portal → Application Insights → Failures
- `az containerapp logs show -n proposal-backend -g proposal-rg --tail 200 | grep -i error`

### Common Causes
| Error | Cause | Fix |
|-------|-------|-----|
| RateLimitError | Azure OpenAI quota | Wait or increase quota |
| ContentFilterError | Flagged content | Review document |
| TimeoutError | Large document | Increase resources |

---

## 4. Frontend Cannot Connect to Backend

### Diagnosis
```bash
BACKEND_URL=$(az containerapp show -n proposal-backend -g proposal-rg \
  --query "properties.configuration.ingress.fqdn" -o tsv)
curl "https://$BACKEND_URL/api/v1/health"
```

### Resolution
```bash
az containerapp update -n proposal-frontend -g proposal-rg \
  --set-env-vars NEXT_PUBLIC_BACKEND_API_URL="https://$BACKEND_URL"
```

---

## Quick Reference

```bash
# View logs
az containerapp logs show -n proposal-backend -g proposal-rg --tail 100

# Restart backend
az containerapp revision restart -n proposal-backend -g proposal-rg

# Check PostgreSQL
az postgres flexible-server show -n proposal-db-fon -g proposal-rg --query state

# Get URLs
az containerapp show -n proposal-frontend -g proposal-rg --query properties.configuration.ingress.fqdn -o tsv
```

---

*Last updated: December 30, 2025*

