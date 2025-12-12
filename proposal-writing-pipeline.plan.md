# Containerize & Deploy

## Why
Deploy the disconnected frontend (ACA) and backend (Prefect Managed Worker Pool) using existing Dockerfiles, pushing images to ACR and wiring secrets/env for Azure OpenAI + storage + Prefect.

## Plan
1) Image build & push
- Build `frontend/Dockerfile` and `backend/Dockerfile` images tagged for ACR
- Push both images to ACR (e.g., `acr.azurecr.io/fon-frontend:latest`, `acr.azurecr.io/fon-backend:latest`)

2) Frontend on Azure Container Apps
- Create/update ACA for frontend image from ACR
- Set env: `BACKEND_API_URL` pointing to backend API endpoint; disable usage stats
- Add ACA secrets for required keys if any (e.g., feature flags)
- Configure ingress (HTTPS) and scale (min/max replicas)

3) Backend on Prefect Managed Worker Pool
- Create Prefect deployment using the backend image from ACR
- Configure work pool (managed) with image, timeouts, and storage if needed
- Set env/secrets via Prefect variables/blocks: `AZURE_API_KEY` (also `OPENAI_API_KEY` if required by LiteLLM), `AZURE_API_BASE`, `AZURE_STORAGE_CONNECTION_STRING` or `AZURE_BLOB_CONTAINER`, `PREFECT_API_KEY`, `LANGCHAIN_TRACING_V2`/Langfuse if used
- Confirm flow entrypoint (`backend/prefect_flows/extraction_flow.py`) and parameters for `generate_proposal`/`use_two_stage_writer`

4) Networking & URLs
- Ensure backend API endpoint reachable from ACA; if backend API is not exposed, set ACA to call the public API layer (if any) or provide a stub status page
- Update `frontend/app.py` config defaults if necessary (e.g., `BACKEND_API_URL` env)

5) Release verification
- Smoke test ACA frontend → submit job → verify Prefect run triggers and produces SAS URLs for matrix & proposal
- Check logs for citing modality and chunking behavior

6) Documentation & Ops
- Add short deploy docs (commands for build/push, ACA create/update, Prefect deployment apply)
- Note required secrets mapping (ACA vs Prefect blocks) and image tags

## Todo
- build-push-acr: Build & push frontend/backend images to ACR
- configure-aca: Deploy/update ACA for frontend with env/secrets/ingress
- configure-prefect: Create Prefect deployment using backend image and secrets
- smoke-test: Submit job end-to-end (ACA → backend → SAS URLs)
