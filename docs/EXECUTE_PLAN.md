# Execution Guide: Decoupled Frontend/Backend Deployment

Follow these steps in order. Replace ALL_CAPS placeholders with your values. Keep secrets out of chat; export them locally before running commands.

## Architecture (Simplified)

```
Frontend ACA (Streamlit) → Backend ACA (FastAPI + DSPy pipeline) → Azure Blob Storage
```

The backend runs the DSPy pipeline directly as a FastAPI background task. No Prefect work pools or deployments required.

## 1) Prereqs
- Azure CLI logged in: `az login` and `az account set --subscription "<SUBSCRIPTION_ID>"`
- Docker buildx available and logged into ACR

## 2) Export runtime secrets (local shell)
```bash
# Azure OpenAI
export AZURE_API_KEY=...
export AZURE_API_BASE=...
export AZURE_API_VERSION=2024-12-01-preview
export AZURE_OPENAI_DEPLOYMENT=gpt-4.1

# Azure Storage
export AZURE_STORAGE_CONNECTION_STRING=...
export AZURE_BLOB_CONTAINER=proposal-container

# Optional integrations
export LANGFUSE_PUBLIC_KEY=...
export LANGFUSE_SECRET_KEY=...
export LANGFUSE_HOST=https://cloud.langfuse.com
export HIGHERGOV_API_KEY=...
export DOCUMENTINTELLIGENCE_ENDPOINT=...
export DOCUMENTINTELLIGENCE_API_KEY=...
```

## 3) Set non-secret deploy metadata
```bash
export ACR_LOGIN_SERVER=proposalapp.azurecr.io
export AZURE_RESOURCE_GROUP=proposal-rg
export ACA_ENV=proposal-env
export ACA_APP_NAME=proposal-frontend         
# frontend Container App name
export BACKEND_ACA_APP_NAME=proposal-backend    
# backend Container App name
```

## 4) ACR login
```bash
az acr login --name "$(echo $ACR_LOGIN_SERVER | cut -d. -f1)"
```

## 5) Build & push images
```bash
cd /root/fon_proposal_writer

# Frontend (build from frontend directory)
docker buildx build -t "$ACR_LOGIN_SERVER/proposal-frontend:latest" ./frontend
docker push "$ACR_LOGIN_SERVER/proposal-frontend:latest"

# Backend (build from project root to include app/src)
docker buildx build -f backend/Dockerfile -t "$ACR_LOGIN_SERVER/proposal-backend:latest" .
docker push "$ACR_LOGIN_SERVER/proposal-backend:latest"
```

## 6) Deploy/Update Azure Container App (backend API)

### If the backend app exists, update:
```bash
az containerapp update --name "$BACKEND_ACA_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" \
  --image "$ACR_LOGIN_SERVER/proposal-backend:latest" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --ingress external --target-port 8000 \
  --env-vars AZURE_API_BASE="$AZURE_API_BASE" \
             AZURE_API_VERSION="$AZURE_API_VERSION" \
             AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" \
             AZURE_BLOB_CONTAINER="$AZURE_BLOB_CONTAINER" \
             LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY" \
             LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY" \
             LANGFUSE_HOST="$LANGFUSE_HOST" \
             DOCUMENTINTELLIGENCE_ENDPOINT="$DOCUMENTINTELLIGENCE_ENDPOINT"
```

### If you need to create it:
```bash
az containerapp create --name "$BACKEND_ACA_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" \
  --environment "$ACA_ENV" \
  --image "$ACR_LOGIN_SERVER/proposal-backend:latest" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --ingress external --target-port 8000 \
  --env-vars AZURE_API_BASE="$AZURE_API_BASE" \
             AZURE_API_VERSION="$AZURE_API_VERSION" \
             AZURE_OPENAI_DEPLOYMENT="$AZURE_OPENAI_DEPLOYMENT" \
             AZURE_BLOB_CONTAINER="$AZURE_BLOB_CONTAINER" \
             LANGFUSE_PUBLIC_KEY="$LANGFUSE_PUBLIC_KEY" \
             LANGFUSE_SECRET_KEY="$LANGFUSE_SECRET_KEY" \
             LANGFUSE_HOST="$LANGFUSE_HOST" \
             DOCUMENTINTELLIGENCE_ENDPOINT="$DOCUMENTINTELLIGENCE_ENDPOINT"
```

### After create/update, add secrets manually via Azure Portal:
1. Go to Azure Portal → Container Apps → your backend app → Settings → Secrets
2. Add secrets:
   - `AZURE_API_KEY` → your Azure OpenAI key
   - `AZURE_STORAGE_CONNECTION_STRING` → your storage connection string
   - `HIGHERGOV_API_KEY` → your HigherGov key (if used)
   - `DOCUMENTINTELLIGENCE_API_KEY` → your Doc Intel key (if used)
3. Go to Settings → Environment variables
4. Add env vars referencing the secrets:
   - `AZURE_API_KEY` → secretref: `AZURE_API_KEY`
   - `AZURE_STORAGE_CONNECTION_STRING` → secretref: `AZURE_STORAGE_CONNECTION_STRING`
   - `HIGHERGOV_API_KEY` → secretref: `HIGHERGOV_API_KEY`
   - `DOCUMENTINTELLIGENCE_API_KEY` → secretref: `DOCUMENTINTELLIGENCE_API_KEY`

## 7) Export BACKEND_API_URL from the deployed backend ACA
```bash
export BACKEND_API_URL="https://$(az containerapp show -n $BACKEND_ACA_APP_NAME -g $AZURE_RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv)"
echo "Using BACKEND_API_URL=$BACKEND_API_URL"
```

## 8) Deploy/Update Azure Container App (frontend)

### If the app exists, update:
```bash
az containerapp update --name "$ACA_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" \
  --image "$ACR_LOGIN_SERVER/proposal-frontend:latest" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --ingress external --target-port 8501 \
  --env-vars BACKEND_API_URL="$BACKEND_API_URL" STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"
```

### If you need to create it:
```bash
az containerapp create --name "$ACA_APP_NAME" --resource-group "$AZURE_RESOURCE_GROUP" \
  --environment "$ACA_ENV" \
  --image "$ACR_LOGIN_SERVER/proposal-frontend:latest" \
  --registry-server "$ACR_LOGIN_SERVER" \
  --ingress external --target-port 8501 \
  --env-vars BACKEND_API_URL="$BACKEND_API_URL" STREAMLIT_BROWSER_GATHER_USAGE_STATS="false"
```

### After create/update, add HIGHERGOV_API_KEY manually via Portal (if used):
1. Go to Azure Portal → Container Apps → your frontend app → Settings → Secrets
2. Add secret: `HIGHERGOV_API_KEY` → your HigherGov key
3. Go to Settings → Environment variables
4. Add: `HIGHERGOV_API_KEY` → secretref: `HIGHERGOV_API_KEY`

## 9) Smoke test
1. Open the ACA frontend URL (from Portal or `az containerapp show -n $ACA_APP_NAME -g $AZURE_RESOURCE_GROUP --query properties.configuration.ingress.fqdn -o tsv`)
2. Submit a job (upload files or provide blob URLs)
3. Confirm the job completes and returns SAS URLs for:
   - Compliance matrix (Excel)
   - Proposal document (Word)
   - ZIP archive (all outputs)
4. Check ACA logs for errors: `az containerapp logs show -n $BACKEND_ACA_APP_NAME -g $AZURE_RESOURCE_GROUP`

## 10) Optional verifications
```bash
az containerapp show -n "$ACA_APP_NAME" -g "$AZURE_RESOURCE_GROUP" -o table
az containerapp show -n "$BACKEND_ACA_APP_NAME" -g "$AZURE_RESOURCE_GROUP" -o table
```

## Notes
- The backend runs the DSPy pipeline directly as a FastAPI background task. No Prefect deployment or work pool is needed.
- The app reads secrets via `config.Settings` from environment variables.
- Ensure `BACKEND_API_URL` points to the backend endpoint reachable from the frontend ACA.
- Results are uploaded to Azure Blob Storage with 24-hour SAS URL expiry.
