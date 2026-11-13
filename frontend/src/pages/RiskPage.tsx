import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { AlertBanner } from '../components/AlertBanner';
import {
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Clock,
  Compass,
} from 'lucide-react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  Tooltip,
} from 'recharts';

export const RiskPage: React.FC = () => {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        setLoading(true);
        const report = await api.getRiskAnalysis();
        setData(report);
      } catch (err) {
        setError('Failed to fetch risk analysis.');
      } finally {
        setLoading(false);
      }
    };
    fetchRisk();
  }, []);

  if (loading) return <LoadingSpinner label="Compiling qualitative risk evaluation..." />;

  if (error || !data) {
    return (
      <div className="p-8 text-center bg-rose-950/20 border border-rose-900 rounded-2xl">
        <p className="text-rose-400 font-mono">{error || 'No risk data available'}</p>
      </div>
    );
  }

  // Radar data mapping qualitative security attributes onto a 1-5 scale for visual comparison
  const radarData = [
    { property: 'Collision Resistance', MD5: 1, 'SHA-1': 2, 'SHA-256': 5, 'SHA3-256': 5, 'HMAC-SHA3': 5 },
    { property: 'Preimage Resistance', MD5: 3, 'SHA-1': 4, 'SHA-256': 5, 'SHA3-256': 5, 'HMAC-SHA3': 5 },
    { property: 'Authentication Capability', MD5: 1, 'SHA-1': 1, 'SHA-256': 1, 'SHA3-256': 1, 'HMAC-SHA3': 5 },
    { property: 'Length-Extension Immunity', MD5: 1, 'SHA-1': 1, 'SHA-256': 1, 'SHA3-256': 5, 'HMAC-SHA3': 5 },
    { property: 'NIST Standards Compliance', MD5: 1, 'SHA-1': 2, 'SHA-256': 5, 'SHA3-256': 5, 'HMAC-SHA3': 5 },
    { property: 'EVSE Hardware Suitability', MD5: 1, 'SHA-1': 2, 'SHA-256': 5, 'SHA3-256': 5, 'HMAC-SHA3': 5 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-950/80 border border-amber-800/60 text-amber-400 text-xs font-mono mb-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              NIST SP 800-131A & FIPS 202 Compliant
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Cryptographic Risk Analysis & Evaluation Matrix
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-3xl leading-relaxed">
              Transparent qualitative comparative evaluation of cryptographic hash and MAC algorithms
              in legacy EV charging firmware deployments.
            </p>
          </div>
        </div>
      </div>

      {/* Radar Chart & Key Takeaways Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar Chart */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
          <div>
            <h4 className="text-sm font-semibold text-white mb-2">
              Cryptographic Security Profile Radar
            </h4>
            <p className="text-xs text-slate-400 mb-4">
              Comparative security bounds across 6 cryptographic dimensions (Scale: 1 [Broken] to 5 [Maximum Assurance]).
            </p>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData} outerRadius="75%">
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="property" stroke="#94a3b8" fontSize={10} />
                <PolarRadiusAxis angle={30} domain={[0, 5]} stroke="#475569" fontSize={9} />
                <Radar name="MD5" dataKey="MD5" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
                <Radar name="SHA-256" dataKey="SHA-256" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.15} />
                <Radar name="SHA3-256" dataKey="SHA3-256" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.25} />
                <Radar name="HMAC-SHA3" dataKey="HMAC-SHA3" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Executive Summary & Roadmap */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg space-y-4">
          <h4 className="text-sm font-semibold text-white flex items-center gap-2">
            <Compass className="w-4 h-4 text-cyan-400" />
            Executive Synthesis & Roadmap
          </h4>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-xs text-slate-300 leading-relaxed">
            {data.executive_summary}
          </div>

          <div className="space-y-2.5">
            <span className="text-[11px] uppercase font-mono text-slate-400 block tracking-wider">
              Phased Migration Roadmap
            </span>
            {data.migration_roadmap.map((phase: any, idx: number) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start gap-3 text-xs"
              >
                <div className="w-6 h-6 rounded-lg bg-blue-950 border border-blue-800 text-blue-400 flex items-center justify-center font-bold text-xs flex-shrink-0 mt-0.5">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-white">{phase.phase}</span>
                    <span className="text-[10px] text-cyan-400 font-mono">{phase.timeline}</span>
                  </div>
                  <p className="text-slate-400 text-[11px] leading-relaxed">{phase.action}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Comprehensive Risk Matrix Table */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <h4 className="text-sm font-semibold text-white mb-4">
          Comparative Cryptographic Risk Matrix
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 bg-slate-950/60">
              <tr>
                <th className="py-3 px-3">Algorithm</th>
                <th className="py-3 px-3">Family & Construction</th>
                <th className="py-3 px-3">Collision Resistance</th>
                <th className="py-3 px-3">Preimage Resistance</th>
                <th className="py-3 px-3">NIST Guidance</th>
                <th className="py-3 px-3">Overall Risk</th>
                <th className="py-3 px-3">EVSE Suitability</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
              {data.evaluations.map((algo: any) => (
                <tr key={algo.algorithm} className="hover:bg-slate-800/40 transition">
                  <td className="py-3 px-3 font-bold text-white">{algo.algorithm}</td>
                  <td className="py-3 px-3 text-slate-400 text-[11px]">{algo.family}</td>
                  <td className="py-3 px-3">
                    <span
                      className={`font-semibold ${
                        algo.collision_resistance === 'BROKEN'
                          ? 'text-rose-400'
                          : algo.collision_resistance === 'RECOMMENDED' ||
                            algo.collision_resistance === 'EXCELLENT'
                          ? 'text-emerald-400'
                          : 'text-blue-400'
                      }`}
                    >
                      {algo.collision_resistance}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-slate-400">{algo.preimage_resistance}</td>
                  <td className="py-3 px-3 max-w-xs truncate text-[11px] text-slate-400">
                    {algo.nist_status}
                  </td>
                  <td className="py-3 px-3">
                    <StatusBadge status={algo.overall_risk} />
                  </td>
                  <td className="py-3 px-3">
                    {algo.suitable_for_ev_firmware ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Approved
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-rose-400 font-semibold">
                        <XCircle className="w-3.5 h-3.5" />
                        Disallowed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
