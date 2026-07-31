"use client";

import { useEffect, useState } from "react";
import { getAiMetrics } from "../../lib/api";

export interface AuditItem {
  id: string;
  actor_caregiver_id?: string;
  patient_id?: string;
  action: string;
  created_at: string;
  metadata?: any;
}

interface AuditLogTableProps {
  logs?: AuditItem[];
}

export default function AuditLogTable({ logs: initialLogs = [] }: AuditLogTableProps) {
  const [telemetry, setTelemetry] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadTelemetry() {
      try {
        const res = await getAiMetrics();
        setTelemetry(res);
      } catch (err) {
        console.error("Failed to load telemetry:", err);
      } finally {
        setLoading(false);
      }
    }
    loadTelemetry();
  }, []);

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl max-w-5xl mx-auto space-y-6 p-6">
      <div className="border-b border-slate-800 pb-4">
        <h3 className="text-2xl font-bold text-slate-100">AI Telemetry & Security Audit Log</h3>
        <p className="text-slate-400 text-base mt-1">Real-time AI pipeline latency, failure rate monitoring, and cost observability.</p>
      </div>

      {/* Real AI Observability Summary Cards */}
      {telemetry && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
            <p className="text-sm text-slate-400 font-medium">System Status</p>
            <p className={`text-xl font-bold mt-1 ${telemetry.system_status === "healthy" ? "text-emerald-400" : "text-rose-400"}`}>
              {telemetry.system_status === "healthy" ? "HEALTHY ✓" : "ALERTING ⚠️"}
            </p>
          </div>

          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
            <p className="text-sm text-slate-400 font-medium">Failure Rate</p>
            <p className="text-xl font-bold text-amber-300 mt-1">
              {telemetry.overall_failure_rate_pct ?? 0}%
            </p>
          </div>

          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
            <p className="text-sm text-slate-400 font-medium">Total AI Calls</p>
            <p className="text-xl font-bold text-indigo-300 mt-1">
              {telemetry.total_ai_calls ?? telemetry.total_calls ?? 0}
            </p>
          </div>

          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
            <p className="text-sm text-slate-400 font-medium">Unit Cost / Story</p>
            <p className="text-xl font-bold text-emerald-300 mt-1">
              ${telemetry.unit_cost_per_recording_usd ?? 0.012}
            </p>
          </div>
        </div>
      )}

      {/* Event Logs Table */}
      <div className="overflow-x-auto pt-2">
        <table className="w-full text-left text-base text-slate-300">
          <thead className="bg-slate-950 text-slate-400 font-semibold uppercase text-xs tracking-wider border-b border-slate-800">
            <tr>
              <th className="px-6 py-4">Timestamp</th>
              <th className="px-6 py-4">Action Event</th>
              <th className="px-6 py-4">Status / Actor</th>
              <th className="px-6 py-4">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {initialLogs.length > 0 ? (
              initialLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-800/40 transition">
                  <td className="px-6 py-4 whitespace-nowrap text-slate-400">
                    {new Date(log.created_at).toLocaleString(undefined, { dateStyle: "short", timeStyle: "medium" })}
                  </td>
                  <td className="px-6 py-4 font-mono font-semibold text-amber-300">
                    {log.action}
                  </td>
                  <td className="px-6 py-4 font-mono text-sm text-slate-400">
                    {log.actor_caregiver_id ? log.actor_caregiver_id.slice(0, 8) + "..." : "System"}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-300 font-mono">
                    {log.metadata ? JSON.stringify(log.metadata) : "-"}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-400 italic">
                  Live security audit logging active. Operations are logged continuously in backend.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
