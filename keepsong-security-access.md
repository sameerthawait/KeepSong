# Keepsong — Security & Access Document

**Audience:** Written in plain English so a non-technical founder can understand every decision here, not just an engineer.

---

## 1. Authentication Method

Keepsong has two very different users, and they need two very different login systems. Using the same method for both would either be insecure for one or unusable for the other.

### Caregivers: Email + Password (JWT)
Caregivers are adults managing an account, comfortable with normal app logins. They authenticate with email and password, and the server issues a **JWT (JSON Web Token)** — a short-lived, cryptographically signed pass that proves who they are on every subsequent request, plus a longer-lived refresh token so they aren't forced to log in constantly.

**Why this fits:** Caregivers need normal account security expectations — password reset, the ability to log in from a new device, session persistence over days or weeks.

### Patients: A Simple PIN, No Password
The patient is living with dementia. Asking them to remember a password, an email address, or how to reset either is not just inconvenient — it's a guaranteed failure point for the exact person the product exists to serve.

Instead, a patient logs in with a **short PIN**, scoped to one specific patient record only. There's no password, no account recovery flow, and no way for a PIN to unlock anything beyond that one patient's daily check-in screen.

**Why this fits:** The PIN's only job is to make sure a stranger can't casually open the app and record something as if they were the patient. It is not meant to be bank-grade security — it's meant to be usable by someone with memory loss, while still requiring a deliberate action to access.

**Guardrail:** PIN attempts are rate-limited per patient record. If someone tries PIN after PIN in a short window, the system slows down or blocks further attempts — this stops anyone from just guessing every 4-digit combination until one works.

---

## 2. User Roles & Permissions

| Role | Can do | Cannot do |
|---|---|---|
| **Caregiver (Owner)** | Create/manage the patient profile, add family members and prompts, record consent, view and search the full timeline, approve or dismiss AI-suggested prompts and captions, invite other caregivers, view the audit log | Access another family's patient data — a caregiver only ever has access to patients explicitly connected to their account |
| **Caregiver (Contributor)** — an invited second caregiver, e.g. a sibling | Same day-to-day access as an Owner: view timeline, add prompts, approve suggestions | Cannot revoke the original owning caregiver's access (prevents one invited caregiver from locking out the family member who set the account up) |
| **Patient** | Complete the daily check-in: see today's prompt, record, play back, save | See the dashboard, timeline, other family members' details, settings, or any AI-generated content that hasn't been caregiver-approved. There is no path from the patient screen into anything else in the app |
| **Family Viewer** *(not in v1)* | Planned as read-only timeline access for extended relatives once built | N/A — role doesn't exist yet |

**The one rule that matters most:** No AI-generated content — a suggested prompt, a photo caption, anything — ever reaches the patient's screen without a caregiver approving it first. This isn't a "nice to have" review step; it's a hard boundary. The system should be built so this is structurally impossible to bypass, not just a checkbox that happens to usually get checked.

---

## 3. Row-Level Security Rules

Every patient's data — recordings, family members, prompts, everything — must be invisible to every other family using Keepsong. This isn't optional or a "best practice"; it's the core trust promise of a product handling a vulnerable person's life story.

**The rule, stated simply:** A caregiver can only see or touch a patient record if there's an explicit access record connecting that caregiver to that patient. No exceptions, no "just this once," no fallback that grants broader access.

In practice, this means:
- Every single request for patient data — recordings, timeline, family members, prompts, audit log, anything — must check "does this caregiver have an access record for this specific patient?" **on the server**, every single time. Never assume the app's screen structure alone keeps people out (a person could, in theory, guess or copy a valid-looking web address and just try to load someone else's data directly).
- Even a perfectly valid, correctly logged-in caregiver should be blocked (with a clear "access denied" response) if they try to reach a patient they aren't connected to — even if they somehow know or guess that patient's ID.
- The audit log records every access, including denied attempts, so if something ever looks wrong, there's a trail to investigate.

**Why this matters practically:** if this check is ever done only in the app's visual design (e.g., "the dashboard just doesn't show a button for other patients") rather than enforced by the server itself, it's not actually security — it's just hiding the door, not locking it.

---

## 4. Error Handling Guide

The goal here is simple: **the app should never fail silently, and it should never confuse or frighten the patient.**

| Failure point | What happens | What the user sees |
|---|---|---|
| Patient enters wrong PIN | Attempt is logged, rate-limiting kicks in after repeated failures | A simple, non-alarming message — no "invalid PIN" jargon, no lockout explanation that a confused user can't act on |
| Caregiver enters wrong password | Standard login failure | Clear, calm error message with a password-reset option |
| Caregiver tries to access a patient they're not connected to | Request is blocked at the server, logged | A generic "you don't have access to this" message — never details about why, which could leak information about other families' data |
| Recording upload fails mid-way (bad connection, dropped signal) | The partial upload is not treated as a saved recording | Patient sees a friendly retry prompt — never a technical error, never silence that leaves them unsure if it worked |
| AI processing pipeline fails (transcription, classification, etc.) | The recording is preserved either way — the *audio itself* is never lost even if the AI step fails. The system marks exactly which processing stage failed | Caregiver dashboard shows "processing failed at [stage]" rather than the recording just vanishing or hanging forever on "processing" |
| Payment/billing failure | N/A in v1 — no billing exists yet | N/A |
| Server or AI service is temporarily down | Requests get a clear "try again shortly" response rather than hanging indefinitely | Caregiver sees a status message, not a blank or broken screen |

**The core principle across all of these:** every failure has a defined, human-readable response. Nothing should ever just crash, hang forever, or silently lose the recording itself — the recording is the one thing in this product that can never be recreated if lost.

---

## 5. Edge Cases to Handle Before Launch

- **Empty or near-silent recording** — patient presses record and says nothing, or the mic fails. The system should detect this and let the patient (or caregiver) know rather than "processing" a blank file forever.
- **Patient tries to navigate away or close the app mid-recording** — the app should handle this gracefully rather than leaving a corrupted or half-saved recording behind.
- **Multiple caregivers editing at the same time** — e.g., two siblings both approving/editing the same recommended prompt within seconds of each other. The system needs a clear, consistent "who won" rule rather than silent data conflicts.
- **Caregiver revokes their own access by mistake** — there should always be at least one caregiver with access to a patient; the system shouldn't allow a family to accidentally lock everyone out.
- **Slow or unreliable home internet connection** — this is a very real condition for the target audience, not an edge case to deprioritize. Uploads should be resilient to a dropped connection mid-upload, with the ability to retry rather than restart from scratch.
- **A caregiver deletes a patient profile** — the audit log must survive this deletion regardless (for accountability), even though the patient's other data may be removed. This is a deliberate design decision, not an oversight.
- **PIN brute-force attempts** — repeated wrong PIN entries from the same device or session must be rate-limited, without punishing a genuinely confused patient who just needs a couple of retries.
- **AI produces a low-confidence or clearly wrong classification** — the system should surface the confidence score and reasoning to the caregiver rather than presenting an uncertain AI guess as settled fact.
- **AI infers something health/medical-related that wasn't explicitly said** — this is treated as a hard blocking failure, not a quality metric to tolerate at some acceptable error rate. Given the target user is an elderly person with a health condition, an AI-fabricated medical detail attached to their record is not an acceptable risk at any frequency.
- **Photo or family member entry with no name/relationship provided** — the system should require the minimum fields needed for the AI pipeline (especially entity matching) to function, rather than silently producing broken or unmatched data downstream.

---

*This document should be read alongside the Technical Architecture Document, which covers how these rules are implemented at the database and API level (authentication endpoints, schema-level access controls, and structured error responses).*
