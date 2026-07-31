const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

let caregiverToken: string | null = null;
let patientToken: string | null = null;

export function setCaregiverToken(token: string | null) {
  caregiverToken = token;
}

export function setPatientToken(token: string | null) {
  patientToken = token;
}

export async function fetchApi<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const token = caregiverToken || patientToken;
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `API request failed with status ${res.status}`);
  }

  return res.json();
}

// ----------------------------------------------------
// Authentication API Calls
// ----------------------------------------------------

export async function loginCaregiver(email: string, password: string) {
  const data = await fetchApi("/auth/caregiver/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (data.access_token) {
    setCaregiverToken(data.access_token);
  }
  return data;
}

export async function registerCaregiver(name: string, email: string, password: string) {
  const data = await fetchApi("/auth/caregiver/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
  if (data.access_token) {
    setCaregiverToken(data.access_token);
  }
  return data;
}

export async function verifyPatientPin(patientId: string, pin: string) {
  const data = await fetchApi("/auth/patient/verify-pin", {
    method: "POST",
    body: JSON.stringify({ patient_id: patientId, pin }),
  });
  if (data.access_token) {
    setPatientToken(data.access_token);
  }
  return data;
}

// ----------------------------------------------------
// Patient Profile & Setup API Calls
// ----------------------------------------------------

export async function createPatient(name: string, pin: string = "1234") {
  return fetchApi("/patients", {
    method: "POST",
    body: JSON.stringify({ name, pin }),
  });
}

export async function listPatients() {
  return fetchApi("/patients", { method: "GET" });
}

export async function getPatientProfile(patientId: string) {
  return fetchApi(`/patients/${patientId}`, { method: "GET" });
}

export async function addFamilyMember(patientId: string, name: string, relationship: string, photoUrl?: string) {
  return fetchApi(`/patients/${patientId}/family-members`, {
    method: "POST",
    body: JSON.stringify({ name, relationship, photo_url: photoUrl }),
  });
}

export async function listFamilyMembers(patientId: string) {
  return fetchApi(`/patients/${patientId}/family-members`, { method: "GET" });
}

export async function addStoryPrompt(patientId: string, promptText: string, sequenceOrder?: number) {
  return fetchApi(`/patients/${patientId}/prompts`, {
    method: "POST",
    body: JSON.stringify({ prompt_text: promptText, sequence_order: sequenceOrder, is_custom: true }),
  });
}

export async function listStoryPrompts(patientId: string) {
  return fetchApi(`/patients/${patientId}/prompts`, { method: "GET" });
}

export async function recordConsent(patientId: string, consentBasis: string) {
  return fetchApi(`/patients/${patientId}/consent`, {
    method: "POST",
    body: JSON.stringify({ consent_basis: consentBasis }),
  });
}

export async function getConsentStatus(patientId: string) {
  return fetchApi(`/patients/${patientId}/consent`, { method: "GET" });
}

export async function generateCaregiverInvite(patientId: string, role: string = "contributor") {
  return fetchApi(`/patients/${patientId}/invite-caregiver`, {
    method: "POST",
    body: JSON.stringify({ role }),
  });
}

export async function claimCaregiverInvite(inviteCode: string) {
  return fetchApi("/patients/claim-invite", {
    method: "POST",
    body: JSON.stringify({ invite_code: inviteCode }),
  });
}

// ----------------------------------------------------
// Patient Check-In & Audio Recording API Calls
// ----------------------------------------------------

export async function getPatientCheckIn(patientId: string) {
  return fetchApi(`/patients/${patientId}/checkin`, { method: "GET" });
}

export async function requestUploadUrl(patientId: string, contentType: string, fileSize: number, filename?: string) {
  return fetchApi(`/patients/${patientId}/upload-url`, {
    method: "POST",
    body: JSON.stringify({
      content_type: contentType,
      file_size: fileSize,
      category: "audio",
      filename: filename || "checkin_recording.webm",
    }),
  });
}

export async function createRecording(patientId: string, audioUrl: string, promptId?: string, durationSeconds?: number) {
  return fetchApi(`/patients/${patientId}/recordings`, {
    method: "POST",
    body: JSON.stringify({
      audio_url: audioUrl,
      prompt_id: promptId,
      duration_seconds: durationSeconds,
    }),
  });
}

export async function retryRecording(patientId: string, recordingId: string) {
  return fetchApi(`/patients/${patientId}/recordings/${recordingId}/retry`, {
    method: "POST",
  });
}

// ----------------------------------------------------
// Timeline & Hybrid Vector Search API Calls
// ----------------------------------------------------

export async function getPatientTimeline(patientId: string) {
  return fetchApi(`/patients/${patientId}/timeline`, { method: "GET" });
}

export async function searchPatientTimeline(patientId: string, query: string) {
  const params = new URLSearchParams({ q: query });
  return fetchApi(`/patients/${patientId}/timeline/search?${params.toString()}`, { method: "GET" });
}

// ----------------------------------------------------
// Knowledge Graph & AI Recommendation API Calls
// ----------------------------------------------------

export async function getKnowledgeGraph(patientId: string) {
  return fetchApi(`/patients/${patientId}/graph`, { method: "GET" });
}

export async function listSuggestedPrompts(patientId: string) {
  return fetchApi(`/patients/${patientId}/suggested-prompts`, { method: "GET" });
}

export async function approveSuggestedPrompt(patientId: string, promptId: string) {
  return fetchApi(`/patients/${patientId}/suggested-prompts/${promptId}/approve`, {
    method: "POST",
  });
}

export async function suggestPhotoCaption(patientId: string, photoUrl: string, name?: string, relationship?: string) {
  return fetchApi(`/patients/${patientId}/photos/suggest-caption`, {
    method: "POST",
    body: JSON.stringify({
      photo_url: photoUrl,
      family_member_name: name,
      relationship: relationship,
    }),
  });
}

// ----------------------------------------------------
// Admin Observability & Telemetry API Calls
// ----------------------------------------------------

export async function getAiMetrics() {
  return fetchApi("/admin/ai-metrics", { method: "GET" });
}
