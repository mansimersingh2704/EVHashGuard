import React, { useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { AlertBanner } from '../components/AlertBanner';
import { ShieldAlert, Play, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';

export const LegacyMD5Page: React.FC = () => {
  const [payloadText, setPayloadText] = useState<string>(
    JSON.stringify(
      {
        stationId: 'CS-NORDIC-001',
        action: 'MeterValues',
        connectorId: 1,
        meterValue: 142850,
        unit: 'Wh',
      },
      null,
      2
    )
  );

  // Pre-computed canonical MD5 for this sample payload
  const [legacyMd5, setLegacyMd5] = useState<string>('00000000000000000000000000000000');
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleComputeLegit = async () => {
    setLoading(true);
    setError(null);
    try {
      // Use hash lab route to get genuine MD5
      const hData = await api.compareHashes(payloadText, ['md5']);
      const trueMd5 = hData.results[0].digest;
      setLegacyMd5(trueMd5);

      const vData = await api.legacyVerify(payloadText, trueMd5);
      setResult(vData);
    } catch (err: any) {
      setError('Computation failed. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateTamper = async () => {
    setLoading(true);
    setError(null);
    try {
      // Alter the payload without updating the legacy MD5 digest
      const tampered = JSON.stringify(
        {
          stationId: 'CS-NORDIC-001',
          action: 'MeterValues',
          connectorId: 1,
          meterValue: 999999, // tampered value
          unit: 'Wh',
        },
        null,
        2
      );
      setPayloadText(tampered);

      const vData = await api.legacyVerify(tampered, legacyMd5);
      setResult(vData);
    } catch (err: any) {
      setError('Tamper simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-950/80 border border-amber-800/60 text-amber-400 text-xs font-mono mb-2">
              <ShieldAlert className="w-3.5 h-3.5" />
              Legacy Firmware Verification Engine
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              Legacy MD5 Integrity System Simulation
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Demonstrates how legacy charging management software performs naive MD5 digest checks.
              While capable of detecting accidental transmission bit-flips, it fails fundamentally against
              deliberate cryptographic collision attacks.
            </p>
          </div>
        </div>

        {/* Inputs */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5">
              Simulated Firmware / OCPP Payload JSON
            </label>
            <textarea
              value={payloadText}
              onChange={(e) => setPayloadText(e.target.value)}
              rows={6}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-cyan-300 focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="flex flex-col justify-between">
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1.5">
                Legacy MD5 Digest (128-bit Hex)
              </label>
              <input
                type="text"
                value={legacyMd5}
                onChange={(e) => setLegacyMd5(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-amber-400 focus:outline-none focus:border-amber-500"
                placeholder="e.g. 79054025255fb1a26e4bc422aef54eb4"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                Transported via legacy proprietary header <code className="text-slate-400">X-OCPP-Legacy-MD5</code>.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 mt-4">
              <button
                onClick={handleComputeLegit}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-600/20 transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Compute & Verify Genuine</span>
              </button>

              <button
                onClick={handleSimulateTamper}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-rose-600/20 transition disabled:opacity-50"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Inject Tampered Meter (Bypass Check)</span>
              </button>
            </div>
          </div>
        </div>

        {error && <p className="text-xs text-rose-400 font-mono mt-3">{error}</p>}
      </div>

      {loading && <LoadingSpinner label="Validating legacy integrity..." />}

      {/* Verification Result Card */}
      {result && (
        <div className="space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-white">Legacy MD5 Verification Status:</span>
                {result.verified ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-950/80 border border-emerald-800 text-emerald-400">
                    <CheckCircle2 className="w-4 h-4" />
                    LEGACY DIGEST MATCH (PASS)
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950/80 border border-rose-800 text-rose-400">
                    <XCircle className="w-4 h-4" />
                    DIGEST MISMATCH (TAMPER DETECTED)
                  </span>
                )}
              </div>
              <StatusBadge status={result.verified ? 'WEAK_PASS' : 'FAIL'} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">COMPUTED PAYLOAD MD5</span>
                <span className="text-amber-400 font-bold break-all">{result.computed_digest}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">PROVIDED LEGACY MD5</span>
                <span className="text-cyan-400 font-bold break-all">{result.provided_digest}</span>
              </div>
            </div>

            <AlertBanner
              type={result.verified ? 'warning' : 'error'}
              title="False Sense of Security in Legacy Systems"
              message={result.security_warning}
            />
          </div>
        </div>
      )}
    </div>
  );
};
