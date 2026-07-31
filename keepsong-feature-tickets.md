# Keepsong — Feature Ticket List

**How to use this doc:** Tickets are grouped by area and ordered so that dependencies are always built before the tickets that need them. Each ticket is written to be pasted directly into an AI coding tool as a self-contained prompt.

---

## A. Foundation (build first, nothing else can start without these)

### A1. Monorepo & Environment Scaffold
**Description:** Set up a monorepo with `/apps/web` (Next.js 14, TypeScript, Tailwind) and `/apps/api` (FastAPI, Python 3.11+, Pydantic v2). Add a root `docker-compose.yml` running Postgres with the pgvector extension enabled, plus both apps for local development. Create a `.env.example` listing every required environment variable (`DATABASE_URL`, `JWT_SECRET`, `OBJECT_STORAGE_*`, `ASR_API_KEY`, `NIM_API_KEY`, `NIM_BASE_URL`, `WEATHER_API_KEY`) with placeholder values only. Add a README covering architecture overview, local setup, and a credential checklist.

**Acceptance Criteria:**
- `docker-compose up` brings up Postgres with pgvector verified working (`CREATE EXTENSION IF NOT EXISTS vector;` succeeds)
- Both apps run locally with placeholder env vars without crashing
- No real secrets are committed anywhere in the repo

**Dependencies:** None — this is the starting point.
**Priority:** Must-have

---

### A2. Database Schema & Migrations
**Description:** Implement the core database schema via SQLAlchemy models and Alembic migrations: `caregivers`, `patients`, `caregiver_patient_access`, `consent_records`, `family_members`, `story_prompts`, `recordings` (base columns only — AI-specific columns added later), and `audit_logs`. Ensure `audit_logs` does NOT cascade-delete when a patient is deleted. Add indexes on `caregivers.email` (unique) and `recordings.patient_id`. Include a seed script using clearly fake test data only.

**Acceptance Criteria:**
- `alembic upgrade head` runs clean
- Seed script populates a working test dataset
- A test confirms that deleting a patient does not delete their `audit_logs` rows

**Dependencies:** A1 (Monorepo Scaffold)
**Priority:** Must-have

---

### A3. Authentication & Access Control (RBAC)
**Description:** Build caregiver authentication (register/login, bcrypt password hashing, JWT access + refresh token pattern) and patient authentication (PIN verification scoped to a single patient record, rate-limited against brute-forcing). Add a FastAPI dependency that enforces `caregiver_patient_access` on every patient-scoped endpoint. Add audit logging as middleware/decorator applied automatically to every sensitive read/write endpoint, not added manually per-endpoint.

**Acceptance Criteria:**
- A caregiver with no access record for a patient receives a 403 even with a valid JWT and a guessed valid patient ID
- Expired JWTs are rejected
- Every recording/transcript/photo access produces an `audit_logs` row
- Patient PIN verification is rate-limited

**Dependencies:** A2 (Database Schema)
**Priority:** Must-have

---

## B. Patient View

### B1. Daily Check-In Screen
**Description:** Build the single-screen Patient View: today's date, weather, one family photo with name/relationship shown in large high-contrast text, and one story prompt in large text. No visible navigation, no settings, no way to exit into anything else.

**Acceptance Criteria:**
- A first-time user completes a check-in with zero prior explanation, validated against a written no-context walkthrough script
- Text contrast and size meet WCAG AA, measured (not assumed)
- No dead-end states anywhere on the screen

**Dependencies:** A3 (Auth & RBAC), C3 (Weather integration, for live data — screen can be built against mock weather data first)
**Priority:** Must-have

---

### B2. Patient PIN Entry
**Description:** Build a large-numeral PIN pad for patient login, scoped to a single patient record. Minimum 64×64px numeral buttons, high contrast, a single obvious "start over" action instead of small backspace/clear targets.

**Acceptance Criteria:**
- Patient can log in with a valid PIN
- Repeated wrong PINs trigger rate-limiting without a confusing error message
- All touch targets meet the 64×64px minimum

**Dependencies:** A3 (Auth & RBAC)
**Priority:** Must-have

---

### B3. Recording Flow (Record → Playback → Save)
**Description:** Build the record → stop → playback → confirm-save flow. Record button must be a minimum 88×88px circular target. Recording must survive a dropped connection mid-capture without data loss, with a friendly retry prompt rather than a technical error.

**Acceptance Criteria:**
- Patient can record, play back before saving, and confirm save
- A simulated dropped connection during recording does not lose the audio
- No technical error language is ever shown to the patient

**Dependencies:** B1 (Check-In Screen), C1 (File Upload & Object Storage)
**Priority:** Must-have

---

## C. Backend Infrastructure & AI Pipeline

### C1. File Upload & Object Storage
**Description:** Implement direct-to-storage uploads via presigned URLs (not routed through FastAPI). Enable server-side encryption on the storage bucket by default. Handle upload failure/retry gracefully. Validate file type/size server-side before issuing presigned URLs. On successful upload, create a `recordings` row with `processing_status: 'pending'` and enqueue it for AI processing.

**Acceptance Criteria:**
- Upload works end-to-end against real or sandboxed object storage
- A dropped connection mid-upload can be retried without losing progress entirely
- Invalid file types/sizes are rejected server-side, not just client-side

**Dependencies:** A2 (Database Schema)
**Priority:** Must-have

---

### C2. Transcription & Classification Pipeline
**Description:** Wire up the ASR provider to transcribe uploaded recordings. Send the transcript to NVIDIA NIM (Llama-3.3-70b-instruct) to classify theme, estimated decade, and generate a caption, along with a confidence score and rationale. Require structured JSON output; malformed responses must fall back to `'uncategorized'` rather than crashing the pipeline. Store `model_identifier` and `prompt_version` at write time on every AI-generated field.

**Acceptance Criteria:**
- A test recording is transcribed and classified end-to-end
- A malformed/invalid model response is handled gracefully (falls back, does not crash)
- `model_identifier` and `prompt_version` are populated on every classification row, with no backfilled values anywhere

**Dependencies:** C1 (File Upload & Object Storage)
**Priority:** Must-have

---

### C3. Weather Integration
**Description:** Integrate a weather API to show current conditions on the Patient View. Location is configured once per patient during setup (never requested live from the device). Cache/refresh periodically rather than calling fresh on every check-in load.

**Acceptance Criteria:**
- Patient View displays real current weather for the configured location
- No location permission prompt ever appears on the Patient View
- API is not called on every single page load (caching verified)

**Dependencies:** A2 (Database Schema)
**Priority:** Must-have

---

### C4. Embeddings & Semantic Search
**Description:** Generate an embedding for each transcript and store it in the `recordings.embedding` pgvector column once classification succeeds. Implement `/timeline/search` to support semantic search (returning relevant recordings, not an LLM-generated answer) combined with optional filters (decade, theme, entity, date range).

**Acceptance Criteria:**
- A paraphrased query (different wording than the transcript) returns the relevant recording, proving semantic matching rather than keyword search
- Search is correctly scoped to `patient_id` — verified that cross-patient leakage never occurs
- Combined filters (e.g. decade + entity) return correct results against known seed data
- The vector index is confirmed in use via `EXPLAIN ANALYZE`, not assumed

**Dependencies:** C2 (Transcription & Classification Pipeline)
**Priority:** Must-have

---

### C5. Knowledge Graph & Entity Extraction
**Description:** Extend the classification call to also extract named entities (people/places/events) and relationships per recording, using structured JSON with the same malformed-response fallback as C2. Deduplicate entities using exact name match plus `family_members` cross-reference only — no fuzzy/probabilistic matching. Add `GET /patients/{id}/graph` returning entities and relationships for a lightweight visualization.

**Acceptance Criteria:**
- Entity extraction correctly links entities to existing `family_members` for a test recording naming them
- A test confirms exact-name dedup does NOT merge two differently-named entities
- `/graph` endpoint returns correct data against seed data

**Dependencies:** C2 (Transcription & Classification Pipeline)
**Priority:** Should-have

---

### C6. Recommendation Engine
**Description:** Scan the knowledge graph for entities that are mentioned but under-elaborated. Generate a candidate follow-up prompt via NIM and write it to `recommended_prompts` with `status: 'pending_review'`. Never auto-inject a recommendation into the patient's prompt queue — it must first be approved by a caregiver.

**Acceptance Criteria:**
- A recommended prompt is generated for a test case with an under-elaborated entity
- A direct API test confirms a recommended prompt never reaches the patient queue without `approved_by_caregiver_id` set

**Dependencies:** C5 (Knowledge Graph & Entity Extraction)
**Priority:** Should-have

---

### C7. Caregiver-Side Photo Captioning
**Description:** Send caregiver-uploaded family photos to a vision-capable model and return an editable suggested caption. Never auto-apply the suggestion, and never show it to the patient as a question. Clearly label it "AI suggestion — please review" in the rendered UI.

**Acceptance Criteria:**
- A test photo upload returns a suggested caption
- The rendered component (not just the API response) is verified to never auto-apply the suggestion
- The suggestion never appears anywhere in the Patient View

**Dependencies:** A3 (Auth & RBAC)
**Priority:** Should-have

---

## D. Caregiver Dashboard

### D1. Patient Profile Setup
**Description:** Build the flow for creating a patient profile, adding family members (name, relationship, photo), and selecting/customizing story prompts from a library.

**Acceptance Criteria:**
- Caregiver can create a patient, add at least one family member, and select at least one prompt
- All required fields are validated server-side, not just client-side

**Dependencies:** A3 (Auth & RBAC)
**Priority:** Must-have

---

### D2. Consent Capture
**Description:** Build a required, non-skippable consent recording step (`POST /patients/{id}/consent`) that must be completed before recording can be enabled for a patient.

**Acceptance Criteria:**
- Recording is impossible for a patient with no consent record on file — verified by direct API test, not just UI behavior
- Consent record stores who recorded it and when

**Dependencies:** D1 (Patient Profile Setup)
**Priority:** Must-have

---

### D3. Timeline View
**Description:** Build the caregiver-facing timeline: recordings grouped by decade/theme, playable, showing AI caption and processing status (with a clear "still processing" state, not a blank or broken-looking placeholder).

**Acceptance Criteria:**
- Full flow works: create patient → add family member → add prompt → record consent → a (mock) recording appears in the timeline once processed
- "Still processing" state is visually distinct and clear, not ambiguous with a failure or empty state

**Dependencies:** D2 (Consent Capture), C2 (Transcription & Classification Pipeline)
**Priority:** Must-have

---

### D4. Search Interface
**Description:** Build the dashboard search bar wired to `/timeline/search`, supporting semantic queries and the decade/theme/entity/date-range filters.

**Acceptance Criteria:**
- Search returns relevant results for a paraphrased query (not just literal keyword matches)
- Filters correctly narrow results against seed data

**Dependencies:** D3 (Timeline View), C4 (Embeddings & Semantic Search)
**Priority:** Must-have

---

### D5. Multi-Caregiver Invite
**Description:** Build a flow allowing an existing caregiver to invite another caregiver (e.g. a sibling) to share access to a patient, creating a `contributor` role in `caregiver_patient_access`.

**Acceptance Criteria:**
- An invited caregiver gains access to the patient's data after accepting
- An invited caregiver cannot revoke the original owning caregiver's access

**Dependencies:** A3 (Auth & RBAC), D1 (Patient Profile Setup)
**Priority:** Must-have

---

### D6. Recommended Prompt Review
**Description:** Build the dashboard UI for reviewing AI-suggested follow-up prompts: caregiver can edit the wording or approve/dismiss as-is. Approved prompts enter the patient's queue; dismissed ones do not.

**Acceptance Criteria:**
- A pending recommended prompt is visible to the caregiver with its source context
- Approve/dismiss actions correctly update `recommended_prompts.status` and, on approval, record `approved_by_caregiver_id`

**Dependencies:** C6 (Recommendation Engine)
**Priority:** Should-have

---

### D7. Knowledge Graph Visualization
**Description:** Build a lightweight node-link visualization of entities and relationships in the dashboard, backed by `GET /patients/{id}/graph`. This is a supporting view — do not over-invest in visual sophistication here relative to core features.

**Acceptance Criteria:**
- Graph renders correctly against seed data with known entities/relationships
- Performs acceptably at beta scale (a single family's data volume)

**Dependencies:** C5 (Knowledge Graph & Entity Extraction)
**Priority:** Should-have

---

### D8. Audit Log View
**Description:** Build a dashboard view showing the audit log for a patient: who accessed or changed what, and when.

**Acceptance Criteria:**
- Log entries are visible and correctly attributed to the acting caregiver
- Log entries persist even after a patient record is deleted (verified by test)

**Dependencies:** A3 (Auth & RBAC)
**Priority:** Should-have

---

## E. Testing, Safety Evaluation & Deployment

### E1. Standard Test Suite
**Description:** Build unit tests (auth/RBAC, consent-gating, AI pipeline JSON validation/fallback, encryption utilities), integration tests (full upload → pipeline → timeline flow), API tests (RBAC boundaries, rate limiting), and E2E tests (Playwright: patient check-in happy path, caregiver setup happy path, search returning relevant results).

**Acceptance Criteria:**
- All test categories pass in CI
- RBAC boundary tests explicitly confirm cross-patient access fails

**Dependencies:** All of A, B, C, D tickets marked Must-have
**Priority:** Must-have

---

### E2. AI Evaluation Harness
**Description:** Build a labeled evaluation fixture (15–20 synthetic, never real, transcripts with hand-labeled theme/decade/entities, plus 5–8 search queries with known-correct matches), versioned in git. Measure and report classification accuracy, retrieval Precision@K/Recall@K (K=3, K=5), and rationale fidelity (hallucination rate), all with real numbers in a reproducible `EVAL_RESULTS.md`.

**Acceptance Criteria:**
- `EVAL_RESULTS.md` contains real, reproducible numbers with documented methodology (dataset size, K value, ground-truth method)
- At least one documented case where filtered search measurably beats pure semantic search
- Eval set is built before results are known, not curated afterward

**Dependencies:** C4 (Embeddings & Semantic Search), C5 (Knowledge Graph & Entity Extraction)
**Priority:** Must-have

---

### E3. Safety Evaluation (Blocking)
**Description:** Extend the evaluation fixture with adversarial cases: relationship invention, unstated medical/health inference, tone/sensitivity on grief-related content, and confidence calibration. Report results in `SAFETY_EVAL.md` with pass/fail per case and quoted model output for any failures. Any medical-inference failure is a blocking release issue, not a tunable/averaged metric.

**Acceptance Criteria:**
- `SAFETY_EVAL.md` exists with zero unresolved medical-inference failures before any real family uses the product
- Category scores are never averaged together in a way that could mask a medical-inference failure

**Dependencies:** E2 (AI Evaluation Harness)
**Priority:** Must-have

---

### E4. Deployment & Observability
**Description:** Dockerize the FastAPI backend (multi-stage build, non-root user). Set up GitHub Actions CI (lint, typecheck, unit + integration tests, blocking merge on failure). Deploy frontend to Vercel, backend to Render/Fly.io, database to managed Postgres with pgvector. Wire up Sentry on both apps and structured logging on the backend, plus uptime monitoring on the API health endpoint. Wrap every AI provider call in a shared instrumentation utility logging latency, cost, and model/prompt version. Build a daily aggregation job for cost/latency/failure-rate reporting, and lightweight alerting on failure-rate or latency thresholds.

**Acceptance Criteria:**
- CI blocks a PR with a failing test
- A full production smoke test succeeds on the live deployed system (not localhost): register → create patient → consent → upload a real recording → see it processed and appear in the timeline → search for it successfully
- Sentry shows zero unhandled errors from that smoke test
- Every AI provider call in the codebase goes through the instrumentation wrapper, verified by confirming no direct calls bypass it
- A simulated failure spike triggers an alert within the expected window

**Dependencies:** E1 (Standard Test Suite), E3 (Safety Evaluation)
**Priority:** Must-have

---

## Summary — Build Order at a Glance

1. **Foundation:** A1 → A2 → A3
2. **Core loop in parallel:** B1/B2/B3 (Patient View) and C1/C2/C3/C4 (backend + AI pipeline) and D1/D2/D3/D4 (Caregiver Dashboard core)
3. **Should-have layer:** C5 → C6 → D6, C5 → D7, C7, D5, D8
4. **Hardening & launch:** E1 → E2 → E3 → E4

Nothing in the "Should-have" layer should be started before the corresponding Must-have dependency is genuinely done and tested — not just "mostly working."
