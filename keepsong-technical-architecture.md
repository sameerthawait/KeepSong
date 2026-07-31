# Keepsong — Technical Architecture Document

**Audience:** Written for a founder who can follow technical reasoning but wants the "why," not just the "what." Any developer joining the project should be able to build from this directly.

---

## 1. Recommended Tech Stack

| Layer | Choice | Why this, and not the obvious alternative |
|---|---|---|
| **Frontend** | Next.js 14 (App Router), TypeScript, Tailwind CSS | One codebase serves both the Patient View and Caregiver Dashboard, which keeps the team small and the design system consistent. Server components reduce how much JavaScript ships to the browser — important for the Patient View, since a low-tech-fluency user on an older device benefits from a lighter, faster-loading page. |
| **Backend** | FastAPI (Python 3.11+), Pydantic v2 | Strong async support matters here because the backend orchestrates several sequential AI calls per recording (transcribe → classify → embed) without blocking other requests. Pydantic v2 gives strict, typed request/response validation, which matters more than usual given this product handles sensitive personal data. |
| **Database** | PostgreSQL + pgvector extension | One database handles both normal relational data (patients, consent records, family members) *and* vector similarity search (for semantic search over transcripts). Running a second, separate vector database (like Pinecone or Chroma) would add real operational complexity that isn't justified at beta scale (~20 families) — this is a deliberate, revisitable trade-off, not an oversight. If the product scales well beyond beta, a dedicated vector DB becomes worth reconsidering. |
| **Object storage** | S3-compatible storage (AWS S3 or Cloudflare R2) | Audio and photo files don't belong in a relational database — they're large, binary, and don't need to be queried like rows. Cloudflare R2 is worth strong consideration specifically because it doesn't charge egress fees, and this product will be reading audio/photos back out frequently (every timeline view, every playback). |
| **Speech-to-text (ASR)** | A dedicated speech-to-text API (e.g. Deepgram or AssemblyAI — verify current pricing/capability before committing, since this space changes quickly) | The LLM provider chosen below (NVIDIA NIM) hosts language models, not speech-to-text models — these are different categories of AI service, and assuming one covers the other would be a mistake caught only after building against it. |
| **LLM tasks** (classification, entity extraction, captions, recommendations) | NVIDIA NIM — Llama-3.3-70b-instruct | Handles every task that requires understanding and structuring the *content* of a transcript: what theme it's about, what decade it likely refers to, who's mentioned, and what a good follow-up prompt would be. |
| **Embeddings** | NIM's embedding endpoint if available in the current catalog, otherwise a dedicated embedding API | Powers the semantic search feature — this needs to be verified against the live NIM catalog rather than assumed, since AI provider offerings change frequently. |
| **Vision (photo captioning)** | A vision-capable model (verify current NIM catalog, or use a dedicated vision API) | Used only for caregiver-side photo caption *suggestions* — never for anything patient-facing. |
| **Authentication** | JWT (caregivers) + scoped PIN (patients) | See Section 3 (Database Schema) and the Security & Access Document for the full reasoning — these are genuinely different threat models, not just two implementations of the same idea. |
| **Background processing** | FastAPI's built-in background tasks (v1) | At 20-family beta scale, a dedicated task queue (Celery/RQ + Redis) is infrastructure the product doesn't need yet. The migration path exists and should be documented, but shouldn't be built preemptively — that's complexity added before there's a real load problem to justify it. |
| **Frontend hosting** | Vercel | Native fit for Next.js; simplest path to production for the frontend specifically. |
| **Backend hosting** | Render or Fly.io | Both support long-running Python services well; final choice can come down to pricing/DX at the time of deployment. |
| **Error monitoring** | Sentry (both frontend and backend) | Given this product handles sensitive data for a vulnerable population, silent failures are unacceptable — Sentry needs to be wired in from day one, not added later. |
| **Analytics** | Plausible | Lightweight, privacy-respecting product usage analytics — appropriate given the sensitivity of what this product's users are doing. |

---

## 2. Complete File & Folder Structure

This project is structured as a **monorepo** — one repository containing both the frontend and backend, so they can be developed, versioned, and reasoned about together.

```
keepsong/
├── apps/
│   ├── web/                        # Next.js 14 frontend (TypeScript, Tailwind)
│   │   ├── app/
│   │   │   ├── (patient)/          # Route group: everything the patient can reach
│   │   │   └── (caregiver)/        # Route group: everything the caregiver can reach
│   │   ├── components/
│   │   │   ├── patient/            # Components used only in the Patient View
│   │   │   ├── caregiver/          # Components used only in the Caregiver Dashboard
│   │   │   └── shared/             # Components used by both
│   │   └── lib/                    # Frontend utilities (API client, formatting, etc.)
│   │
│   └── api/                        # FastAPI backend (Python 3.11+)
│       ├── routers/                # One file per resource area (patients, recordings, etc.)
│       ├── models/                 # SQLAlchemy database models
│       ├── schemas/                # Pydantic request/response schemas
│       ├── services/               # Business logic (kept separate from routers)
│       ├── ai/                     # ASR, classification, embeddings, vision — all AI-specific code
│       └── core/                   # Config, auth, and security utilities shared across the app
│
├── docker-compose.yml               # Local dev: Postgres (with pgvector) + both apps
├── .env.example                     # Template listing every required environment variable
└── README.md                        # Architecture overview, local setup steps, credential checklist
```

**Why the route groups matter specifically for this product:** keeping `(patient)` and `(caregiver)` as separate route groups in Next.js isn't just organizational tidiness — it's a structural enforcement of ADR-004 (the patient interface must never have a path into anything else). Separating them at the folder level makes it much harder to *accidentally* wire a navigation link from the patient screen into caregiver territory.

**Why `services/` is separate from `routers/` on the backend:** routers should only handle HTTP concerns (validating a request came in correctly, returning the right response shape). The actual logic — like "does this caregiver have access to this patient" or "what does it mean for a recording to be fully processed" — lives in `services/`, so that logic can be tested directly without spinning up HTTP requests, and so it isn't duplicated if the same logic is ever needed from more than one endpoint.

---

## 3. Full Database Schema (Explained in Plain English)

The database has one central idea: **everything hangs off a `patient` record.** A caregiver doesn't own recordings directly — they have *access* to a patient, and that patient owns everything else (family members, recordings, prompts, entities).

### 3.1 How the tables relate to each other

```
caregivers ──< caregiver_patient_access >── patients ──< consent_records
                                               │
                                               ├──< family_members
                                               ├──< story_prompts
                                               ├──< recordings ──< entity_mentions >── entities ──< entity_relationships
                                               ├──< recommended_prompts
                                               └──< audit_logs
```

Read this as: one caregiver can have access to multiple patients, and one patient can have multiple caregivers (that's what `caregiver_patient_access` connects). Everything else — consent, family members, prompts, recordings, entities, audit logs — belongs to exactly one patient.

### 3.2 What each table is for

**`caregivers`** — One row per adult account holder. Stores email, a hashed password (never the actual password), and their name.

**`patients`** — One row per person with dementia using the app. Stores their name, a hashed PIN, and which caregiver originally set them up (`primary_caregiver_id`).

**`caregiver_patient_access`** — The "who can see what" table. Connects a caregiver to a patient, with a role of either `owner` (the caregiver who set the patient up) or `contributor` (an invited caregiver, e.g. a sibling). This table is the single source of truth that every access-control check in the app relies on.

**`consent_records`** — Proof that a caregiver has recorded consent for a patient before any recording is allowed. This exists as its own table (rather than just a checkbox on the patient record) so there's a permanent, auditable record of *when* consent was given and by whom.

**`family_members`** — The people shown in the patient's daily check-in (name, relationship, photo). These also get referenced later when the AI tries to recognize a person mentioned in a recording.

**`story_prompts`** — The questions/prompts a patient hears during check-in. Can come from a built-in library, be custom-written by a caregiver, or be AI-recommended (in which case it's not usable until a caregiver has approved it — enforced by `approved_by_caregiver_id`).

**`recordings`** — The core content of the entire product: one row per daily check-in recording. Stores the audio location, the transcript once available, the AI-assigned theme/decade/caption, a confidence score, a plain-English rationale for that classification, and *which* AI model and prompt version produced it (so a future quality issue can be traced back to exactly what generated it, rather than guessed at). Also tracks `processing_status` so the caregiver dashboard always knows exactly where a recording is in the pipeline (pending → transcribing → classifying → embedding → done, or failed at a specific stage).

**`entities`** — People, places, or events mentioned across a patient's recordings (e.g., "Aunt Carol," "the lake house," "the wedding"). Where possible, an entity is linked back to a known `family_members` row.

**`entity_mentions`** — Which recording mentioned which entity, with a confidence score.

**`entity_relationships`** — How two entities relate to each other (e.g., "Aunt Carol" is connected to "the lake house" because a recording described a summer spent there).

**`recommended_prompts`** — AI-suggested follow-up questions based on gaps in the knowledge graph (e.g., someone was mentioned but never elaborated on). Every row starts as `pending_review` and can only become usable once a caregiver has explicitly approved or dismissed it.

**`audit_logs`** — A permanent record of who accessed or changed what, and when. Deliberately **not deleted** even if the related patient record is later deleted — accountability records need to survive the data they're about, not disappear with it.

### 3.3 Key structural decisions worth understanding

- **The audit log outlives the patient record.** If a patient profile is ever deleted, its audit history is intentionally kept. This is a considered decision, not a bug — you want to be able to answer "who accessed this family's data, historically" even after the family has left the product.
- **No fuzzy matching for entities.** If a recording mentions "Sarah," the system only merges her with a previous "Sarah" if it's an exact name match (or matches a known family member). It deliberately does *not* try to guess that two similarly-named people are the same person — an incorrect automatic merge (treating two different people as one) is considered a worse failure than the alternative (briefly having two separate entries for the same person, which a caregiver can notice and isn't hidden or wrong).
- **Every AI-generated field records which model and prompt version produced it, permanently, at the moment it's written.** This is never filled in after the fact. It means that if quality ever seems to regress later, you can actually trace it back to a specific model change or prompt tweak, instead of guessing.

---

## 4. Environment Variables & Configuration Notes

These should live in a `.env.example` file in the repo (with placeholder values only — never real secrets committed to git):

| Variable | What it's for |
|---|---|
| `DATABASE_URL` | Connection string for the Postgres database (with pgvector enabled) |
| `JWT_SECRET` | Signing key for caregiver JWT tokens — must be a long, random value, never reused across environments (dev/staging/production should each have their own) |
| `OBJECT_STORAGE_*` (e.g. `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_KEY`, `OBJECT_STORAGE_SECRET`) | Credentials for wherever audio/photo files are stored (S3 or R2) |
| `ASR_API_KEY` | Key for the speech-to-text provider |
| `NIM_API_KEY` | Key for NVIDIA NIM (LLM calls) |
| `NIM_BASE_URL` | Base endpoint for NIM API calls |
| `WEATHER_API_KEY` | Key for the weather data shown on the patient's daily check-in screen |

**Configuration notes before you start building:**

- **Never hardcode any of the above anywhere in the codebase.** Every one of these should be read from environment variables at runtime, with no fallback to a real value baked into source code.
- **pgvector must be explicitly enabled** on whatever Postgres instance you use (`CREATE EXTENSION IF NOT EXISTS vector;`) — if you choose a managed Postgres provider for production, confirm pgvector support *before* committing to that provider, not after.
- **Object storage should have server-side encryption enabled by default** on the bucket, given the sensitivity of what's stored (a dementia patient's voice recordings and family photos).
- **Uploads should go directly from the browser to object storage using presigned URLs**, not routed through the FastAPI backend. Passing large audio files through your API server adds unnecessary load and timeout risk — and this audience is disproportionately likely to be on unreliable home internet, so upload reliability matters more here than in a typical product.
- **Each environment (local, staging, production) needs its own full set of these variables** — never share a JWT secret or API key across environments, even for convenience during early development.

---

*This document should be read alongside the Security & Access Document (authentication and access-control detail) and the PRD (what each part of this architecture is actually in service of).*
