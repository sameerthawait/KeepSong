"use client";

import { useState } from "react";

export interface SuggestedPromptItem {
  id: string;
  patient_id: string;
  prompt_text: string;
  is_approved: boolean;
  created_at: string;
}

interface SuggestedPromptsListProps {
  prompts: SuggestedPromptItem[];
  onApprove: (id: string) => void;
}

export default function SuggestedPromptsList({ prompts, onApprove }: SuggestedPromptsListProps) {
  const [approvedIds, setApprovedIds] = useState<string[]>([]);

  const handleApprove = (id: string) => {
    setApprovedIds((prev) => [...prev, id]);
    onApprove(id);
  };

  const visiblePrompts = prompts.filter((p) => !approvedIds.includes(p.id));

  if (visiblePrompts.length === 0) {
    return null;
  }

  return (
    <div className="p-6 rounded-2xl bg-amber-950/40 border-2 border-amber-500/40 space-y-4 max-w-4xl mx-auto shadow-xl">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-2xl font-bold text-amber-300">Recommended Follow-Up Prompts</h3>
          <p className="text-slate-300 text-base mt-1">
            Generated from stories mentioned in passing. <span className="font-semibold text-amber-200">Requires caregiver approval before patient sees it.</span>
          </p>
        </div>
        <span className="px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full border border-amber-500/40 text-xs font-bold uppercase tracking-wider">
          Review Queue
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
              className="px-5 py-3 min-h-[44px] rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-base shadow-md shrink-0 transition"
            >
              Approve & Add to Queue ✓
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
