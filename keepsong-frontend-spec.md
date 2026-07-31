# Keepsong — Frontend Specification Document

**Scope note:** Keepsong renders two visually and behaviorally distinct experiences from one design system — the **Patient View** (radical simplicity, high contrast, large touch targets) and the **Caregiver Dashboard** (denser, information-rich, standard SaaS conventions). Shared tokens keep them recognizably one product; component sizing and density differ deliberately between the two.

---

## 1. Design System

### 1.1 Color Palette

| Token | Hex | Usage |
|---|---|---|
| `--color-primary` | `#2E5D4E` (deep sage green) | Primary actions, active states, brand accent. Calm and warm rather than clinical — deliberately avoids the cold blue/white palette common to "medical" apps, since this is a family product, not a clinical one. |
| `--color-primary-light` | `#5C8A79` | Hover states, secondary emphasis |
| `--color-secondary` | `#C97B4A` (warm terracotta) | Accent for highlights, the record button, and any "this needs attention" affordance that isn't an error |
| `--color-background` | `#FAF8F3` (warm off-white) | Default page background — softer than pure white, easier on the eyes for extended dashboard use and less clinical for the Patient View |
| `--color-surface` | `#FFFFFF` | Cards, modals, elevated surfaces |
| `--color-text-primary` | `#1F2B27` (near-black, green-tinted) | Body and heading text |
| `--color-text-secondary` | `#5A6560` | Supporting text, captions, metadata |
| `--color-border` | `#E0DCD3` | Dividers, card borders, input borders |
| `--color-success` | `#3A7D5C` | Confirmation states ("recording saved," "consent recorded") |
| `--color-warning` | `#B8863B` | "Still processing," low-confidence classification flags |
| `--color-error` | `#B5493A` | Failed uploads, access-denied, validation errors |
| `--color-patient-focus` | `#2E5D4E` at 100% with a `4px` focus ring | Used exclusively in the Patient View for the record button and PIN pad — the single highest-contrast, highest-visibility element on that screen |

**Contrast requirement:** every text/background pairing above must meet WCAG AA (4.5:1 for body text, 3:1 for large text) — verified against the actual rendered values, not assumed from the palette alone, especially for `--color-text-secondary` on `--color-background`.

### 1.2 Typography

| Token | Font | Usage |
|---|---|---|
| `--font-heading` | Inter (600/700 weight) | Headings, dashboard section titles |
| `--font-body` | Inter (400/500 weight) | Body text, UI labels, everywhere else |
| `--font-patient` | Inter (500 weight), same family but a dedicated scale (below) | Patient View only — same typeface for brand consistency, but a completely different size scale |

**Caregiver Dashboard scale:**

| Token | Size | Usage |
|---|---|---|
| `--text-xs` | 12px | Timestamps, metadata |
| `--text-sm` | 14px | Secondary labels, table content |
| `--text-base` | 16px | Body text |
| `--text-lg` | 18px | Emphasized body text |
| `--text-xl` | 24px | Card titles |
| `--text-2xl` | 32px | Page/section headings |

**Patient View scale (deliberately oversized — this is not the same scale, not a "responsive" shrink of it):**

| Token | Size | Usage |
|---|---|---|
| `--text-patient-body` | 28px minimum | Family member name, prompt text |
| `--text-patient-label` | 36px | Date, primary label text |
| `--text-patient-button` | 32px | Record button label |

**Hard rule from the product spec:** body text must be ≥18px everywhere, but the Patient View's actual working minimum is far higher than the accessibility floor — this screen is designed around low vision and reduced processing speed as the default assumption, not the edge case.

### 1.3 Component Styles

**Buttons**

| Variant | Style | Where used |
|---|---|---|
| Primary | `--color-primary` fill, white text, 8px radius, 44px min height | Caregiver Dashboard primary actions ("Save," "Invite Caregiver") |
| Secondary | White fill, `--color-primary` border and text, 8px radius | Secondary dashboard actions |
| Destructive | `--color-error` fill, white text | Delete/remove actions, always paired with a confirmation step |
| Patient Record Button | `--color-secondary` fill, perfect circle, **minimum 88×88px**, white icon, no text label needed but paired with large text above it | The single most important interactive element in the product — sized per the product spec's explicit minimum, not a standard button token |

**Inputs**

- 48px min height (Caregiver Dashboard), `--color-border` border, 6px radius, `--color-primary` border on focus with a visible focus ring (never color-only focus indication)
- Patient PIN pad: large numeral buttons, minimum 64×64px each, high contrast, no small "clear"/"backspace" targets — a single obvious "start over" affordance instead

**Cards**

- `--color-surface` background, `--color-border` 1px border, 12px radius, subtle shadow (`0 1px 3px rgba(0,0,0,0.08)`)
- Used for: timeline recording entries, family member entries, recommended-prompt review items

**Modals**

- Centered, `--color-surface` background, 16px radius, max-width 480px on desktop
- Always include a clear, single-purpose title and an explicit close/cancel action — no modal in the Caregiver Dashboard should rely on a click-outside-to-dismiss as the only exit, since this product's caregivers are often reviewing sensitive content and shouldn't lose context accidentally
- **No modals in the Patient View at all** — per ADR-004, that interface has zero navigation or interruption patterns; a modal is itself a form of navigation complexity this view must never introduce

### 1.4 Spacing & Layout Rules

**Base unit:** 4px. All spacing values are multiples of this (4, 8, 12, 16, 24, 32, 48, 64).

| Context | Rule |
|---|---|
| Caregiver Dashboard grid | 12-column grid, 24px gutters, max content width 1200px |
| Card internal padding | 16px (dashboard), 24px (Patient View — generous padding around the one card that matters on that screen) |
| Section spacing | 32px between major dashboard sections |
| Patient View layout | Single column, generous vertical spacing (48px+ between the photo, the prompt, and the record button) — nothing competes visually with the record button |
| Touch targets | 44×44px minimum everywhere (WCAG AA), 88×88px minimum for the Patient View record button specifically |

---

## 2. API & Integration Spec

Every third-party service Keepsong depends on, what it's for, and the shape of the request/response. **Exact endpoint paths and payload schemas for the ASR, NIM, and vision providers should be confirmed against each provider's current API documentation before implementation** — provider APIs evolve, and this section documents the integration's *role and data flow*, not a guaranteed-current wire format.

### 2.1 Speech-to-Text (ASR Provider — e.g. Deepgram or AssemblyAI)

- **What it does:** Converts a patient's recorded audio into a text transcript.
- **Data sent:** The recorded audio file (or a reference/URL to it in object storage).
- **Data expected back:** A transcript (plain text), and ideally per-word or per-segment confidence data if the provider offers it.
- **Where it's called from:** Backend only (`/apps/api/ai/`), triggered automatically once a recording upload is confirmed. Never called from the frontend directly — the frontend never holds this provider's API key.
- **Failure behavior:** If transcription fails, the recording's `processing_status` is set to `failed` with `failure_stage: 'transcribing'` — the original audio is preserved regardless (see Security & Access Document, Section 4).

### 2.2 LLM Tasks — NVIDIA NIM (Llama-3.3-70b-instruct)

- **What it does:** Classifies each transcript (theme, estimated decade, caption, confidence, rationale), extracts named entities and relationships, and generates candidate follow-up prompts.
- **Data sent:** The transcript text, plus a structured prompt instructing the model to return JSON matching a defined schema (theme/decade/caption/confidence/rationale, or entities/relationships depending on the call).
- **Data expected back:** Structured JSON matching that schema. **Malformed or non-JSON responses must fall back to an `'uncategorized'` state rather than crashing the pipeline** — this is a hard requirement, not a nice-to-have, since this call sits in the middle of the automated pipeline.
- **Where it's called from:** Backend only (`/apps/api/ai/`).
- **Metadata requirement:** every response written to the database must be stored alongside `model_identifier` and `prompt_version` at write time (never backfilled) — this is what makes future quality regressions traceable.

### 2.3 Embeddings

- **What it does:** Converts each transcript into a vector representation for semantic search.
- **Data sent:** Transcript text.
- **Data expected back:** A numeric vector (dimension depends on the specific embedding model/provider chosen — confirm against the current NIM catalog or fallback provider before implementation).
- **Where it's called from:** Backend, immediately after classification succeeds, storing the result in the `recordings.embedding` pgvector column.

### 2.4 Vision (Caregiver-Side Photo Captioning)

- **What it does:** Suggests a caption/context for a caregiver-uploaded family photo.
- **Data sent:** The photo (or a reference to it in object storage).
- **Data expected back:** A short suggested caption string.
- **Where it's called from:** Backend, triggered when a caregiver uploads a new family photo.
- **Critical constraint:** the response is surfaced to the caregiver as an **editable suggestion only**, clearly labeled "AI suggestion — please review" in the actual rendered component. It is never auto-applied and never shown to the patient directly.

### 2.5 Object Storage (S3 or Cloudflare R2)

- **What it does:** Stores all audio recordings and photos.
- **Data sent:** The file itself, uploaded **directly from the browser to storage using a presigned URL** obtained from the backend — not routed through the FastAPI server.
- **Data expected back:** A presigned upload URL (from the backend's own endpoint) and, on the storage provider's side, a success response for the direct upload.
- **Where it's called from:** The backend issues the presigned URL; the frontend performs the actual upload directly to the storage provider.
- **Configuration requirement:** server-side encryption enabled on the bucket by default, given the sensitivity of the content.

### 2.6 Weather API

- **What it does:** Shows today's weather on the Patient View check-in screen, as a small piece of everyday grounding context.
- **Data sent:** A location (configured once per patient during setup, not re-requested from the device each time — avoids any location-permission friction on the Patient View, which has zero tolerance for friction).
- **Data expected back:** Current conditions and temperature, in a simple format the frontend can render as an icon + short label.
- **Where it's called from:** Backend, cached/refreshed periodically rather than called fresh on every single check-in load.

### 2.7 Sentry

- **What it does:** Error monitoring for both the frontend and backend.
- **Data sent:** Error/exception details, stack traces, and request context on unhandled errors.
- **Data expected back:** N/A (write-only from the app's perspective; Sentry's dashboard is where this is reviewed).
- **Where it's called from:** Both apps — configured once at the framework level (Next.js and FastAPI both have standard Sentry SDK integration), not manually added per-endpoint.
- **Sensitivity note:** error payloads must be scrubbed of PII (transcript content, names, PINs) before being sent — this needs explicit configuration, not the SDK's default behavior assumed to be safe.

### 2.8 Plausible Analytics

- **What it does:** Lightweight, privacy-respecting product usage analytics (page views, feature usage).
- **Data sent:** Page/event names only — no personal data, no transcript content, no patient identifiers.
- **Data expected back:** N/A (write-only).
- **Where it's called from:** Frontend only, and explicitly never on the Patient View in a way that could leak any identifying information about the patient — analytics on that screen, if any, should be limited to anonymous, aggregate interaction events (e.g., "check-in completed"), never content.

---

*This document should be read alongside the Technical Architecture Document (backend structure these integrations plug into) and the PRD (why the Patient View and Caregiver Dashboard have such different design requirements in the first place).*
