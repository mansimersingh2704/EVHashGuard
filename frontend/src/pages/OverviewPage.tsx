import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StatCard } from '../components/StatCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { StatusBadge } from '../components/StatusBadge';
import {
  ShieldCheck,
  Radio,
  Bug,
  Activity,
  Layers,
  ArrowUpCircle,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

export const OverviewPage: React.FC = () => {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getDashboardStats();
      setStats(data);
    } catch (err: any) {
      setError('Unable to connect to EVHashGuard backend. Ensure FastAPI server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  if (loading && !stats) {
    return <LoadingSpinner label="Fetching telemetry and audit metrics..." />;
  }

  if (error) {
    return (
      <div className="p-8 text-center bg-rose-950/20 border border-rose-900 rounded-2xl">
        <p className="text-rose-400 font-mono mb-4">{error}</p>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-sm font-medium transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  // Format algorithm distribution for charts
  const algoData = Object.entries(stats.algorithm_usage || {}).map(([key, val]) => ({
    name: key,
    count: val,
  }));

  const COLORS = ['#06b6d4', '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

  return (
    <div className="space-y-6">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-blue-950/60 via-slate-900/60 to-cyan-950/60 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-800/60 text-cyan-400 text-xs font-mono mb-3">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            Active Posture: {stats.security_posture}
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">
            EV Firmware Cryptographic Migration Framework
          </h2>
          <p className="text-slate-300 text-sm mt-2 leading-relaxed">
            Eliminating MD5 collision vulnerability in legacy OCPP 1.6 charging systems through a backward-compatible
            cryptographic envelope pipeline without altering downstream message parsers.
          </p>
        </div>
      </div>

      {/* 4 Top KPI Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Messages Processed"
          value={stats.total_messages_processed}
          subtitle="OCPP 1.6-J frames ingested"
          icon={Radio}
          color="cyan"
        />
        <StatCard
          title="Verifications"
          value={stats.successful_verifications}
          subtitle={`${stats.failed_verifications} rejected invalid tags`}
          icon={ShieldCheck}
          color="emerald"
        />
        <StatCard
          title="Attacks Blocked"
          value={stats.tampering_and_attacks_detected}
          subtitle={`Out of ${stats.total_attacks_simulated} simulations`}
          icon={Bug}
          color="rose"
        />
        <StatCard
          title="Active Stations"
          value={stats.active_charging_stations}
          subtitle="Monitored charging endpoints"
          icon={Layers}
          color="blue"
        />
      </div>

      {/* Analytics Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Algorithm Usage Chart */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Cryptographic Algorithm Distribution
            </h3>
            <span className="text-xs text-slate-500 font-mono">SQLite Live Logs</span>
          </div>
          {algoData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={algoData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} angle={-15} textAnchor="end" />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    labelStyle={{ color: '#94a3b8' }}
                  />
                  <Bar dataKey="count" fill="#3b82f6" radius={[6, 6, 0, 0]}>
                    {algoData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-500 text-xs font-mono">
              Execute hash lab or EV simulator tasks to generate telemetry
            </div>
          )}
        </div>

        {/* Security Posture Summary Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-white tracking-wide flex items-center gap-2">
                <ArrowUpCircle className="w-4 h-4 text-emerald-400" />
                Migration Pipeline Health
              </h3>
              <StatusBadge status="RECOMMENDED" />
            </div>
            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-300">Legacy MD5 Deprecation</span>
                <span className="font-mono text-amber-400 font-semibold">Strict Quarantine</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-300">Target Algorithm</span>
                <span className="font-mono text-cyan-400 font-semibold">SHA3-256 (Keccak)</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-300">Authenticated Transport</span>
                <span className="font-mono text-emerald-400 font-semibold">HMAC-SHA3-256</span>
              </div>
              <div className="flex justify-between items-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                <span className="text-slate-300">Total Migrated Envelopes</span>
                <span className="font-mono text-white font-bold">{stats.total_migrations}</span>
              </div>
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-500 flex justify-between">
            <span>Deterministic JSON Canonicalization: RFC 8785</span>
            <span className="text-cyan-400 font-mono">Active</span>
          </div>
        </div>
      </div>

      {/* Recent Security Audit Events Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <h3 className="text-sm font-semibold text-white tracking-wide mb-4">
          Recent Security Audit Timeline
        </h3>
        {stats.recent_security_events && stats.recent_security_events.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 bg-slate-950/40">
                <tr>
                  <th className="py-2.5 px-3">Event Type</th>
                  <th className="py-2.5 px-3">Station</th>
                  <th className="py-2.5 px-3">Algorithm</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Details</th>
                  <th className="py-2.5 px-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {stats.recent_security_events.map((ev: any) => (
                  <tr key={ev.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-semibold text-white">{ev.event_type}</td>
                    <td className="py-2.5 px-3 text-cyan-400">{ev.station_id || 'CSMS-CORE'}</td>
                    <td className="py-2.5 px-3 text-slate-300">{ev.algorithm || '—'}</td>
                    <td className="py-2.5 px-3">
                      <StatusBadge status={ev.status} />
                    </td>
                    <td className="py-2.5 px-3 max-w-xs truncate text-slate-400">{ev.details}</td>
                    <td className="py-2.5 px-3 text-slate-500 text-[11px]">
                      {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-xs text-slate-500 font-mono">No security events logged yet.</p>
        )}
      </div>
    </div>
  );
};
