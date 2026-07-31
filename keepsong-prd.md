# Keepsong — Product Requirements Document (PRD)

**Version:** 1.0
**Status:** v1 scope frozen — see Section 9 for non-goals and Section 10 for how changes should be proposed

---

## 1. What the App Does

Keepsong preserves the voice and life stories of a person with dementia through a radically simple daily check-in. Each recording is automatically transcribed, classified, and organized by an AI pipeline into a searchable family timeline — one that a caregiver can trust, review, and override at every step.

In one sentence: **Keepsong turns a two-minute daily conversation into a permanent, searchable family archive, without asking a person with memory loss to do anything more complicated than press "record."**

---

## 2. Problem Statement

Families of people with dementia are racing against a closing window. As the disease progresses, the person's voice, stories, and memories become harder to access and eventually disappear entirely — often before anyone thought to record them.

Today, families rely on:
- Ad-hoc phone recordings that are never organized, transcribed, or searchable
- Memory, which fades on both sides — the patient's and the family's
- Nothing at all, because there's no simple system built for a user who may not remember how to open an app, let alone use one

The result is that irreplaceable stories — a wedding day, a childhood home, a sibling's name — are lost permanently, not because families didn't care, but because there was no tool simple enough for the person who needed to use it, and no system smart enough to organize what was captured.

This matters because these recordings aren't just data. They're often the last accessible version of a parent's voice and history that a family will have.

---

## 3. Target Users

### Primary user: The Caregiver
- Typically an adult child of the person with dementia
- Comfortable with everyday apps and dashboards; not necessarily technical
- Time-constrained — often juggling caregiving with work and their own family
- Motivated by urgency (disease progression) and guilt/love (wanting to "get this right" and not miss the window)
- Wants to trust that AI-organized content is accurate, and wants control — the idea of an AI saying something false or inappropriate to or about their parent is a real fear, not a hypothetical

### Secondary user: The Patient
- The person living with dementia
- Tech comfort level: low, and declining. Cannot be expected to learn a new interface, remember multi-step flows, or recover from a wrong tap
- Wants: to talk about their life, respond to a familiar face or prompt, feel successful completing something small
- Frustrated by: complexity, being asked to remember things, feeling tested or interrogated

### Tertiary (not v1): Family Viewer
- Extended relatives who want read-only access to the growing timeline
- Explicitly deferred to v1.5 — see Section 9

---

## 4. Product Vision

Keepsong becomes the trusted, default way families capture and preserve the voice and life story of a loved one with dementia — simple enough for the patient to use alone, and smart enough that the caregiver never has to organize it themselves.

---

## 5. Core Features (v1)

### Patient View

| Feature | Description | Priority |
|---|---|---|
| Daily check-in screen | Shows date, weather, one family photo (with name/relationship), and one story prompt | Must-have |
| Record button | Large, single, unambiguous record control | Must-have |
| Playback before save | Patient can hear their recording before confirming | Must-have |
| No navigation | No visible menu, settings, or way to exit into anything else — one screen, one task | Must-have |

### Caregiver Dashboard

| Feature | Description | Priority |
|---|---|---|
| Patient profile setup | Add family members (name, relationship, photo) | Must-have |
| Story prompt management | Library of prompts + custom prompts, sequenced | Must-have |
| Consent record | Required before recording can be enabled for a patient | Must-have |
| Timeline view | Recordings organized by decade/theme, playable, with AI captions and processing status | Must-have |
| Search | Semantic search plus filters (decade, theme, entity, date range) | Must-have |
| Knowledge graph view | People/places/events and the relationships between them | Should-have |
| Recommended prompts | AI-suggested follow-up prompts, requiring caregiver approval before reaching the patient | Should-have |
| Photo context suggestions | AI-suggested captions on uploaded photos — editable, never auto-applied | Should-have |
| Audit log | Who accessed what, and when | Should-have |
| Multi-caregiver invite | Share access to one patient with another caregiver (e.g. a sibling) | Must-have |

### AI Processing (invisible to both user types)

| Feature | Description | Priority |
|---|---|---|
| Transcription (ASR) | Converts recordings to text | Must-have |
| Classification | Theme, decade, caption, confidence, rationale | Must-have |
| Entity extraction | People/places/events and their relationships | Must-have |
| Embedding generation | Powers semantic search | Must-have |
| Recommendation candidate generation | Surfaces possible follow-up prompts for caregiver review | Should-have |

---

## 6. App Flow

### 6.1 First-time caregiver setup
1. Register an account
2. Create a patient profile
3. Add 3–5 family members with names, relationships, and photos
4. Record consent (required before recording can be enabled)
5. Select and/or customize story prompts
6. Optionally invite a second caregiver (e.g. a sibling)

### 6.2 Daily patient check-in
1. Patient enters their PIN
2. Screen shows today's date, weather, and one family photo
3. Patient hears today's story prompt
4. Patient records their response
5. Patient plays back the recording
6. Patient confirms save
7. Flow ends — no further navigation, nothing else to do or find

### 6.3 Caregiver reviews a new recording
1. Dashboard shows a notification of a new recording
2. Recording initially shows "processing"
3. Within roughly 2 minutes, the recording shows transcript, theme, decade, caption, and a confidence/rationale note
4. Caregiver can later search for it by content, decade, or person mentioned

### 6.4 Caregiver approves a recommended prompt
1. Dashboard surfaces a suggested follow-up (e.g. "Last time your mother mentioned a school friend — ask about them?")
2. Caregiver edits the wording or approves it as-is
3. Approved prompt enters the patient's queue for a future check-in

---

## 7. What the MVP Looks Like

The MVP is the smallest version of Keepsong that lets a real family use it end-to-end, safely, without a caregiver having to do any manual organization:

- A patient can open the app, complete a check-in, and finish without help or explanation
- A caregiver can set up a patient profile, record consent, and add family members and prompts
- Every recording is automatically transcribed, classified, and made searchable within about 2 minutes
- No AI-generated content ever reaches the patient without caregiver approval
- No recording is possible without a consent record on file

Everything beyond this — knowledge graph visualization, multi-caregiver collaboration, recommended prompts — is valuable but the MVP can survive without any one of them if beta timeline pressure requires cutting scope. The check-in → transcribe → organize → search loop is the one piece that cannot be cut.

---

## 8. Success Metrics (Beta, ~20 families)

- A patient can complete a daily check-in unassisted — validated against a written usability walkthrough, not just internal review
- ≥60% of beta families record at least 3x/week after week 2
- The AI pipeline (upload → searchable and visible in the timeline) completes within 2 minutes for ≥95% of recordings
- Zero blocking safety-eval failures in the medical/health inference category before any real family uses the product

These are deliberately mixed: the first two measure whether real families actually adopt and stick with the habit; the third and fourth measure whether the AI pipeline is fast enough and safe enough to trust with a vulnerable user's data.

---

## 9. What We Are Deliberately NOT Building in v1

- **Native iOS/Android apps** — a responsive web app reaches both user types without app store distribution overhead
- **Billing/subscriptions** — no live pricing tier exists yet to build against
- **Voice cloning or AI-generated memory books** — real features on the roadmap, but not built until v1 has real usage data to build on
- **Facility/B2B licensing portal** — out of scope for the family-focused beta
- **Face recognition or biometric photo clustering** — privacy-sensitive, deliberately deferred rather than added by default
- **Patient-facing AI questioning** (e.g., an AI directly asking "is this your wedding day?") — any AI-generated content directed at the patient must go through caregiver review first; this is a product-safety boundary, not a convenience feature to add later
- **Family Viewer role** (read-only access for extended relatives) — planned for v1.5, not v1

Anything not explicitly listed as must-have or should-have above should be treated as out of scope for v1 by default, not built opportunistically.

---

*This PRD should be read alongside the Technical Architecture Document and Security & Access documentation for this project, which cover the "how" behind what's described here.*
