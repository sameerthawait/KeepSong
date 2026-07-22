# Keepsong Operational Runbook & Rollback Procedure

This document provides a **"What to Check First"** diagnostic decision tree for AI pipeline failures and step-by-step rollback procedures for production deployments.

---

## 1. AI Pipeline Operational Incident Runbook ("What to Check First")

When recordings remain in `processing_status="pending"` or transition to `processing_status="failed"`, follow this diagnostic decision tree:

```
                          [AI Pipeline Failure Detected]
                                        │
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
     [ASR Failure]               [NIM LLM Failure]         [Storage / Database]
  - STT API key expired       - NIM 429/503 rate limit     - Presigned URL expired
  - Unsupported audio codec   - JSON parse error           - pgvector index deadlock
  - Solution: Check ASR log   - Solution: Graceful JSON    - Solution: Retry storage
```

### Stage-Specific Diagnostic Steps

#### A. Speech-to-Text ASR Failures (`failure_stage="asr"`)
1. **Check Sentry / Logs:** Search for `ASR_API_KEY` authentication errors or HTTP 401/429 status codes.
2. **Verify Audio Asset URL:** Confirm audio file was successfully uploaded to object storage and URL is publicly readable by ASR.
3. **Verify Audio Format:** Ensure client recorded in supported MIME type (`audio/webm`, `audio/wav`, `audio/mp4`).

#### B. NIM Llama-3.3-70b Classification Failures (`failure_stage="classification"`)
1. **Check NIM Base URL & API Key:** Verify `NIM_API_KEY` quota on NVIDIA API portal.
2. **Malformed LLM JSON Response:** Pipeline automatically applies safe fallback schema (`theme="uncategorized"`, `confidence=0.5`).
3. **Caregiver Retry Trigger:** Invoke caregiver retry endpoint:
   ```http
   POST /patients/{patient_id}/recordings/{recording_id}/retry
   ```

#### C. Vector Embedding & Search Failures (`failure_stage="embedding"`)
1. **Check Embedding API:** Confirm 1536-dimensional vector array format.
2. **Check pgvector Index:** Verify index status:
   ```sql
   SELECT * FROM pg_indexes WHERE tablename = 'recordings';
   ```

---

## 2. Step-by-Step Production Rollback Procedures

### A. Backend Container Rollback (Render / Fly.io / Docker Compose)

#### For Render / Fly.io Deployments:
1. Open Render / Fly.io dashboard -> Releases tab.
2. Select previous stable deployment build hash.
3. Click **"Rollback to this revision"**.

#### For Docker Compose Production Environments:
```bash
# 1. Stop current containers
docker-compose -f docker-compose.prod.yml down

# 2. Pull previous stable image tag
docker pull keepsong/api:v1.2.0

# 3. Restart production stack
docker-compose -f docker-compose.prod.yml up -d
```

### B. Database Migration Rollback (`alembic downgrade`)

If a database schema deployment causes breaking errors:
```bash
# 1. Inspect current migration revision
alembic current

# 2. Revert 1 migration step
alembic downgrade -1

# 3. Verify database health
alembic current
```

### C. Vercel Frontend Instant Rollback

1. Open Vercel Project Dashboard (`apps/web`).
2. Navigate to **Deployments**.
3. Locate previous healthy deployment before incident.
4. Click `...` -> **Promote to Production**. Rollback completes in $< 5$ seconds.

---

## 3. Uptime Monitoring & Health Endpoints

- **API Health Check Endpoint:** `GET /health` -> Returns `{"status": "healthy"}` with HTTP 200.
- **Uptime Robot / Better Stack Integration:** Configure 60-second ping to `https://api.keepsong.app/health`.
