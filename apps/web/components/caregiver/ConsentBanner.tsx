"use client";

import { useState } from "react";
import { recordConsent } from "@/lib/api";

interface ConsentBannerProps {
  patientId: string;
  hasConsent: boolean;
  onConsentSubmitted: () => void;
}

export default function ConsentBanner({ patientId, hasConsent, onConsentSubmitted }: ConsentBannerProps) {
  const [consentBasis, setConsentBasis] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  if (hasConsent) {
    return (
      <div className="mb-6 p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">✓</span>
          <div>
            <p className="font-semibold text-lg">Consent On File</p>
            <p className="text-sm text-emerald-300/80">Recording features are enabled for this patient profile.</p>
          </div>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consentBasis.trim()) return;
    setSubmitting(true);
    setError("");

    try {
      // Call real backend consent endpoint
      await recordConsent(patientId, consentBasis.trim());
      onConsentSubmitted();
    } catch (err: any) {
      setError(err.message || "Failed to record consent.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mb-8 p-6 rounded-2xl bg-amber-950/50 border-2 border-amber-500/60 text-amber-100 shadow-xl">
      <div className="flex items-start gap-4">
        <span className="text-3xl text-amber-400">⚠️</span>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-amber-300">Required Consent Record</h2>
          <p className="mt-2 text-lg text-amber-200/90 leading-relaxed">
            Before daily voice check-ins can be recorded, you must confirm consent has been granted or proxy consent is logged on behalf of the patient.
          </p>

          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div>
              <label htmlFor="consent_basis" className="block text-base font-semibold text-amber-200 mb-2">
                Consent Basis / Legal Authority
              </label>
              <textarea
                id="consent_basis"
                rows={2}
                value={consentBasis}
                onChange={(e) => setConsentBasis(e.target.value)}
                placeholder="e.g. Granted by patient or legal power of attorney proxy consent signed on file."
                className="w-full rounded-xl bg-slate-900 border border-amber-500/40 px-4 py-3 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500 text-lg"
                required
              />
            </div>

            {error && <p className="text-rose-400 text-base font-medium">{error}</p>}

            <button
              type="submit"
              disabled={submitting || !consentBasis.trim()}
              className="px-6 py-3 min-h-[48px] rounded-xl bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold text-lg transition shadow-lg shadow-amber-500/20 cursor-pointer"
            >
              {submitting ? "Recording Consent..." : "Record & Enable Check-Ins"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
