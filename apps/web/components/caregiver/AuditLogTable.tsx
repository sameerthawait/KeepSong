"use client";

export interface AuditItem {
  id: string;
  actor_caregiver_id?: string;
  patient_id?: string;
  action: string;
  created_at: string;
  metadata?: any;
}

interface AuditLogTableProps {
  logs: AuditItem[];
}

export default function AuditLogTable({ logs }: AuditLogTableProps) {
  if (logs.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-2xl border border-slate-800 text-slate-400 text-lg">
        No audit log history recorded yet.
      </div>
    );
  }

  return (
    <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden shadow-xl max-w-5xl mx-auto">
      <div className="p-6 border-b border-slate-800">
        <h3 className="text-2xl font-bold text-slate-100">Access History & Security Audit Log</h3>
        <p className="text-slate-400 text-base mt-1">Immutable record of data access and configuration changes.</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-base text-slate-300">
          <thead className="bg-slate-950 text-slate-400 font-semibold uppercase text-xs tracking-wider border-b border-slate-800">
            <tr>
              <th className="px-6 py-4">Timestamp</th>
              <th className="px-6 py-4">Action Event</th>
              <th className="px-6 py-4">Actor ID</th>
              <th className="px-6 py-4">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {logs.map((log) => (
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
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
