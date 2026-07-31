"use client";

import { useState } from "react";
import { generateCaregiverInvite, claimCaregiverInvite } from "@/lib/api";

interface InviteCaregiverModalProps {
  patientId: string;
}

export default function InviteCaregiverModal({ patientId }: InviteCaregiverModalProps) {
  const [inviteCode, setInviteCode] = useState("");
  const [claimCode, setClaimCode] = useState("");
  const [claimSuccess, setClaimSuccess] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [generating, setGenerating] = useState(false);
  const [claiming, setClaiming] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    setErrorMsg("");
    try {
      const res = await generateCaregiverInvite(patientId, "contributor");
      setInviteCode(res.invite_code);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate invite code.");
    } finally {
      setGenerating(false);
    }
  };

  const handleClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claimCode.trim()) return;
    setClaiming(true);
    setErrorMsg("");
    setClaimSuccess("");

    try {
      await claimCaregiverInvite(claimCode.trim());
      setClaimSuccess("Invite claimed successfully! Contributor access granted.");
      setClaimCode("");
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to claim invite. Invalid or expired code.");
    } finally {
      setClaiming(false);
    }
  };

  return (
    <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-8 max-w-2xl mx-auto shadow-xl">
      <div>
        <h3 className="text-2xl font-bold text-slate-100">Share Access with Another Caregiver</h3>
        <p className="text-slate-400 text-lg mt-1">Invite a sibling or relative to collaborate on this patient record.</p>
      </div>

      {errorMsg && <p className="text-rose-400 font-semibold text-lg bg-rose-950/40 p-3 rounded-xl border border-rose-500/30">{errorMsg}</p>}

      {/* Generate Invite Code */}
      <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
        <h4 className="text-xl font-semibold text-amber-300">Generate Contributor Invite</h4>
        <p className="text-slate-300 text-base">Generate an invite code that grants read and prompt management access.</p>
        
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-6 py-3 min-h-[48px] bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-slate-950 font-bold text-lg rounded-xl transition cursor-pointer"
        >
          {generating ? "Generating..." : "Generate Invite Code"}
        </button>

        {inviteCode && (
          <div className="mt-4 p-4 bg-slate-900 rounded-xl border border-amber-500/40 space-y-2">
            <p className="text-sm text-amber-400 font-semibold">Shareable Invite Code:</p>
            <p className="text-lg font-mono text-white break-all select-all">{inviteCode}</p>
          </div>
        )}
      </div>

      {/* Claim Invite Code */}
      <div className="p-6 rounded-xl bg-slate-950 border border-slate-800 space-y-4">
        <h4 className="text-xl font-semibold text-indigo-300">Claim an Invite Code</h4>
        
        <form onSubmit={handleClaim} className="space-y-4">
          <input
            type="text"
            value={claimCode}
            onChange={(e) => setClaimCode(e.target.value)}
            placeholder="Paste invite code here..."
            className="w-full px-4 py-3 rounded-xl bg-slate-900 border border-slate-700 text-white text-lg font-mono"
          />

          <button
            type="submit"
            disabled={claiming || !claimCode.trim()}
            className="px-6 py-3 min-h-[48px] bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-lg rounded-xl transition cursor-pointer"
          >
            {claiming ? "Claiming..." : "Claim Access"}
          </button>
        </form>

        {claimSuccess && <p className="text-emerald-400 text-lg font-semibold">{claimSuccess}</p>}
      </div>
    </div>
  );
}
