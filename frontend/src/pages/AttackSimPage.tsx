import React, { useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { JsonViewer } from '../components/JsonViewer';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { AlertBanner } from '../components/AlertBanner';
import {
  Bug,
  Play,
  ShieldCheck,
  ShieldAlert,
  Clock,
  FileMinus,
  KeyRound,
  ArrowDownCircle,
  FileCode,
} from 'lucide-react';

export const AttackSimPage: React.FC = () => {
  const [activeAttack, setActiveAttack] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, any>>({});
  const [loadingAttack, setLoadingAttack] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const attacks = [
    {
      id: 'tampering',
      name: 'Message Tampering',
      icon: Bug,
      category: 'Data Integrity',
      description:
        'Adversary alters meterStop readings in StopTransaction to falsify electricity billing totals.',
      fn: () => api.simulateTampering(),
    },
    {
      id: 'collision',
      name: 'Legacy MD5 Collision Bypass',
      icon: ShieldAlert,
      category: 'Cryptanalytic Exploit',
      description:
        'Exploits verified differential MD5 collision pair to substitute payload while matching 128-bit MD5 digest.',
      fn: () => api.simulateCollision(),
    },
    {
      id: 'replay',
      name: 'Replay Attack (Stale Token)',
      icon: Clock,
      category: 'Session Security',
      description:
        'Captures legitimate historic Authorize frame and injects it outside the 300s freshness window.',
      fn: () => api.simulateReplay(),
    },
    {
      id: 'missing_meta',
      name: 'Metadata Stripping',
      icon: FileMinus,
      category: 'Envelope Bypass',
      description:
        'Strips cryptographic envelope completely, attempting to trigger legacy fail-open CSMS behavior.',
      fn: () => api.simulateMissingMetadata(),
    },
    {
      id: 'invalid_tag',
      name: 'Forged HMAC-SHA3-256 Tag',
      icon: KeyRound,
      category: 'Authentication Forgery',
      description:
        'Injects arbitrary 256-bit authentication tag without knowledge of the CSMS secret key.',
      fn: () => api.simulateInvalidTag(),
    },
    {
      id: 'downgrade',
      name: 'Algorithm Downgrade Attempt',
      icon: ArrowDownCircle,
      category: 'Protocol Negotiation',
      description:
        'Forces connection downgrade to broken legacy MD5 on an HMAC-SHA3-256 enforced channel.',
      fn: () => api.simulateDowngrade(),
    },
    {
      id: 'firmware_mod',
      name: 'Firmware Metadata Modification',
      icon: FileCode,
      category: 'Supply Chain',
      description:
        'Falsifies FirmwareStatusNotification to report rogue firmware as legitimately installed.',
      fn: () => api.simulateFirmwareMod(),
    },
    {
      id: 'unkeyed_recomp',
      name: 'MITM Unkeyed Digest Recomputation',
      icon: KeyRound,
      category: 'Cryptographic Integrity vs Authenticity',
      description:
        'Alters payload and recomputes unkeyed SHA3-256 digest. Evades unkeyed detection; fails against HMAC authentication.',
      fn: () => api.simulateUnkeyedRecomputation(),
    },
  ];

  const runAttack = async (attack: (typeof attacks)[0]) => {
    setLoadingAttack(attack.id);
    setActiveAttack(attack.id);
    setError(null);
    try {
      const data = await attack.fn();
      setResults((prev) => ({ ...prev, [attack.id]: data }));
    } catch (err: any) {
      setError(`Simulation '${attack.name}' failed. Ensure backend is running.`);
    } finally {
      setLoadingAttack(null);
    }
  };

  const runAllAttacks = async () => {
    for (const at of attacks) {
      await runAttack(at);
    }
  };

  const activeResult = activeAttack ? results[activeAttack] : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-lg">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-950/80 border border-rose-800/60 text-rose-400 text-xs font-mono mb-2">
              <Bug className="w-3.5 h-3.5" />
              Controlled Red-Team Laboratory
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Attack Simulation & Defense Verification Lab
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Test seven real-world attack vectors against EVHashGuard's cryptographic defenses.
              All simulations run locally in offline test sandboxes without impacting production networks.
            </p>
          </div>

          <button
            onClick={runAllAttacks}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-rose-600/20 transition self-start sm:self-auto"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run All 7 Simulations</span>
          </button>
        </div>

        {error && <p className="text-xs text-rose-400 font-mono mt-3">{error}</p>}
      </div>

      {/* Grid of 7 Attack Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {attacks.map((at) => {
          const Icon = at.icon;
          const res = results[at.id];
          const isCurrentLoading = loadingAttack === at.id;
          const isSelected = activeAttack === at.id;

          return (
            <div
              key={at.id}
              onClick={() => setActiveAttack(at.id)}
              className={`p-5 rounded-2xl border transition cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-slate-900 border-cyan-500 shadow-lg shadow-cyan-500/10 ring-1 ring-cyan-500'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/90'
              }`}
            >
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-cyan-400">
                    <Icon className="w-4 h-4" />
                  </div>
                  {res && (
                    <StatusBadge status={res.detected ? 'DETECTED' : 'UNDETECTED'} />
                  )}
                </div>

                <span className="text-[10px] uppercase font-mono text-slate-500 block">
                  {at.category}
                </span>
                <h4 className="text-sm font-bold text-white mt-0.5">{at.name}</h4>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">{at.description}</p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-mono">
                  {res ? 'Tested' : 'Ready'}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    runAttack(at);
                  }}
                  disabled={isCurrentLoading}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5 disabled:opacity-50"
                >
                  <Play className="w-3 h-3 fill-current" />
                  <span>{isCurrentLoading ? 'Testing...' : 'Simulate'}</span>
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {loadingAttack && <LoadingSpinner label={`Simulating ${loadingAttack} attack vector...`} />}

      {/* Selected Attack Deep Dive Result */}
      {activeResult && (
        <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div>
              <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">
                Simulation Detailed Output
              </span>
              <h3 className="text-lg font-bold text-white mt-0.5">{activeResult.attack_name}</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Defense Verdict:</span>
              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                  activeResult.detected
                    ? 'bg-emerald-950/80 border-emerald-800 text-emerald-400'
                    : 'bg-rose-950/80 border-rose-800 text-rose-400'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                {activeResult.detected ? 'ATTACK DETECTED & BLOCKED' : 'ATTACK EVADED DEFENSES'}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1.5">
              <span className="text-slate-500 font-mono block text-[10px] uppercase">
                Expected Defense Behavior
              </span>
              <p className="text-slate-200 leading-relaxed font-mono">
                {activeResult.expected_result}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-1.5">
              <span className="text-slate-500 font-mono block text-[10px] uppercase">
                Actual System Response
              </span>
              <p className="text-emerald-400 leading-relaxed font-mono font-semibold">
                {activeResult.actual_result}
              </p>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-white">Detection Mechanism Applied:</span>
              <span className="font-mono text-cyan-400">{activeResult.detection_method}</span>
            </div>
            <p className="text-slate-300 leading-relaxed pt-2 border-t border-slate-900">
              {activeResult.security_explanation}
            </p>
          </div>

          {activeResult.input_message && (
            <div>
              <p className="text-xs font-mono text-slate-400 mb-2">Simulated Attack Payload:</p>
              <JsonViewer
                data={activeResult.input_message}
                title="Red-Team Injected Message Frame"
                maxHeight="max-h-60"
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
};
