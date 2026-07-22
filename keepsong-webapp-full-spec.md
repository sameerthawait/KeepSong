# Keepsong Web App — Master Specification v1.0

**Status:** Frozen for implementation. Changes to core architecture after this
point should go through the ADR process (Section 11), not ad-hoc edits.

---

## 1. Executive Summary

**Product vision:** Keepsong preserves the voice and life stories of a person
with dementia through a radically simple daily check-in, organized
automatically into a searchable family timeline by an AI pipeline that a
caregiver can trust, review, and override.

**Scope (v1):** A responsive web application with two interfaces — a
single-screen **Patient View** for daily check-ins, and a **Caregiver
Dashboard** for setup, review, and family collaboration — backed by an AI
pipeline for transcription, classification, semantic search, and knowledge
graph construction.

**Non-goals (v1):**
- Native iOS/Android apps (web app is responsive; distribution is not through
  app stores)
- Billing/subscriptions (no live pricing tier exists yet to build against)
- Voice cloning, AI-generated memory books (future paid tiers per the
  original business plan — not built until v1 has real usage data)
- Facility/B2B licensing portal
- Face recognition or biometric photo clustering (privacy-sensitive,
  deliberately deferred)
- Patient-facing AI questioning ("is this your wedding day?") — any
  AI-generated content directed at the patient goes through caregiver review
  first (see ADR-003)

**Success metrics (beta, ~20 families):**
- A patient can complete a daily check-in unassisted — validated against a
  written usability walkthrough, not just internal review
- ≥60% of beta families record at least 3x/week after week 2
- AI pipeline (upload → searchable + visible in timeline) completes within 2
  minutes for ≥95% of recordings
- Zero blocking safety-eval failures (Section 8.4) in the medical/health
  inference category before any real family uses the product

---

## 2. Product Requirements Document

### 2.1 Users

| Role | Description | Auth strategy |
|---|---|---|
| Caregiver | Adult child/family member. Full setup, review, and management access. | Email + password, JWT |
| Patient | The person with dementia. Daily check-in only. | PIN, scoped to one patient record — no password (see ADR-009) |
| Family Viewer (v1.5, not v1) | Invited relatives, read-only timeline access | Invite link, read-only |

### 2.2 Features (v1)

**Patient View**
- Daily check-in: date, weather, one family photo with name/relationship,
  one story prompt, large record button, playback-before-save
- No visible navigation, no settings, no way to exit into anything else

**Caregiver Dashboard**
- Patient profile setup: family members (name, relationship, photo), story
  prompts (library + custom, sequenced)
- Consent record: required before recording is enabled (see 2.4, Section 4.2)
- Timeline: recordings organized by decade/theme, playable, with AI captions
  and processing status
- Search: semantic + filtered (decade, theme, entity, date range)
- Knowledge graph view: people/places/events and their relationships
- Recommended prompts: AI-suggested follow-ups, caregiver-approved before
  reaching the patient
- Photo context suggestions: AI-suggested captions on uploaded photos,
  editable, never auto-applied
- Audit log view: who accessed what, when
- Invite another caregiver (shared access to one patient)

**AI Processing (invisible to both user types)**
- Transcription (ASR)
- Classification: theme, decade, caption, confidence, rationale
- Entity extraction: people/places/events, relationships between them
- Embedding generation for semantic search
- Recommendation candidate generation

### 2.3 User Journeys (representative, not exhaustive)

1. **First-time caregiver setup:** register → create patient profile → add
   3-5 family members with photos → record consent → select/customize story
   prompts → invite a sibling as a second caregiver
2. **Daily patient check-in:** enter PIN → see today's date/weather/photo →
   hear today's prompt → record → play back → confirm save → done, no further
   navigation
3. **Caregiver reviews a new recording:** dashboard notification → recording
   shows "processing" → within ~2 minutes shows transcript, theme, decade,
   caption, confidence/rationale → caregiver can search for it later by
   content, decade, or person mentioned
4. **Caregiver approves a recommended prompt:** dashboard surfaces "Last time
   your mother mentioned a school friend — ask about them?" → caregiver edits
   wording or approves as-is → prompt enters patient's queue

### 2.4 Acceptance Criteria (product-level)

- Patient View: a first-time user completes a check-in with zero prior
  explanation (validated via a written walkthrough script assuming no context)
- No recording is enabled for a patient without a consent record on file
- No AI-generated content reaches the patient view without caregiver approval
- WCAG AA compliance across both interfaces, with body text ≥18px

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
[Next.js Frontend]  →  [FastAPI Backend]  →  [PostgreSQL + pgvector]
      |                       |
      |                       ├──→ [Object Storage: photos, audio] (encrypted)
      |                       ├──→ [ASR Service] (transcription)
      |                       ├──→ [NVIDIA NIM: Llama-3.3-70b] (classification, entities, captions, recommendations)
      |                       ├──→ [Embedding model] → pgvector (semantic search)
      |                       └──→ [Vision-capable model] (caregiver-side photo suggestions)
      |
      └──→ [Plausible Analytics] (product usage)
      └──→ [Sentry] (error monitoring, both apps)
```

### 3.2 Technology Stack

| Layer | Choice | Rationale |
|---|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind | One codebase for patient + caregiver views; server components reduce client JS for the low-tech-fluency patient view |
| Backend | FastAPI (Python), Pydantic v2 | Matches existing CA-RAG stack, strong async support for AI pipeline orchestration |
| Database | PostgreSQL + pgvector | Relational integrity and vector search in one system; see ADR-001 |
| Object storage | S3-compatible (S3 or Cloudflare R2) | Audio/photos don't belong in Postgres; R2 avoids egress fees |
| ASR | Dedicated speech-to-text API (e.g. Deepgram or AssemblyAI — confirm current capability before committing) | NIM does not provide ASR; see ADR-005 |
| LLM tasks | NVIDIA NIM — Llama-3.3-70b-instruct | Classification, entity extraction, captions, recommendations, query understanding |
| Embeddings | NIM embedding endpoint if currently available, else a dedicated embedding API (verify catalog, don't assume) | Powers semantic search |
| Vision | Vision-capable model (verify NIM catalog or use dedicated vision API) | Caregiver-side photo caption suggestions only |
| Auth | JWT (caregiver), PIN (patient) | See ADR-009 |
| Background processing | FastAPI background tasks (v1), documented migration path to Celery/RQ if load requires it | See ADR-011 |
| Deployment | Frontend: Vercel. Backend: Render/Fly.io. DB: managed Postgres with pgvector support. | Independently deployable frontend/backend |

### 3.3 AI Architecture — see Section 6 (dedicated section, cross-referenced from Roadmap Phases 6-8)

### 3.4 Security Architecture — see Section 4.2 (schema) and roadmap Phase 2 (RBAC enforcement)

### 3.5 Deployment Architecture — see Roadmap Phase 10

---

## 4. Database Design

### 4.1 Entity Overview (ER summary)

```
caregivers ──< caregiver_patient_access >── patients ──< consent_records
                                               │
                                               ├──< family_members
                                               ├──< story_prompts
                                               ├──< recordings ──< entity_mentions >── entities ──< entity_relationships
                                               ├──< recommended_prompts
                                               └──< audit_logs
```

### 4.2 Full Schema (v1.0 target — delivered incrementally per roadmap phase, see 4.3)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_uuid()

CREATE TABLE caregivers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE patients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  pin_hash TEXT,
  primary_caregiver_id UUID REFERENCES caregivers(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE caregiver_patient_access (
  caregiver_id UUID REFERENCES caregivers(id),
  patient_id UUID REFERENCES patients(id),
  role TEXT CHECK (role IN ('owner', 'contributor')),
  PRIMARY KEY (caregiver_id, patient_id)
);

CREATE TABLE consent_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID REFERENCES patients(id),
  recorded_by_caregiver_id UUID REFERENCES caregivers(id),
  consent_basis TEXT NOT NULL,
  granted_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE family_members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID REFERENCES patients(id),
  name TEXT NOT NULL,
  relationship TEXT NOT NULL,
  photo_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE story_prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID REFERENCES patients(id),
  prompt_text TEXT NOT NULL,
  sequence_order INT,
  is_custom BOOLEAN DEFAULT false,
  source TEXT CHECK (source IN ('library', 'caregiver_custom', 'ai_recommended')) DEFAULT 'library',
  approved_by_caregiver_id UUID REFERENCES caregivers(id), -- null until approved, required for ai_recommended
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Core content asset. AI-generated fields carry model_identifier + prompt_version
-- from the moment they're written — never backfilled (ADR-013).
CREATE TABLE recordings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID REFERENCES patients(id),
  prompt_id UUID REFERENCES story_prompts(id),
  audio_url TEXT NOT NULL,
  transcript TEXT,
  theme TEXT,
  estimated_decade TEXT,
  ai_caption TEXT,
  classification_confidence NUMERIC(3,2),      -- 0.00-1.00
  classification_rationale TEXT,
  model_identifier TEXT,                        -- e.g. "llama-3.3-70b-instruct"
  prompt_version TEXT,                           -- e.g. "classification_v2"
  embedding VECTOR(1536),
  duration_seconds INT,
  recorded_at TIMESTAMPTZ DEFAULT now(),
  processing_status TEXT CHECK (processing_status IN
    ('pending','transcribing','classifying','embedding','done','failed')),
  failure_stage TEXT                             -- populated only if processing_status = 'failed'
);

CREATE TABLE entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID REFERENCES patients(id),
  type TEXT CHECK (type IN ('person','place','event')),
  name TEXT NOT NULL,
  linked_family_member_id UUID REFERENCES family_members(id), -- null if not resolved to a known person
  first_mentioned_recording_id UUID REFERENCES recordings(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE entity_mentions (
  entity_id UUID REFERENCES entities(id),
  recording_id UUID REFERENCES recordings(id),
  confidence NUMERIC(3,2),
  model_identifier TEXT,
  prompt_version TEXT,
  PRIMARY KEY (entity_id, recording_id)
);

CREATE TABLE entity_relationships (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id_a UUID REFERENCES entities(id),
  entity_id_b UUID REFERENCES entities(id),
  relationship_type TEXT,
  source_recording_id UUID REFERENCES recordings(id),
  model_identifier TEXT,
  prompt_version TEXT
);

CREATE TABLE recommended_prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID REFERENCES patients(id),
  suggested_text TEXT NOT NULL,
  based_on_entity_id UUID REFERENCES entities(id),
  model_identifier TEXT,
  prompt_version TEXT,
  status TEXT CHECK (status IN ('pending_review','approved','dismissed')) DEFAULT 'pending_review',
  reviewed_by_caregiver_id UUID REFERENCES caregivers(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Audit trail deliberately does NOT cascade-delete with patients (ADR, see 4.4)
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_caregiver_id UUID REFERENCES caregivers(id),
  patient_id UUID,  -- intentionally not FK-cascaded; retained after patient deletion
  action TEXT NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### 4.3 Migration Sequencing (which roadmap phase creates which tables)

- Phase 1: caregivers, patients, caregiver_patient_access, consent_records,
  family_members, story_prompts, recordings (without entity/graph columns),
  audit_logs
- Phase 6: recordings gets classification_confidence, classification_rationale,
  model_identifier, prompt_version, embedding, failure_stage added via migration
- Phase 8: entities, entity_mentions, entity_relationships, recommended_prompts
  created; story_prompts gets source and approved_by_caregiver_id added

### 4.4 Key Schema Decisions
- Indexes: caregivers.email (unique), recordings.patient_id,
  recordings.embedding (ivfflat/hnsw for vector search performance)
- audit_logs.patient_id is not a cascading foreign key — audit history must
  survive patient record deletion for accountability (see ADR list, Section 11)
- No fuzzy entity resolution in v1 — entities are deduplicated by exact name
  match plus family_members cross-reference only (see Section 6.4)

---

## 5. API Specification

### 5.1 Authentication
- Caregiver: `POST /auth/caregiver/register`, `POST /auth/caregiver/login` →
  short-lived JWT access token + refresh token
- Patient: `POST /auth/patient/verify-pin` → scoped session token, rate-limited
  per patient record to prevent PIN brute-forcing

### 5.2 Core Endpoints
```
GET    /patients/{id}/checkin
POST   /patients/{id}/recordings
GET    /patients/{id}/recordings/{rid}

GET    /patients/{id}/timeline
GET    /patients/{id}/timeline/search?q=&decade=&theme=&entity_id=&date_from=&date_to=
GET    /patients/{id}/graph

POST   /patients/{id}/family-members
POST   /patients/{id}/prompts
GET    /patients/{id}/prompts/recommended
POST   /patients/{id}/prompts/recommended/{rid}/approve
POST   /patients/{id}/prompts/recommended/{rid}/dismiss

POST   /patients/{id}/consent
POST   /patients/{id}/invite-caregiver
POST   /patients/{id}/photos/{photo_id}/suggest-caption

GET    /audit-logs?patient_id=
```

### 5.3 RBAC
Every patient-scoped endpoint enforces `caregiver_patient_access` server-side
(not just hidden client-side). A caregiver with no access record for a patient
must receive a 403 even with a valid, correctly-formatted JWT and a guessed
valid patient ID.

### 5.4 Error Handling
- Structured error responses: `{ "error_code": "...", "message": "...", "field": "..." }`
  for validation errors
- 429 with retry-after guidance on rate-limited endpoints (patient PIN
  verification, waitlist-style abuse prevention on public endpoints if any)
- AI pipeline failures surface as `processing_status: 'failed'` with
  `failure_stage` populated — never a silent loss of the underlying recording

---

## 6. AI Architecture

This section describes what each AI capability does and why; Section 7
(Roadmap) is where each is actually built.

### 6.1 ASR (Transcription)
A dedicated speech-to-text API — not NIM, which does not provide ASR (ADR-005).
Every recording is transcribed before any downstream AI processing occurs.

### 6.2 Classification
NIM (Llama-3.3-70b-instruct) classifies each transcript into a theme (fixed
set: childhood, career, family, romance/wedding, place/home, other) and
estimated decade, and generates a short caption. The same call returns a
confidence score and a rationale string, enabling explainability (6.7).
Structured JSON output is required and validated; malformed responses fall
back to 'uncategorized' rather than crashing the pipeline.

### 6.3 Embeddings & RAG
Transcripts are embedded and stored in a pgvector column. Semantic search
(5.2, `/timeline/search`) retrieves relevant recordings by similarity — this
is the one genuinely retrieval-augmented-generation-shaped feature in the
product. It is retrieval, not generation: search returns actual matching
recordings for the caregiver to review, not an LLM-synthesized answer about
the patient's life (deliberate scope boundary, see ADR-006).

### 6.4 Knowledge Graph
The same classification call is extended to extract named entities (people,
places, events) and relationships between them per recording. Entities are
deduplicated across recordings by exact name match plus cross-reference
against `family_members` only — no fuzzy/probabilistic matching in v1, since
an incorrect merge (conflating two different people) is worse than leaving
them as separate entities (ADR-002 covers the storage choice; the resolution
policy is a related, separate decision documented in Section 8 testing).

### 6.5 Recommendation Engine
The graph is scanned for entities mentioned but not elaborated on. NIM
generates a candidate follow-up prompt, which enters `recommended_prompts`
with `status: pending_review` — never auto-injected into the patient's queue
without caregiver approval (ADR-003).

### 6.6 Caregiver-Side Multimodal Suggestions
Uploaded family photos are sent to a vision-capable model for a suggested
caption/context. This is surfaced to the caregiver as an editable suggestion
only — never shown to the patient as a question, and never auto-applied. The
original brief's patient-facing "is this your wedding day?" interaction is
explicitly not built (see Section 2, Non-goals, and ADR-003).

### 6.7 Explainability
Every classification carries a confidence score and a rationale string
referencing content actually present in the transcript, surfaced to
caregivers as an expandable detail. Rationale fidelity is manually verified
in the safety evaluation (Section 8.4) — the rationale itself can hallucinate,
and this is checked, not assumed correct because it sounds plausible.

### 6.8 Model Metadata & Prompt Versioning
Every AI-generated field (`recordings.theme/caption/rationale`,
`entity_mentions`, `entity_relationships`, `recommended_prompts`) stores
`model_identifier` and `prompt_version` at write time. This makes it possible
to correlate a later quality regression with a specific model or prompt
change, without guessing (ADR-013).

---

## 7. Implementation Roadmap

Execute phases in order. Each phase below is a complete, standalone
instruction for an autonomous coding agent. Credential checkpoints are marked
explicitly — everything else should be resolved by the agent without
escalation, verified against the acceptance criteria before moving on.

### Phase 0 — Monorepo Scaffold
```
You are a senior full-stack architect setting up a codebase for a product
handling sensitive personal data about a vulnerable population. Every
structural decision should assume this will be audited later.

TASK
1. Monorepo: /apps/web (Next.js 14, TypeScript, Tailwind), /apps/api (FastAPI,
   Python 3.11+, Pydantic v2).
2. Root docker-compose.yml: Postgres with pgvector extension enabled, both
   apps for local dev.
3. /apps/api: /routers, /models (SQLAlchemy), /schemas (Pydantic), /services,
   /ai, /core (config, auth, security utilities).
4. /apps/web: /app/(patient), /app/(caregiver) route groups, /components/patient,
   /components/caregiver, /components/shared, /lib.
5. .env.example: DATABASE_URL, JWT_SECRET, OBJECT_STORAGE_*, ASR_API_KEY,
   NIM_API_KEY, NIM_BASE_URL, WEATHER_API_KEY.
6. README.md: architecture overview, local setup, credential checklist.
7. Alembic configured for backend migrations.

ACCEPTANCE CRITERIA
- docker-compose up brings up Postgres with pgvector verified working
  (CREATE EXTENSION IF NOT EXISTS vector; succeeds).
- Both apps run locally with placeholder env vars without crashing.
- No secrets committed anywhere.
```

### Phase 1 — Database Schema & Migrations
```
You are a senior backend engineer designing a schema for data-protection
correctness review before this touches real families' data.

TASK
Implement via SQLAlchemy models + Alembic: caregivers, patients,
caregiver_patient_access, consent_records, family_members, story_prompts,
recordings (base columns only — AI-specific columns added in Phase 6),
audit_logs — per Section 4.2/4.3 of this spec.

Requirements:
- FK ON DELETE behavior: deleting a patient must NOT cascade-delete
  audit_logs — audit trails persist after data deletion.
- Indexes: caregivers.email (unique), recordings.patient_id.
- Seed script with clearly fake test data (e.g. "Test Patient") — never
  anything resembling real personal data.

ACCEPTANCE CRITERIA
- alembic upgrade head runs clean.
- Seed script populates a working test dataset.
- Test confirms deleting a patient does not delete their audit_logs rows.
```

### Phase 2 — Auth & RBAC
```
You are a senior backend engineer who treats authorization bugs as the most
expensive class of bug this product can ship, given data sensitivity.

TASK
1. Caregiver auth: register/login, bcrypt password hashing, JWT access +
   refresh token pattern.
2. Patient auth: PIN verification scoped to one patient record, rate-limited.
3. FastAPI dependency enforcing caregiver_patient_access on every
   patient-scoped endpoint.
4. Audit logging as middleware/decorator on every sensitive read/write
   endpoint — not manually added per-endpoint where it can be missed.

ACCEPTANCE CRITERIA
- Caregiver A cannot access Patient X's data without an access record, even
  with a guessed valid patient ID — verified via direct API test.
- Expired JWT rejected.
- Every recording/transcript/photo access produces an audit_logs row.
- Patient PIN verification is rate-limited against brute-forcing.
```

### Phase 3 — Caregiver Dashboard
```
You are a senior full-stack engineer building the setup/management interface
for a stressed adult child, often at the end of a long day — clarity over
cleverness.

TASK
1. Patient profile setup: create patient, add family members (name,
   relationship, photo), add/select story prompts.
2. Consent capture (POST /patients/{id}/consent) — required, non-skippable,
   before recording is enabled.
3. Timeline view: recordings grouped by decade/theme, playable, showing
   ai_caption and processing_status (clear "still processing" state).
4. Search bar wired to /timeline/search — semantic search returning relevant
   results even without literal keyword matches.
5. Invite-another-caregiver flow.
6. Audit log view.

ACCEPTANCE CRITERIA
- Full flow: create patient → add family member → add prompt → record
  consent → (mock) recording appears in timeline once processed.
- Search returns relevant results for a paraphrased query.
- WCAG AA compliant.
```

### Phase 4 — Patient Check-In View
```
You are a senior front-end engineer whose primary constraint is radical
simplicity, not features. Every element is something a person with memory
loss parses alone. When in doubt, remove it.

⚠️ CREDENTIAL CHECKPOINT: weather API key needed before this phase can show
real weather data.

TASK
1. Single screen: date, weather, one family photo with name/relationship in
   large high-contrast text.
2. One story prompt, large text, single large record button (min 88x88px).
3. Recording flow: record → stop → playback → confirm save → simple
   confirmation, no further action.
4. No visible navigation, no settings, no accidental-deletion paths.
5. PIN entry with large number pad.

ACCEPTANCE CRITERIA
- A first-time user completes a check-in with zero prior explanation,
  validated against a written no-context walkthrough script.
- Contrast/size meet WCAG AA, measured not assumed.
- No dead-end states.
```

### Phase 5 — File Upload & Object Storage
```
You are a senior backend engineer ensuring uploads are reliable on home wifi,
not just fast office connections.

⚠️ CREDENTIAL CHECKPOINT: object storage credentials (S3 or R2).

TASK
1. Direct-to-storage upload via presigned URLs (not routed through FastAPI).
2. Server-side encryption enabled on the bucket by default.
3. Graceful upload failure/retry — a dropped connection mid-recording must
   not lose the audio.
4. Server-side file type/size validation before issuing presigned URLs.
5. On success: create recordings row (processing_status: 'pending'), enqueue
   AI pipeline (Phase 6).

ACCEPTANCE CRITERIA
- Simulated network interruption during a large upload is recoverable without
  data loss.
- Non-audio file to the audio endpoint is rejected clearly.
- Bucket encryption-at-rest verified via actual configuration, not assumed.
```

### Phase 6 — AI Pipeline: Transcription & Classification
```
You are a senior AI engineer building a pipeline that degrades gracefully —
failure must never silently lose a family's recording.

⚠️ CREDENTIAL CHECKPOINT: ASR API key (confirm provider against current docs),
NVIDIA NIM API key + base URL.

TASK
1. Migration: add classification_confidence, classification_rationale,
   model_identifier, prompt_version, embedding, failure_stage to recordings
   (per Section 4.3).
2. Background job on upload: send audio to ASR, store transcript, update
   processing_status through 'transcribing'.
3. Classification: NIM call with structured JSON output requesting theme,
   estimated_decade, confidence, rationale. Validate JSON; malformed
   responses fall back to 'uncategorized' with a retry, not a crash.
4. Caption generation (same or follow-up NIM call).
5. Write model_identifier + prompt_version at the moment each AI field is
   generated — never backfilled.
6. Embedding generation, stored in the pgvector column, processing_status →
   'done'.
7. Failure at any step: processing_status → 'failed', failure_stage recorded,
   logged with debugging context, surfaced in the caregiver dashboard with a
   retry action.

ACCEPTANCE CRITERIA
- Full pipeline test: upload → transcript → theme/decade/caption/confidence/
  rationale populated → 'done', within the 2-minute target.
- Simulated ASR failure: status 'failed', audio preserved, retry available.
- Simulated malformed LLM JSON: handled without crash, sensible fallback.

DO NOT
- Do not use NIM for transcription — confirm in NIM's current model catalog
  that ASR isn't offered rather than assuming.
```

### Phase 7 — Semantic & Filtered Search (RAG)
```
You are a senior AI engineer building the one genuinely RAG-shaped feature in
this product. Be precise about what that means — this is retrieval, not
generation.

TASK
1. Embed transcripts using an embedding model — confirm NIM's current catalog
   for a suitable embedding endpoint, or use a dedicated embedding API if not
   available; do not assume without checking.
2. GET /patients/{id}/timeline/search: accepts q (semantic query) plus
   structured filters — decade, theme, entity_id, date_range.
3. Combine structured filters (SQL WHERE) with vector similarity ranking:
   filters narrow the candidate set, semantic ranking applies within it. Do
   not re-run the LLM per filter — this is a SQL + vector query, not an LLM
   call.
4. Return actual matching recordings, not an LLM-synthesized answer — do not
   let this feature drift into a chatbot that answers questions about the
   patient's life (see ADR-006).

ACCEPTANCE CRITERIA
- A paraphrased query (different words than the transcript) returns the
  relevant recording — proof of semantic matching, not keyword search.
- Search is correctly scoped to patient_id — verify cross-patient leakage
  never occurs.
- Combined filters (e.g. decade + entity) return correct results against
  known seed data.
- Response time reasonable at beta scale; verify the vector index is
  actually used via EXPLAIN ANALYZE, not assumed.
```

### Phase 8 — Knowledge Graph, Recommendations & Caregiver-Side Multimodal
```
You are a senior AI engineer extending classification into a structured
knowledge graph — the same category of work as conflict-graph construction,
applied to a life story instead of contradictory documents.

⚠️ CREDENTIAL CHECKPOINT: vision-capable model access (confirm NIM catalog or
use a dedicated vision API).

TASK
1. Migration: entities, entity_mentions, entity_relationships,
   recommended_prompts tables (per Section 4.2/4.3); story_prompts gets
   source and approved_by_caregiver_id columns.
2. Entity extraction: extend the Phase 6 classification call to also extract
   named entities and relationships per recording, structured JSON, validated,
   same malformed-response handling as Phase 6.
3. Entity deduplication: exact name match plus family_members cross-reference
   only — no fuzzy/probabilistic matching. Verify this does NOT merge two
   differently-named entities even if contextually similar.
4. GET /patients/{id}/graph — entities + relationships for a lightweight
   node-link visualization in the dashboard (supporting view, not core
   product — don't over-invest here).
5. Recommendation engine: scan the graph for under-elaborated entities,
   generate a candidate follow-up prompt via NIM, write to
   recommended_prompts with status 'pending_review'. Never auto-inject into
   the patient's prompt queue.
6. Approval endpoints: POST /prompts/recommended/{id}/approve and /dismiss —
   only an approved prompt (with caregiver ID recorded) enters the patient
   queue.
7. Caregiver-side photo captioning: send uploaded photos to a vision model,
   return an editable suggested caption. Never auto-applied, never shown to
   the patient as a question, clearly labeled "AI suggestion — please review"
   in the actual rendered UI.

ACCEPTANCE CRITERIA
- Entity extraction correctly links entities to existing family_members for a
  test recording that names them.
- Exact-name dedup works; a test confirms it does NOT merge differently-named
  entities.
- A recommended prompt never reaches the patient queue without an
  approved_by_caregiver_id being set — verified by direct test, not just UI
  behavior.
- Filtered search from Phase 7 correctly uses entity_id filters against this
  phase's tables.
- Photo suggestions are inspected in the rendered component (not just the API
  response) to confirm they're never auto-applied.

DO NOT
- Do not stand up Neo4j — Postgres relational tables per this spec (ADR-002).
- Do not build the patient-facing photo-questioning interaction from the
  original business brief.
```

### Phase 9 — Testing & AI Evaluation
```
You are a senior QA/AI-eval engineer whose job is to prove this works with
measured numbers, not assertions.

TASK

A. Standard testing
1. Unit tests: auth/RBAC, consent-gating, AI pipeline JSON validation/fallback,
   encryption utilities.
2. Integration tests: full upload → pipeline → timeline flow, explicit about
   which external calls are real/sandboxed vs. mocked.
3. API tests: RBAC boundaries (cross-patient access must fail), rate limiting.
4. E2E (Playwright): patient check-in happy path, caregiver setup happy path,
   search returning semantically relevant results.

B. AI evaluation
5. Build a labeled eval fixture (/tests/eval): 15-20 synthetic (never real)
   transcripts with hand-labeled theme/decade/entities, plus 5-8 search
   queries with known-correct matching recordings. Version this in git.
6. Classification accuracy: theme accuracy, decade accuracy (define and
   document the standard — exact match or within-one-decade), entity
   extraction precision/recall. Report actual numbers in EVAL_RESULTS.md.
7. Retrieval quality: Precision@K and Recall@K (K=3, K=5) for pure semantic
   vs. filtered search — demonstrate filters measurably improve precision.
8. Rationale fidelity: manually verify ≥10 classification rationales actually
   reference content present in the transcript. Report a hallucination rate
   as a fraction — do not round up, do not skip if the number is bad.
9. End-to-end pipeline success rate: for a test batch, track pass/fail at
   each stage (upload confirmed → transcribed → classified → embedded →
   searchable → visible in timeline). Report overall success rate AND
   per-stage failure attribution — do not report only the aggregate number.
10. Regression harness: wire this as a script (`eval:ai`) re-runnable
    whenever prompts change.

C. Safety evaluation (blocking, not just measured)
11. Extend the eval fixture with adversarial cases probing:
    - Relationship invention: ambiguous-relationship transcripts — does
      entity extraction ever assign an unstated relationship type?
    - Unstated medical/health inference: transcripts with no medical content
      — does any output introduce health/diagnosis-adjacent language? Any
      occurrence is a BLOCKING failure, not a tunable rate.
    - Tone/sensitivity: transcripts touching grief/loss — does the caption
      stay neutral, or become flippant/presumptuous?
    - Confidence calibration: compare average confidence on correct vs.
      incorrect classifications — a well-calibrated system shows a clear gap.
12. Report in SAFETY_EVAL.md: pass/fail per case, actual model output quoted
    for failures, explicit zero-tolerance flag on the medical-inference
    category. Do not average category scores into one number that could mask
    a medical-inference failure behind other categories performing well.

ACCEPTANCE CRITERIA
- All standard tests pass.
- EVAL_RESULTS.md contains real, reproducible numbers with documented
  methodology (K value, dataset size, ground-truth method) — no bare
  percentages without context.
- At least one documented case where filtered search measurably beats pure
  semantic search.
- SAFETY_EVAL.md exists with zero unresolved medical-inference failures
  before this is considered ready for real families — any failure in that
  category blocks sign-off, it is not merely noted.
- Eval set is built before pipeline results are known — not curated
  afterward to look better.
```

### Phase 10 — Deployment & Operations
```
You are a senior DevOps/platform engineer deploying a system handling
sensitive personal data — logging, monitoring, and rollback need to be real.

⚠️ CREDENTIAL CHECKPOINT: Vercel account, Render/Fly.io account, managed
Postgres provider (confirm pgvector support before committing), Sentry DSN.

TASK

A. Deployment
1. Dockerize FastAPI backend (multi-stage build, non-root user).
2. GitHub Actions CI: lint, typecheck, unit + integration tests on every PR,
   blocking merge on failure.
3. Deploy: frontend → Vercel, backend → Render/Fly.io, DB → managed Postgres
   with pgvector.
4. Sentry on both apps, structured logging on backend, uptime monitoring on
   the API health endpoint.
5. Document rollback procedure and an AI-pipeline-failure runbook (most
   likely operational failure mode given external API dependencies).

B. AI observability
6. Wrap every NIM/ASR/vision/embedding call in a shared instrumentation
   utility logging: timestamp, call purpose, latency, token usage (if
   reported), estimated cost, model_identifier, prompt_version. Structured
   JSON logs, queryable without a full metrics stack.
7. Scheduled aggregation job (not Prometheus/Grafana at this scale — see
   ADR-008): daily average/p95 latency per call type, total token usage and
   cost per day/per patient/system-wide, failure rate per call type tied to
   processing_status='failed' + failure_stage.
8. Cost-per-recording figure: ASR cost + NIM classification/entity/embedding
   token cost, documented formula so it can be recalculated if provider
   pricing changes — this connects directly to the $19/month pricing
   assumption in the original business plan.
9. Lightweight alerting (Sentry alert rule or equivalent): AI pipeline
   failure rate exceeding a threshold (e.g. >10% in a rolling 24h window), or
   latency consistently exceeding the 2-minute target.

ACCEPTANCE CRITERIA
- CI blocks a PR with a failing test.
- Full production smoke test: register → create patient → consent → upload a
  real recording → see it processed and appear in the timeline → search for
  it successfully — on the live deployed system, not localhost.
- Sentry shows zero unhandled errors from that smoke test.
- Every NIM/ASR/vision call in the codebase goes through the instrumentation
  wrapper — verified by confirming no direct API calls bypass it.
- Aggregation job produces a real daily report with actual numbers from a
  test run, not placeholder zeros.
- Simulated failure spike triggers the alert within the expected window.

DO NOT
- Do not stand up Prometheus/Grafana for a 20-family beta — document it as
  the next step if/when call volume justifies it (ADR-008).
```

---

## 8. Testing & AI Evaluation Summary

Covered in full in Phase 9 above. Summary of what's measured:
- Functional correctness: unit, integration, API, E2E
- Classification accuracy: theme, decade, entity precision/recall
- Retrieval quality: Precision@K, Recall@K, semantic vs. filtered comparison
- Explainability fidelity: rationale hallucination rate
- Pipeline reliability: end-to-end success rate with per-stage attribution
- Safety: relationship invention, medical inference (blocking), tone,
  confidence calibration
- Regression: versioned eval harness re-runnable on prompt changes

---

## 9. Operations & Observability Summary

Covered in full in Phase 10 above. Summary:
- Structured logging on every AI call (latency, tokens, cost, model/prompt
  version)
- Daily aggregation job (not a full metrics stack — deferred per ADR-008)
- Cost-per-recording tracked and tied back to the product's pricing model
- Lightweight alerting on failure rate and latency thresholds
- Sentry across both apps, uptime monitoring on API health

---

## 10. Future Roadmap (explicitly not v1)

- Voice cloning for late-stage communication loss
- AI-generated printed memory books
- Facility/memory-care licensing portal (B2B2C)
- Native iOS/Android apps
- Neo4j migration for the knowledge graph, if scale/query complexity
  eventually justifies it over the Postgres relational implementation (ADR-002)
- Fuzzy/probabilistic entity resolution (if exact-match dedup proves
  insufficient at scale)
- Prometheus/Grafana observability stack (ADR-008)
- Family Viewer role (read-only invited relatives)
- Billing/subscription tiers, once pricing is finalized against real beta data

Ideas beyond this list go here, not into the frozen v1 architecture.

---

## 11. Architecture Decision Records

**ADR-001: PostgreSQL + pgvector instead of a dedicated vector database.**
At beta scale (20-200 families), running one database system for both
relational data and vector search is simpler to operate than adding
Chroma/Pinecone. Trade-off: pgvector is less performant than a dedicated
vector DB at very large scale — accepted as a deliberate, revisitable choice,
not an oversight.

**ADR-002: Postgres relational tables for the knowledge graph instead of
Neo4j in v1.** A second database system adds operational complexity not
justified at beta scale. Recursive CTEs are sufficient for the graph
traversal needs of a single family's data. Documented migration path to Neo4j
exists if query complexity grows (Section 10).

**ADR-003: AI-generated content directed at the patient always requires
caregiver approval first.** Applies to recommended prompts and photo
captions. A caregiver should control tone and framing before their parent
sees AI-generated content — this is a product-safety boundary, not just a
review-queue convenience.

**ADR-004: The patient interface is intentionally single-screen with no
navigation.** The target user has memory loss and may be using the app
without help. Every additional screen or menu is a point of failure for this
specific user, even if it would be a normal UX pattern elsewhere.

**ADR-005: ASR is a dedicated service, not NVIDIA NIM.** NIM hosts LLMs, not
speech-to-text models. Using it for ASR would require assuming a capability
that isn't confirmed to exist rather than verifying it against the current
model catalog.

**ADR-006: Semantic search returns retrieved recordings, not an
LLM-generated answer.** A chatbot that answers questions about a dementia
patient's life history from possibly-incomplete recordings risks presenting
a hallucinated answer as established fact about a real, vulnerable person.
Retrieval-only keeps the caregiver in the loop as the one interpreting the
source material.

**ADR-007: Unstated medical/health inference is a blocking safety failure,
not a tunable metric.** Most AI quality issues are acceptable at some
non-zero error rate. A fabricated health detail attached to a real elderly
person's record is not — any occurrence blocks release of that pipeline
stage, regardless of how it affects an aggregate score.

**ADR-008: Prometheus/Grafana is deferred until call volume justifies it.**
A daily aggregation job into a queryable Postgres table is sufficient
observability at beta scale. Standing up a full metrics stack earlier is
premature infrastructure investment relative to actual load.

**ADR-009: Caregivers authenticate with JWT + password; patients
authenticate with a scoped PIN.** These are different threat models and
different usability requirements — a patient with memory loss cannot be
expected to manage a password, but also doesn't need the same session
persistence or account-recovery flows a caregiver account requires.

**ADR-010: Uploads go directly to object storage via presigned URLs, not
through the API server.** Routing large audio/photo files through FastAPI
adds unnecessary server load and timeout risk on the kind of home internet
connection this audience actually has.

**ADR-011: FastAPI background tasks for v1, not Celery/Redis.** A dedicated
task queue is justified once processing volume or reliability requirements
exceed what in-process background tasks can handle. Introducing that
complexity before it's needed is over-engineering for a 20-family beta.

**ADR-012: No fuzzy/probabilistic entity resolution in v1.** Deduplicating
"Sarah" across recordings uses exact name match plus family_members
cross-reference only. An incorrect probabilistic merge (conflating two
different people) is a worse failure than under-merging, which just leaves
two entities where there should be one — a recoverable, visible problem
rather than a silent data-integrity error.

**ADR-013: Every AI-generated field stores model_identifier and
prompt_version at write time, never backfilled.** This is what makes it
possible to correlate a future quality regression with a specific model or
prompt change, rather than guessing after the fact. A backfilled identifier
on old records would be a guess presented as a fact.

**ADR-014: No native mobile apps in v1.** A responsive web app reaches both
patient and caregiver users without App Store review cycles or separate
codebases, and the target complexity (voice recording, photo upload) is
well-supported by modern mobile browsers.

**ADR-015: Voice cloning and AI memory books are deferred past v1.** These
are real features in the original business plan, but building them before
the core check-in/timeline loop has real usage data would be building on an
unvalidated foundation.

**ADR-016: AI orchestration is vanilla Python, no LangChain/LangGraph or equivalent framework.** Direct API calls with manual prompt construction and manual output validation make it clear exactly what request is sent and what response is parsed, with no framework abstraction between the code and the model's actual behavior. This is a deliberate learning and debugging trade-off: a framework would reduce boilerplate but would also obscure the mechanics this project is meant to demonstrate understanding of. Revisit only if a specific framework capability (e.g. LangGraph's state management for a genuinely multi-step agent loop) becomes a real bottleneck vanilla Python can't reasonably handle — not by default.

---

*End of Master Specification v1.0. Future changes to architecture should be
proposed as new ADRs, not silent edits to earlier sections.*
