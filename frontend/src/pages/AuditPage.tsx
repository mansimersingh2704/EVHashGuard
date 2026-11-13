import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { FileText, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react';

export const AuditPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [limit, setLimit] = useState<number>(25);
  const [offset, setOffset] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async (currentOffset: number = offset, currentLimit: number = limit) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getAuditLogs(currentLimit, currentOffset);
      setLogs(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError('Failed to fetch audit log entries from backend SQLite.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(offset, limit);
  }, [offset, limit]);

  const handleNext = () => {
    if (offset + limit < total) {
      setOffset(offset + limit);
    }
  };

  const handlePrev = () => {
    if (offset - limit >= 0) {
      setOffset(offset - limit);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-950/80 border border-blue-800/60 text-blue-400 text-xs font-mono mb-2">
            <FileText className="w-3.5 h-3.5" />
            Immutable Audit Trail
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            Security Audit Logs & Event Journal
          </h3>
          <p className="text-xs text-slate-300 mt-1">
            Real-time persisted SQLite log entries recording all cryptographic evaluations,
            simulated attacks, and envelope verification decisions.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={limit}
            onChange={(e) => {
              setLimit(Number(e.target.value));
              setOffset(0);
            }}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-white focus:outline-none"
          >
            <option value={10}>10 per page</option>
            <option value={25}>25 per page</option>
            <option value={50}>50 per page</option>
            <option value={100}>100 per page</option>
          </select>

          <button
            onClick={() => fetchLogs(offset, limit)}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl transition flex items-center gap-1.5 text-xs px-3"
            title="Refresh logs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Sync</span>
          </button>
        </div>
      </div>

      {loading && <LoadingSpinner label="Fetching audit entries from SQLite..." />}

      {error && (
        <div className="p-6 text-center bg-rose-950/20 border border-rose-900 rounded-2xl">
          <p className="text-rose-400 font-mono text-xs">{error}</p>
        </div>
      )}

      {/* Logs Table */}
      {!loading && !error && (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 font-mono">
            <span>
              Showing {logs.length > 0 ? offset + 1 : 0}–{Math.min(offset + limit, total)} of {total} events
            </span>
          </div>

          {logs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 bg-slate-950/60">
                  <tr>
                    <th className="py-2.5 px-3">ID</th>
                    <th className="py-2.5 px-3">Event Type</th>
                    <th className="py-2.5 px-3">Station / Origin</th>
                    <th className="py-2.5 px-3">Algorithm</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Journal Details</th>
                    <th className="py-2.5 px-3">Timestamp (UTC)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                  {logs.map((item) => (
                    <tr key={item.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-2.5 px-3 text-slate-500 font-bold">#{item.id}</td>
                      <td className="py-2.5 px-3 font-semibold text-white">{item.event_type}</td>
                      <td className="py-2.5 px-3 text-cyan-400">{item.station_id || 'CSMS-EDGE'}</td>
                      <td className="py-2.5 px-3 text-slate-300">{item.algorithm || '—'}</td>
                      <td className="py-2.5 px-3">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="py-2.5 px-3 max-w-sm truncate text-slate-400" title={item.details}>
                        {item.details}
                      </td>
                      <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                        {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs font-mono">
              No audit logs recorded in SQLite database yet. Perform actions across Hash Lab, EV Simulator, or Attack Simulator.
            </div>
          )}

          {/* Pagination Controls */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-800/80 text-xs font-mono">
            <button
              onClick={handlePrev}
              disabled={offset === 0}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed transition"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Previous</span>
            </button>

            <span className="text-slate-500">
              Page {Math.floor(offset / limit) + 1} of {Math.max(1, Math.ceil(total / limit))}
            </span>

            <button
              onClick={handleNext}
              disabled={offset + limit >= total}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed transition"
            >
              <span>Next</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
