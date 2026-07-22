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
}

interface TimelineViewProps {
  recordings: RecordingItem[];
}

export default function TimelineView({ recordings }: TimelineViewProps) {
  if (recordings.length === 0) {
    return (
      <div className="p-12 text-center bg-slate-900/50 rounded-2xl border border-slate-800 text-slate-400 text-xl">
        No recordings found in the timeline yet.
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

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "done":
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">✓ Processed</span>;
      case "failed":
        return <span className="px-3 py-1 text-xs font-semibold rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40">⚠️ Processing Failed (Retry Available)</span>;
      default:
        return (
          <span className="px-3 py-1 text-xs font-semibold rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse">
            ⏳ Still Processing ({status})
          </span>
        );
    }
  };

  return (
    <div className="space-y-10 max-w-5xl mx-auto">
      {Object.entries(groups).map(([groupTitle, recList]) => (
        <div key={groupTitle} className="space-y-4">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
            <span className="w-3 h-3 rounded-full bg-amber-400"></span>
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
                    {getStatusBadge(rec.processing_status)}
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
                    className="w-full h-12 rounded-lg accent-amber-500"
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
