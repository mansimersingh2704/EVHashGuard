import React, { useState } from 'react';
import { api } from '../services/api';
import { JsonViewer } from '../components/JsonViewer';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { AlertBanner } from '../components/AlertBanner';
import {
  ArrowUpCircle,
  ShieldCheck,
  Play,
  ArrowRight,
  Layers,
  KeyRound,
  Lock,
} from 'lucide-react';

export const MigrationPage: React.FC = () => {
  const [mode, setMode] = useState<string>('sha3_256');
  const [payloadJson, setPayloadJson] = useState<string>(
    JSON.stringify(
      {
        station_id: 'CS-NORDIC-001',
        message_id: 'ocpp-msg-88910-dc50',
        message_type: 'MeterValues',
        ocpp_message: [
          2,
          'ocpp-msg-88910-dc50',
          'MeterValues',
          {
            connectorId: 1,
            transactionId: 10429,
            meterValue: [
              {
                timestamp: new Date().toISOString(),
                sampledValue: [
                  {
                    value: '142850',
                    context: 'Sample.Periodic',
                    format: 'Raw',
                    measurand: 'Energy.Active.Import.Register',
                    unit: 'Wh',
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      2
    )
  );

  const [wrappedResponse, setWrappedResponse] = useState<any | null>(null);
  const [verifyResult, setVerifyResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleWrap = async () => {
    setLoading(true);
    setError(null);
    setVerifyResult(null);
    try {
      const parsed = JSON.parse(payloadJson);
      const res = await api.migrationWrap(parsed, mode);
      setWrappedResponse(res.wrapped_message);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Wrap operation failed. Check JSON format.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!wrappedResponse) {
      setError('Please wrap a message first before verifying.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.migrationVerify(wrappedResponse, mode);
      setVerifyResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Verification failed.');
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
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-800/60 text-emerald-400 text-xs font-mono mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              Core Research Innovation
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              SHA-3 Backward-Compatible Cryptographic Wrapper
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-3xl leading-relaxed">
              Enables legacy OCPP 1.6 charging systems to upgrade from broken MD5 integrity checks to
              modern NIST FIPS 202 SHA3-256 and authenticated HMAC-SHA3-256 envelopes without requiring
              any modifications to downstream legacy message parsers.
            </p>
          </div>
        </div>

        {/* Pipeline Architecture Flowchart (HTML/CSS) */}
        <div className="mt-6 p-4 rounded-xl bg-slate-950/80 border border-slate-800/80">
          <p className="text-[11px] font-mono text-slate-400 uppercase tracking-wider mb-3">
            In-Transit Wrapper Processing Pipeline
          </p>
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono text-center flex-1 min-w-[120px]">
              <span className="block text-[10px] text-slate-500">INGRESS</span>
              Incoming Message
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <div className="px-3 py-2 rounded-lg bg-cyan-950/60 border border-cyan-800 text-cyan-300 font-mono text-center flex-1 min-w-[140px] shadow-sm">
              <span className="block text-[10px] text-cyan-500">STAGE 1</span>
              EVHashGuard Wrapper
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <div className="px-3 py-2 rounded-lg bg-blue-950/60 border border-blue-800 text-blue-300 font-mono text-center flex-1 min-w-[140px]">
              <span className="block text-[10px] text-blue-500">STAGE 2</span>
              Deterministic Canonicalize
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <div className="px-3 py-2 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 font-mono text-center flex-1 min-w-[140px]">
              <span className="block text-[10px] text-emerald-500">STAGE 3</span>
              SHA3 / HMAC Tag Check
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <div className="px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono text-center flex-1 min-w-[130px]">
              <span className="block text-[10px] text-slate-500">EGRESS</span>
              Legacy CSMS Parser
            </div>
          </div>
        </div>

        {/* Mode Selector */}
        <div className="mt-6 flex flex-wrap items-center gap-4">
          <span className="text-xs text-slate-400 font-medium">Migration Mode:</span>
          <div className="flex flex-wrap gap-2">
            {[
              { id: 'legacy_md5', label: 'Legacy MD5 (Unsafe)', icon: Layers },
              { id: 'sha3_256', label: 'SHA3-256 (Integrity Enveloped)', icon: Lock },
              { id: 'hmac_sha3_256', label: 'HMAC-SHA3-256 (Authenticated)', icon: KeyRound },
            ].map((m) => {
              const Icon = m.icon;
              const active = mode === m.id;
              return (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-mono transition border ${
                    active
                      ? 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-600/30 font-semibold'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{m.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Controls */}
        <div className="mt-4 flex flex-wrap gap-3 justify-end">
          <button
            onClick={handleWrap}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-cyan-600/20 transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Wrap Payload Envelope</span>
          </button>

          {wrappedResponse && (
            <button
              onClick={handleVerify}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-emerald-600/20 transition disabled:opacity-50"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Verify Wrapped Envelope</span>
            </button>
          )}
        </div>

        {error && <p className="text-xs text-rose-400 font-mono mt-3">{error}</p>}
      </div>

      {loading && <LoadingSpinner label="Executing cryptographic wrapping pipeline..." />}

      {/* Editor & Wrapped Viewer Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Left: Input Payload */}
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1.5 flex justify-between">
            <span>OCPP Payload to Wrap (Preserved 100% Unaltered)</span>
            <span className="text-slate-500 font-mono">RFC 8785 Canonical Target</span>
          </label>
          <textarea
            value={payloadJson}
            onChange={(e) => setPayloadJson(e.target.value)}
            rows={14}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Right: Enveloped Output */}
        <div>
          <label className="block text-xs font-mono text-slate-400 mb-1.5 flex justify-between">
            <span>EVHashGuard Wrapped Output</span>
            {wrappedResponse && (
              <span className="text-emerald-400 font-mono text-[11px]">
                Algorithm: {wrappedResponse.crypto_metadata?.algorithm}
              </span>
            )}
          </label>
          {wrappedResponse ? (
            <JsonViewer
              data={wrappedResponse}
              title="Wrapped Message with Out-of-Band Cryptographic Metadata"
              maxHeight="max-h-[345px]"
            />
          ) : (
            <div className="h-[345px] rounded-xl border border-dashed border-slate-800 bg-slate-950/40 flex flex-col items-center justify-center p-6 text-center text-slate-500 text-xs">
              <ArrowUpCircle className="w-8 h-8 mb-2 text-slate-600" />
              <span>Click "Wrap Payload Envelope" to generate the cryptographic envelope</span>
            </div>
          )}
        </div>
      </div>

      {/* Verification Result Banner */}
      {verifyResult && (
        <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              Verification & Legacy Parser Dispatch Outcome
            </h4>
            <StatusBadge status={verifyResult.verified ? 'PASS' : 'FAIL'} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">ALGORITHM APPLIED</span>
              <span className="text-cyan-400 font-bold">{verifyResult.algorithm}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">VERIFICATION RESULT</span>
              <span className={verifyResult.verified ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
                {verifyResult.verified ? 'VALID CRYPTOGRAPHIC TAG' : 'VERIFICATION FAILED'}
              </span>
            </div>
            <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-slate-500 block text-[10px]">LEGACY PARSER DISPATCH</span>
              <span className="text-slate-300 font-bold">
                {verifyResult.verified ? 'Forwarded to CSMS Parser' : 'Quarantined at Edge'}
              </span>
            </div>
          </div>

          <AlertBanner
            type={verifyResult.verified ? 'success' : 'error'}
            title="Integrity Verification Summary"
            message={verifyResult.details}
          />
        </div>
      )}
    </div>
  );
};
