"use client";

import { useState, useEffect } from "react";
import PatientSetupForm from "@/components/caregiver/PatientSetupForm";
import ConsentBanner from "@/components/caregiver/ConsentBanner";
import TimelineView, { RecordingItem } from "@/components/caregiver/TimelineView";
import SearchBar from "@/components/caregiver/SearchBar";
import InviteCaregiverModal from "@/components/caregiver/InviteCaregiverModal";
import AuditLogTable from "@/components/caregiver/AuditLogTable";
import KnowledgeGraphView from "@/components/caregiver/KnowledgeGraphView";
import SuggestedPromptsList, { SuggestedPromptItem } from "@/components/caregiver/SuggestedPromptsList";
import {
  listPatients,
  getPatientTimeline,
  searchPatientTimeline,
  listSuggestedPrompts,
  retryRecording,
  loginCaregiver,
  registerCaregiver
} from "@/lib/api";

export default function CaregiverDashboardPage() {
  const [activeTab, setActiveTab] = useState<"timeline" | "graph" | "prompts" | "setup" | "invite" | "audit">("timeline");
  const [patient, setPatient] = useState<{ id: string; name: string; has_consent: boolean } | null>(null);

  const [timelineGroups, setTimelineGroups] = useState<any[]>([]);
  const [allRecordings, setAllRecordings] = useState<RecordingItem[]>([]);
  const [searchResults, setSearchResults] = useState<RecordingItem[] | null>(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState<SuggestedPromptItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUnauthenticated, setIsUnauthenticated] = useState(false);

  // Auth Form State
  const [authEmail, setAuthEmail] = useState("caregiver@example.com");
  const [authPassword, setAuthPassword] = useState("Password123!");
  const [authName, setAuthName] = useState("Jane Doe");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authError, setAuthError] = useState("");
  const [submittingAuth, setSubmittingAuth] = useState(false);

  // Auto-load caregiver's accessible patient profile
  useEffect(() => {
    loadPatientData();
  }, []);

  async function loadPatientData() {
    setLoading(true);
    setIsUnauthenticated(false);
    try {
      const patients = await listPatients();
      if (patients && patients.length > 0) {
        const current = patients[0];
        setPatient({ id: current.id, name: current.name, has_consent: current.has_consent });
        await refreshPatientDetails(current.id);
      } else {
        setPatient(null);
      }
    } catch (err: any) {
      if (err.message && (err.message.includes("Not authenticated") || err.message.includes("status 401"))) {
        setIsUnauthenticated(true);
      } else {
        console.error("Failed to load patient profile:", err);
      }
    } finally {
      setLoading(false);
    }
  }

  const refreshPatientDetails = async (patientId: string) => {
    try {
      const tData = await getPatientTimeline(patientId);
      setPatient((prev) => (prev ? { ...prev, has_consent: tData.has_consent } : null));
      setTimelineGroups(tData.timeline || []);

      const recs: RecordingItem[] = [];
      if (tData.timeline) {
        for (const grp of tData.timeline) {
          if (grp.recordings) {
            recs.push(...grp.recordings);
          }
        }
      }
      setAllRecordings(recs);

      const sPrompts = await listSuggestedPrompts(patientId);
      setSuggestedPrompts(sPrompts || []);
    } catch (err) {
      console.error("Error refreshing patient details:", err);
    }
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingAuth(true);
    setAuthError("");

    try {
      if (authMode === "login") {
        await loginCaregiver(authEmail, authPassword);
      } else {
        await registerCaregiver(authName, authEmail, authPassword);
      }
      await loadPatientData();
    } catch (err: any) {
      setAuthError(err.message || "Authentication failed.");
    } finally {
      setSubmittingAuth(false);
    }
  };

  const handleDemoAuth = async () => {
    setSubmittingAuth(true);
    setAuthError("");

    try {
      // Try login first, fallback to register
      try {
        await loginCaregiver("demo_caregiver@example.com", "Password123!");
      } catch {
        await registerCaregiver("Demo Caregiver", "demo_caregiver@example.com", "Password123!");
      }
      await loadPatientData();
    } catch (err: any) {
      setAuthError(err.message || "Demo login failed.");
    } finally {
      setSubmittingAuth(false);
    }
  };

  const handleSearch = async (query: string) => {
    if (!patient) return;
    try {
      const results = await searchPatientTimeline(patient.id, query);
      setSearchResults(results);
    } catch (err) {
      console.error("Search failed:", err);
      setSearchResults([]);
    }
  };

  const handleRetryRecording = async (recordingId: string) => {
    if (!patient) return;
    try {
      await retryRecording(patient.id, recordingId);
      await refreshPatientDetails(patient.id);
    } catch (err) {
      console.error("Failed to retry recording:", err);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 text-[#FAF8F3] font-sans p-10 flex items-center justify-center text-2xl font-bold">
        Loading Caregiver Dashboard...
      </main>
    );
  }

  // Render Authentication Modal if Unauthenticated
  if (isUnauthenticated) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6 font-sans">
        <div className="w-full max-w-md bg-slate-900 p-8 rounded-3xl border border-slate-800 shadow-2xl space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-extrabold bg-gradient-to-r from-amber-200 via-rose-300 to-indigo-300 bg-clip-text text-transparent">
              Caregiver Portal
            </h1>
            <p className="text-slate-400 text-base">Please sign in to manage your family memory profile.</p>
          </div>

          {authError && (
            <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-500/30 text-rose-300 font-semibold text-sm">
              ⚠️ {authError}
            </div>
          )}

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            {authMode === "register" && (
              <div>
                <label className="block text-slate-300 text-sm font-semibold mb-1">Full Name</label>
                <input
                  type="text"
                  value={authName}
                  onChange={(e) => setAuthName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white text-base"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-slate-300 text-sm font-semibold mb-1">Email Address</label>
              <input
                type="email"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white text-base"
                required
              />
            </div>

            <div>
              <label className="block text-slate-300 text-sm font-semibold mb-1">Password</label>
              <input
                type="password"
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white text-base"
                required
              />
            </div>

            <button
              type="submit"
              disabled={submittingAuth}
              className="w-full py-4 min-h-[48px] rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold text-lg shadow-lg shadow-amber-500/20 transition cursor-pointer"
            >
              {submittingAuth ? "Authenticating..." : authMode === "login" ? "Sign In to Dashboard" : "Register Account"}
            </button>
          </form>

          <div className="pt-2 border-t border-slate-800 text-center space-y-3">
            <button
              type="button"
              onClick={handleDemoAuth}
              disabled={submittingAuth}
              className="w-full py-3 min-h-[44px] rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-base transition cursor-pointer"
            >
              ⚡ Instant Demo Caregiver Access
            </button>

            <button
              type="button"
              onClick={() => {
                setAuthMode(authMode === "login" ? "register" : "login");
                setAuthError("");
              }}
              className="text-amber-400 hover:underline text-sm font-medium"
            >
              {authMode === "login" ? "Need an account? Register here" : "Already have an account? Sign in"}
            </button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6 md:p-10 space-y-8">
      {/* Top Header */}
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h1 className="text-4xl font-extrabold bg-gradient-to-r from-amber-200 via-rose-300 to-indigo-300 bg-clip-text text-transparent">
            Caregiver Dashboard
          </h1>
          <p className="text-slate-400 text-lg mt-1">
            Managing Profile for <span className="text-amber-300 font-semibold">{patient ? patient.name : "New Patient"}</span>
          </p>
        </div>

        {/* Tab Navigation */}
        <nav className="flex flex-wrap gap-2 bg-slate-900 p-2 rounded-2xl border border-slate-800">
          <button
            onClick={() => setActiveTab("timeline")}
            className={`px-4 py-3 rounded-xl font-bold text-base min-h-[44px] transition cursor-pointer ${
              activeTab === "timeline" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Timeline & Search
          </button>
          <button
            onClick={() => setActiveTab("graph")}
            className={`px-4 py-3 rounded-xl font-bold text-base min-h-[44px] transition cursor-pointer ${
              activeTab === "graph" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Knowledge Graph
          </button>
          <button
            onClick={() => setActiveTab("prompts")}
            className={`px-4 py-3 rounded-xl font-bold text-base min-h-[44px] transition cursor-pointer ${
              activeTab === "prompts" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Prompts Review ({suggestedPrompts.filter((p) => !p.is_approved).length})
          </button>
          <button
            onClick={() => setActiveTab("setup")}
            className={`px-4 py-3 rounded-xl font-bold text-base min-h-[44px] transition cursor-pointer ${
              activeTab === "setup" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Profile Setup
          </button>
          <button
            onClick={() => setActiveTab("invite")}
            className={`px-4 py-3 rounded-xl font-bold text-base min-h-[44px] transition cursor-pointer ${
              activeTab === "invite" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Invite Relative
          </button>
          <button
            onClick={() => setActiveTab("audit")}
            className={`px-4 py-3 rounded-xl font-bold text-base min-h-[44px] transition cursor-pointer ${
              activeTab === "audit" ? "bg-amber-500 text-slate-950 shadow-md" : "text-slate-300 hover:text-white"
            }`}
          >
            Audit Log & Telemetry
          </button>
        </nav>
      </div>

      <div className="max-w-6xl mx-auto space-y-8">
        {/* Required Consent Banner */}
        {patient && (
          <ConsentBanner
            patientId={patient.id}
            hasConsent={patient.has_consent}
            onConsentSubmitted={() => refreshPatientDetails(patient.id)}
          />
        )}

        {/* Tab Content */}
        {activeTab === "timeline" && (
          <div className="space-y-8">
            {patient && <SearchBar onSearch={handleSearch} onClear={() => setSearchResults(null)} />}
            
            {/* Recommended Prompts Review Widget */}
            {patient && suggestedPrompts.length > 0 && (
              <SuggestedPromptsList
                patientId={patient.id}
                prompts={suggestedPrompts}
                onPromptApproved={() => refreshPatientDetails(patient.id)}
              />
            )}

            <TimelineView
              recordings={searchResults !== null ? searchResults : allRecordings}
              onRetry={patient ? handleRetryRecording : undefined}
            />
          </div>
        )}

        {activeTab === "graph" && patient && <KnowledgeGraphView patientId={patient.id} />}

        {activeTab === "prompts" && patient && (
          <SuggestedPromptsList
            patientId={patient.id}
            prompts={suggestedPrompts}
            onPromptApproved={() => refreshPatientDetails(patient.id)}
          />
        )}

        {activeTab === "setup" && (
          <PatientSetupForm
            onPatientCreated={(p) => {
              setPatient({ id: p.id, name: p.name, has_consent: false });
              refreshPatientDetails(p.id);
              setActiveTab("timeline");
            }}
          />
        )}

        {activeTab === "invite" && patient && <InviteCaregiverModal patientId={patient.id} />}

        {activeTab === "audit" && <AuditLogTable />}
      </div>
    </main>
  );
}
