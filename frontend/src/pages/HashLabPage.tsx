import React, { useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { AlertBanner } from '../components/AlertBanner';
import { FlaskConical, Play, CheckSquare, Square, Info } from 'lucide-react';

export const HashLabPage: React.FC = () => {
  const [message, setMessage] = useState<string>(
    '{"chargePointVendor":"NordicVolt","firmwareVersion":"v1.4.2","meterStart":142850,"status":"Available"}'
  );
  const [selectedAlgos, setSelectedAlgos] = useState<string[]>([
    'md5',
    'sha1',
    'sha256',
    'sha3_256',
  ]);
  const [results, setResults] = useState<any[] | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const availableAlgos = [
    { id: 'md5', label: 'MD5 (128-bit)', broken: true },
    { id: 'sha1', label: 'SHA-1 (160-bit)', broken: true },
    { id: 'sha256', label: 'SHA-256 (256-bit)', broken: false },
    { id: 'sha3_256', label: 'SHA3-256 (Keccak 256-bit)', broken: false },
  ];

  const toggleAlgo = (id: string) => {
    setSelectedAlgos((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  const handleCompute = async () => {
    if (selectedAlgos.length === 0) {
      setError('Please select at least one algorithm');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.compareHashes(message, selectedAlgos);
      setResults(data.results);
    } catch (err: any) {
      setError('Failed to compute hashes. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const loadSample = (type: string) => {
    if (type === 'plain') {
      setMessage('EV Charging Session Authorized: RFID-TAG-99014-ALPHA');
    } else if (type === 'json') {
      setMessage(
        JSON.stringify(
          {
            connectorId: 1,
            errorCode: 'NoError',
            info: 'DC Fast Charge 150kW in progress',
            status: 'Charging',
            powerKW: 148.4,
            timestamp: new Date().toISOString(),
          },
          null,
          2
        )
      );
    } else if (type === 'firmware') {
      setMessage(
        'FIRMWARE_HEADER: Vendor=NordicVolt; Model=TerraCharge; Build=2026.04.1; DigestRequirement=SHA3-256'
      );
    }
  };

  return (
    <div className="space-y-6">
      {/* Introduction Card */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-cyan-400" />
              Cryptographic Hash Laboratory
            </h3>
            <p className="text-xs text-slate-300 mt-1">
              Evaluate cryptographic digest behaviors, output bit lengths, and execution latency side by side.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => loadSample('plain')}
              className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            >
              Plain Text
            </button>
            <button
              onClick={() => loadSample('json')}
              className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            >
              OCPP JSON
            </button>
            <button
              onClick={() => loadSample('firmware')}
              className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition"
            >
              Firmware Meta
            </button>
          </div>
        </div>

        {/* Input Text Area */}
        <div className="mt-4">
          <label className="block text-xs font-mono text-slate-400 mb-1.5">
            Input Message / Firmware Telemetry String
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition"
            placeholder="Type or paste payload message..."
          />
        </div>

        {/* Algorithm Selectors & Action Button */}
        <div className="mt-4 flex flex-wrap items-center justify-between gap-4 pt-3 border-t border-slate-800/80">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs text-slate-400 font-medium">Select Algorithms:</span>
            {availableAlgos.map((algo) => {
              const selected = selectedAlgos.includes(algo.id);
              return (
                <button
                  key={algo.id}
                  onClick={() => toggleAlgo(algo.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition border ${
                    selected
                      ? 'bg-blue-950/80 border-blue-600 text-blue-300'
                      : 'bg-slate-950 border-slate-800 text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {selected ? (
                    <CheckSquare className="w-3.5 h-3.5 text-blue-400" />
                  ) : (
                    <Square className="w-3.5 h-3.5 text-slate-600" />
                  )}
                  <span>{algo.label}</span>
                </button>
              );
            })}
          </div>

          <button
            onClick={handleCompute}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-cyan-600/20 transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{loading ? 'Computing...' : 'Run Cryptographic Benchmark'}</span>
          </button>
        </div>

        {error && <p className="text-xs text-rose-400 font-mono mt-3">{error}</p>}
      </div>

      {loading && <LoadingSpinner label="Running cryptographic hashing engines..." />}

      {/* Results Comparison Grid */}
      {results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold text-white">Comparative Hash Results</h4>
            <span className="text-xs text-slate-500 font-mono">
              Input: {message.length} characters ({new Blob([message]).size} bytes)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((res) => (
              <div
                key={res.algorithm}
                className={`p-5 rounded-2xl border transition shadow-lg ${
                  res.security_status === 'RECOMMENDED'
                    ? 'bg-slate-900/80 border-emerald-800/60'
                    : res.security_status === 'SECURE'
                    ? 'bg-slate-900/80 border-blue-800/60'
                    : res.security_status === 'WEAK'
                    ? 'bg-slate-900/80 border-amber-800/60'
                    : 'bg-slate-900/80 border-rose-900/60'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-white uppercase font-mono">
                      {res.algorithm}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">
                      ({res.digest_length} bits)
                    </span>
                  </div>
                  <StatusBadge status={res.security_status} />
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 mb-3">
                  <p className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mb-1">
                    Digest Hex Output
                  </p>
                  <p className="font-mono text-xs text-cyan-300 break-all leading-relaxed select-all">
                    {res.digest}
                  </p>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                  <span>Execution Latency:</span>
                  <span className="font-mono text-slate-200 font-semibold">
                    {res.execution_time_ms} ms
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed border-t border-slate-800/80 pt-2.5">
                  {res.security_description}
                </p>
              </div>
            ))}
          </div>

          <AlertBanner
            type="info"
            title="Important Cryptographic Accuracy Principle"
            message="An unkeyed cryptographic digest verifies data integrity against accidental bit corruption, NOT sender authenticity. An attacker without key material can recompute unkeyed digests (MD5, SHA-1, SHA-256, SHA3-256) over tampered payloads. Message authenticity requires HMAC or digital signatures."
          />
        </div>
      )}

      {/* Educational Cryptographic Concepts Reference */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 shadow-lg">
        <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
          <Info className="w-4 h-4 text-cyan-400" />
          Cryptographic Security Properties Reference
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <h5 className="font-semibold text-white mb-1">Collision Resistance</h5>
            <p className="text-slate-400 leading-relaxed">
              Computationally infeasible to find ANY two disparate inputs <code className="text-cyan-400">m1 ≠ m2</code> such that <code className="text-cyan-400">H(m1) = H(m2)</code>. MD5 completely fails this property.
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <h5 className="font-semibold text-white mb-1">Preimage Resistance</h5>
            <p className="text-slate-400 leading-relaxed">
              Given digest <code className="text-cyan-400">y</code>, computationally infeasible to find <code className="text-cyan-400">m</code> such that <code className="text-cyan-400">H(m) = y</code>. (One-way property).
            </p>
          </div>
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80">
            <h5 className="font-semibold text-white mb-1">Second-Preimage Resistance</h5>
            <p className="text-slate-400 leading-relaxed">
              Given specific input <code className="text-cyan-400">m1</code>, computationally infeasible to find a different <code className="text-cyan-400">m2 ≠ m1</code> such that <code className="text-cyan-400">H(m1) = H(m2)</code>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
