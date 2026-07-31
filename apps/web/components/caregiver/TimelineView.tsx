"use client";

export interface RecordingItem {
  id: string;
  patient_id: string;
  audio_url: string;
  transcript?: string;
  theme?: string;
  estimated_decade?: string;
  ai_caption?: string;
  recorded_at: string;
  processing_status: string;
  failure_stage?: string;
}

interface TimelineViewProps {
  recordings: RecordingItem[];
  onRetry?: (recordingId: string) => void;
}

export default function TimelineView({ recordings, onRetry }: TimelineViewProps) {
  if (recordings.length === 0) {
    return (
      <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800 text-slate-400 text-xl max-w-5xl mx-auto">
        No memory recordings found in the timeline.
      </div>
    );
  }

  // Group recordings by decade/theme
  const groups: Record<string, RecordingItem[]> = {};
  for (const r of recordings) {
    const key = r.estimated_decade || r.theme || "Uncategorized";
    if (!groups[key]) groups[key] = [];
    groups[key].push(r);
  }

  const getStatusBadge = (rec: RecordingItem) => {
    switch (rec.processing_status) {
      case "done":
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">✓ Processed</span>;
      case "failed":
        return (
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">
              ⚠️ Failed ({rec.failure_stage || "pipeline"})
            </span>
            {onRetry && (
              <button
                onClick={() => onRetry(rec.id)}
                className="px-2 py-1 text-xs font-bold rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 transition cursor-pointer"
              >
                Retry 🔄
              </button>
            )}
          </div>
        );
      default:
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
            ⏳ Processing ({rec.processing_status})
          </span>
        );
    }
  };

  return (
    <div className="space-y-10 max-w-5xl mx-auto">
      {Object.entries(groups).map(([groupTitle, recList]) => (
        <div key={groupTitle} className="space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
            <span className="w-3 h-3 rounded-full bg-[#C97B4A]"></span>
            <h3 className="text-2xl font-bold text-slate-100 tracking-wide">{groupTitle}</h3>
            <span className="text-sm text-slate-400 font-normal">({recList.length} memory recordings)</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {recList.map((rec) => (
              <div
                key={rec.id}
                className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition shadow-lg space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-400">
                      {new Date(rec.recorded_at).toLocaleDateString(undefined, { dateStyle: "medium" })}
                    </span>
                    {getStatusBadge(rec)}
                  </div>

                  {rec.ai_caption && (
                    <h4 className="text-xl font-semibold text-amber-200 leading-snug">
                      "{rec.ai_caption}"
                    </h4>
                  )}

                  {rec.transcript ? (
                    <p className="text-slate-300 text-lg leading-relaxed line-clamp-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                      {rec.transcript}
                    </p>
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 text-slate-500 text-base italic">
                      Transcript is currently generating...
                    </div>
                  )}
                </div>

                <div className="pt-2">
                  <audio
                    controls
                    src={rec.audio_url}
                    className="w-full h-12 rounded-lg accent-[#2E5D4E]"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
