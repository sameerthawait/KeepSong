"use client";

import { useState } from "react";
import PatientSetupForm from "@/components/caregiver/PatientSetupForm";
import ConsentBanner from "@/components/caregiver/ConsentBanner";
import TimelineView, { RecordingItem } from "@/components/caregiver/TimelineView";
import SearchBar from "@/components/caregiver/SearchBar";
import InviteCaregiverModal from "@/components/caregiver/InviteCaregiverModal";
import AuditLogTable, { AuditItem } from "@/components/caregiver/AuditLogTable";

export default function CaregiverDashboardPage() {
  const [activeTab, setActiveTab] = useState<"timeline" | "setup" | "invite" | "audit">("timeline");

  // Mock patient state
  const [patient, setPatient] = useState<{ id: string; name: string; has_consent: boolean }>({
    id: "mock-patient-101",
    name: "John Doe",
    has_consent: false,
  });

  // Seed recordings mock data matching prompt requirements
  const [recordings, setRecordings] = useState<RecordingItem[]>([
    {
      id: "rec-1",
      patient_id: "mock-patient-101",
      audio_url: "https://storage.googleapis.com/keepsong-mock/audio1.mp3",
      transcript: "I had a dog named Buster when I was ten. He was a black retriever. He would follow me everywhere, even to the bus stop.",
      theme: "childhood",
      estimated_decade: "1960s",
      ai_caption: "John shares a memory about Buster, his retriever dog.",
      recorded_at: "2026-07-20T10:30:00Z",
      processing_status: "done",
    },
    {
      id: "rec-2",
      patient_id: "mock-patient-101",
      audio_url: "https://storage.googleapis.com/keepsong-mock/audio2.mp3",
      transcript: "My first job was at the local bakery. I used to get up at five in the morning to bake fresh sourdough.",
      theme: "career",
      estimated_decade: "1970s",
      ai_caption: "John talks about working at the local bakery in the early mornings.",
      recorded_at: "2026-07-21T09:15:00Z",
      processing_status: "done",
    },
    {
      id: "rec-3",
      patient_id: "mock-patient-101",
      audio_url: "https://storage.googleapis.com/keepsong-mock/audio3.mp3",
      transcript: "",
      theme: "family",
      estimated_decade: "1980s",
      ai_caption: "Recent check-in recording.",
      recorded_at: "2026-07-21T21:00:00Z",
      processing_status: "transcribing",
    },
  ]);

  const [filteredRecordings, setFilteredRecordings] = useState<RecordingItem[] | null>(null);

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState<AuditItem[]>([
    { id: "a1", action: "CREATE_PATIENT", created_at: "2026-07-19T10:00:00Z", metadata: { patient: "John Doe" } },
    { id: "a2", action: "VIEW_TIMELINE", created_at: "2026-07-21T18:00:00Z", metadata: { path: "/patients/101/timeline" } },
  ]);

  const handleConsentSubmitted = () => {
    setPatient({ ...patient, has_consent: true });
    setAuditLogs([
      { id: `a-${Date.now()}`, action: "RECORD_CONSENT", created_at: new Date().toISOString(), metadata: { basis: "proxy" } },
      ...auditLogs,
    ]);
  };

  const handleSearch = (query: string) => {
    const q = query.toLowerCase();
    const synonyms: Record<string, string[]> = {
      dog: ["buster", "retriever", "pet", "puppy"],
      wedding: ["marriage", "bride", "romance"],
      bakery: ["bread", "sourdough", "work", "job"],
    };

    let terms = [q];
    for (const [key, syns] of Object.entries(synonyms)) {
      if (key.includes(q) || q.includes(key)) {
        terms.push(...syns);
      }
    }

    const matched = recordings.filter((r) => {
      const text = `${r.transcript} ${r.ai_caption} ${r.theme} ${r.estimated_decade}`.toLowerCase();
      return terms.some((t) => text.includes(t));
    });

    setFilteredRecordings(matched);
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6 md:p-10 space-y-8">
      {/* Top Header */}
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-amber-200 via-rose-300 to-indigo-300 bg-clip-text text-transparent">
            Caregiver Dashboard
          </h1>
          <p className="text-slate-400 text-lg mt-1">
            Managing Profile for <span className="text-amber-300 font-semibold">{patient.name}</span>
          </p>
        </div>

        {/* Tab Navigation */}
        <nav className="flex flex-wrap gap-2 bg-slate-900 p-2 rounded-2xl border border-slate-800">
          <button
            onClick={() => setActiveTab("timeline")}
            className={`px-5 py-3 rounded-xl font-bold text-base min-h-[44px] transition ${
              activeTab === "timeline" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Timeline & Search
          </button>
          <button
            onClick={() => setActiveTab("setup")}
            className={`px-5 py-3 rounded-xl font-bold text-base min-h-[44px] transition ${
              activeTab === "setup" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Profile Setup
          </button>
          <button
            onClick={() => setActiveTab("invite")}
            className={`px-5 py-3 rounded-xl font-bold text-base min-h-[44px] transition ${
              activeTab === "invite" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Invite Relative
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`px-5 py-3 rounded-xl font-bold text-base min-h-[44px] transition ${
              activeTab === "audit" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Audit Log
          </button>
        </nav>
      </div>

      <div className="max-w-6xl mx-auto space-y-8">
        {/* Required Consent Banner */}
        <ConsentBanner hasConsent={patient.has_consent} onConsentSubmitted={handleConsentSubmitted} />

        {/* Tab Content */}
        {activeTab === "timeline" && (
          <div className="space-y-8">
            <SearchBar onSearch={handleSearch} onClear={() => setFilteredRecordings(null)} />
            <TimelineView recordings={filteredRecordings !== null ? filteredRecordings : recordings} />
          </div>
        )}

        {activeTab === "setup" && (
          <PatientSetupForm
            onPatientCreated={(p) => {
              setPatient({ id: p.id, name: p.name, has_consent: false });
              setActiveTab("timeline");
            }}
          />
        )}

        {activeTab === "invite" && <InviteCaregiverModal patientId={patient.id} />}

        {activeTab === "audit" && <AuditLogTable logs={auditLogs} />}
      </div>
    </main>
  );
}
