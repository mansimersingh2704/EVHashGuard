import React, { useState } from 'react';
import { api } from '../services/api';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { AlertBanner } from '../components/AlertBanner';
import { Zap, Play, FileCode, CheckCircle2, XCircle, RotateCcw } from 'lucide-react';

export const CollisionPage: React.FC = () => {
  const [input1Hex, setInput1Hex] = useState<string>('');
  const [input2Hex, setInput2Hex] = useState<string>('');
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadKnownVectors = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.verifyCollision();
      setInput1Hex(data.input1_hex);
      setInput2Hex(data.input2_hex);
      setResult(data);
    } catch (err: any) {
      setError('Failed to fetch verified collision vectors.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCustom = async () => {
    if (!input1Hex.trim() || !input2Hex.trim()) {
      setError('Please provide two hexadecimal inputs, or click "Load Verified Collision Vector"');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await api.verifyCollision(input1Hex.trim(), input2Hex.trim());
      setResult(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Verification failed. Ensure valid hexadecimal bytes.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setInput1Hex('');
    setInput2Hex('');
    setResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-lg">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-950/80 border border-rose-800/60 text-rose-400 text-xs font-mono mb-2">
              <Zap className="w-3.5 h-3.5 text-rose-400" />
              Differential Cryptanalysis Lab
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              MD5 Collision Demonstration
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Demonstrates practical collision vulnerability in MD5 using mathematically verified test vectors
              from differential path research (Marc Stevens / Wang & Yu).
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleLoadKnownVectors}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-cyan-600/20 transition disabled:opacity-50"
            >
              <FileCode className="w-4 h-4" />
              <span>Load Verified Vectors</span>
            </button>
            <button
              onClick={handleClear}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
              title="Clear inputs"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Inputs */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-6">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 flex justify-between">
              <span>Input 1 (Hex Encoded Bytes)</span>
              {input1Hex && <span className="text-cyan-400 font-mono">{input1Hex.length / 2} bytes</span>}
            </label>
            <textarea
              value={input1Hex}
              onChange={(e) => setInput1Hex(e.target.value)}
              rows={4}
              placeholder="e.g. 4dc968ff0ee35c209572d4777b721587..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500 transition break-all"
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5 flex justify-between">
              <span>Input 2 (Hex Encoded Bytes)</span>
              {input2Hex && <span className="text-cyan-400 font-mono">{input2Hex.length / 2} bytes</span>}
            </label>
            <textarea
              value={input2Hex}
              onChange={(e) => setInput2Hex(e.target.value)}
              rows={4}
              placeholder="e.g. 4dc968ff0ee35c209572d4777b721587..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500 transition break-all"
            />
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button
            onClick={handleVerifyCustom}
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-600/25 transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Verify Collision Pair</span>
          </button>
        </div>

        {error && <p className="text-xs text-rose-400 font-mono mt-3">{error}</p>}
      </div>

      {loading && <LoadingSpinner label="Evaluating cryptographic differential states..." />}

      {/* Verification Results */}
      {result && (
        <div className="space-y-4">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <span className="text-sm font-bold text-white">Collision Verification Status:</span>
                {result.collision_detected ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-950/80 border border-rose-800 text-rose-400 animate-pulse">
                    <XCircle className="w-4 h-4" />
                    GENUINE MD5 COLLISION CONFIRMED
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-800 border border-slate-700 text-slate-300">
                    NO COLLISION DETECTED
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-400">Inputs Differ:</span>
                <span className={`font-mono font-bold ${result.inputs_differ ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {result.inputs_differ ? 'YES (Distinct byte sequences)' : 'NO (Identical data)'}
                </span>
              </div>
            </div>

            {/* Side by side digest comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Input 1 Hash Outputs */}
              <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800/80 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono font-bold text-slate-300">INPUT 1 DIGESTS</span>
                  <span className="text-[10px] text-slate-500 font-mono">Byte stream 1</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div>
                    <span className="text-slate-500 text-[11px] block">MD5 (128-bit):</span>
                    <span className="text-amber-400 font-bold break-all bg-amber-950/30 px-2 py-1 rounded block mt-0.5 border border-amber-900/40">
                      {result.md5_1}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">SHA-256 (256-bit):</span>
                    <span className="text-slate-300 break-all bg-slate-900 px-2 py-1 rounded block mt-0.5">
                      {result.sha256_1}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">SHA3-256 (256-bit):</span>
                    <span className="text-cyan-400 break-all bg-cyan-950/30 px-2 py-1 rounded block mt-0.5 border border-cyan-900/40">
                      {result.sha3_256_1}
                    </span>
                  </div>
                </div>
              </div>

              {/* Input 2 Hash Outputs */}
              <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800/80 space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-mono font-bold text-slate-300">INPUT 2 DIGESTS</span>
                  <span className="text-[10px] text-slate-500 font-mono">Byte stream 2</span>
                </div>
                <div className="space-y-2 text-xs font-mono">
                  <div>
                    <span className="text-slate-500 text-[11px] block">MD5 (128-bit):</span>
                    <span className="text-amber-400 font-bold break-all bg-amber-950/30 px-2 py-1 rounded block mt-0.5 border border-amber-900/40">
                      {result.md5_2}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">SHA-256 (256-bit):</span>
                    <span className="text-slate-300 break-all bg-slate-900 px-2 py-1 rounded block mt-0.5">
                      {result.sha256_2}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">SHA3-256 (256-bit):</span>
                    <span className="text-cyan-400 break-all bg-cyan-950/30 px-2 py-1 rounded block mt-0.5 border border-cyan-900/40">
                      {result.sha3_256_2}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Analysis & Explanations */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-xs space-y-2">
              <h5 className="font-semibold text-white">Cryptanalytic Analysis:</h5>
              <p className="text-slate-300 leading-relaxed">{result.explanation}</p>
              {result.source && (
                <p className="text-[11px] text-slate-500 font-mono pt-2 border-t border-slate-900">
                  Citation: {result.source}
                </p>
              )}
            </div>
          </div>

          <AlertBanner
            type="warning"
            title="Operational Impact on EV Charging Infrastructure"
            message="If an EV firmware verification system or CSMS relies on MD5 to authenticate firmware binaries or meter readings, an attacker can substitute benign firmware with malicious code crafted to match the exact same MD5 digest, bypassing the check entirely. Modern algorithms (SHA-256, SHA3-256) cleanly separate the collision pair as shown above."
          />
        </div>
      )}
    </div>
  );
};
