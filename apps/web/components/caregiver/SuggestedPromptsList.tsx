"use client";

import { useState } from "react";
import { approveSuggestedPrompt } from "../../lib/api";

export interface SuggestedPromptItem {
  id: string;
  patient_id: string;
  prompt_text: string;
  is_approved: boolean;
  created_at: string;
}

interface SuggestedPromptsListProps {
  patientId: string;
  prompts: SuggestedPromptItem[];
  onPromptApproved?: () => void;
}

export default function SuggestedPromptsList({ patientId, prompts, onPromptApproved }: SuggestedPromptsListProps) {
  const [approvedIds, setApprovedIds] = useState<string[]>([]);
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleApprove = async (id: string) => {
    setLoadingId(id);
    try {
      // Real API call to approval endpoint (copies to StoryPrompt for patient checkin view)
      await approveSuggestedPrompt(patientId, id);
      setApprovedIds((prev) => [...prev, id]);
      if (onPromptApproved) onPromptApproved();
    } catch (err) {
      console.error("Failed to approve prompt:", err);
    } finally {
      setLoadingId(null);
    }
  };

  const visiblePrompts = prompts.filter((p) => !p.is_approved && !approvedIds.includes(p.id));

  if (visiblePrompts.length === 0) {
    return null;
  }

  return (
    <div className="p-6 rounded-2xl bg-amber-950/40 border-2 border-amber-500/40 space-y-4 max-w-5xl mx-auto shadow-xl">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div>
          <h3 className="text-2xl font-bold text-amber-300">Recommended Follow-Up Prompts</h3>
          <p className="text-slate-300 text-base mt-1">
            Generated from stories mentioned in passing. <span className="font-semibold text-amber-200">Requires caregiver approval before patient sees it.</span>
          </p>
        </div>
        <span className="px-3 py-1 bg-[#2E5D4E] text-white rounded-full border border-emerald-400 text-xs font-bold uppercase tracking-wider shrink-0">
          AI suggestion — please review
        </span>
      </div>

      <div className="space-y-3 pt-2">
        {visiblePrompts.map((item) => (
          <div
            key={item.id}
            className="p-5 rounded-xl bg-slate-900 border border-slate-700 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
          >
            <p className="text-lg font-semibold text-slate-100 italic">"{item.prompt_text}"</p>
            <button
              onClick={() => handleApprove(item.id)}
              disabled={loadingId === item.id}
              className="px-5 py-3 min-h-[44px] rounded-xl bg-[#3A7D5C] hover:bg-[#2E5D4E] disabled:opacity-50 text-white font-bold text-base shadow-md shrink-0 transition cursor-pointer"
            >
              {loadingId === item.id ? "Approving..." : "Approve & Add to Queue ✓"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
