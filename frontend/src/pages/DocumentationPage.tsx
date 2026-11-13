import React, { useState } from 'react';
import { BookOpen, ExternalLink, Code, ShieldCheck, Terminal, Layers } from 'lucide-react';

export const DocumentationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');

  const tabs = [
    { id: 'overview', label: '1. Project Overview' },
    { id: 'architecture', label: '2. System Architecture' },
    { id: 'wrapper', label: '3. Migration Wrapper Spec' },
    { id: 'crypto', label: '4. Cryptographic Foundations' },
    { id: 'api', label: '5. REST API Reference' },
    { id: 'research', label: '6. Research Methodology' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-800/60 text-cyan-400 text-xs font-mono mb-2">
            <BookOpen className="w-3.5 h-3.5" />
            Engineering & Cryptographic Manual
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            EVHashGuard Technical Documentation
          </h3>
          <p className="text-xs text-slate-300 mt-1">
            Complete technical specification, architectural blueprints, and deployment guidelines.
          </p>
        </div>

        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-blue-600/20 transition self-start sm:self-auto"
        >
          <ExternalLink className="w-4 h-4" />
          <span>Interactive Swagger UI</span>
        </a>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 rounded-xl text-xs font-mono transition ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-600/25'
                : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6 text-xs text-slate-300 leading-relaxed">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-cyan-400" />
              1. Project Problem Statement & Scope
            </h4>
            <p>
              Legacy electric vehicle (EV) charging management systems (CSMS) and vendor-specific firmware
              extensions frequently rely on outdated cryptographic hash algorithms such as MD5 for message integrity
              and firmware status verification.
            </p>
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-900/60 text-amber-200">
              <span className="font-bold block mb-1">Critical Protocol Fidelity Distinction:</span>
              Standard OCPP 1.6-J (Open Charge Point Protocol JSON over WebSocket) specification published by the Open
              Charge Alliance does <strong className="underline">NOT</strong> mandate or specify MD5 integrity algorithms.
              EVHashGuard simulates MD5 as a hypothetical or explicitly documented proprietary legacy vendor extension
              commonly found in older field-deployed charging hardware.
            </div>
            <h5 className="font-semibold text-white text-sm pt-2">Objectives:</h5>
            <ul className="list-disc pl-5 space-y-1 text-slate-300">
              <li>Demonstrate MD5 collision vulnerability using verified differential test vectors.</li>
              <li>Provide side-by-side benchmarking of MD5, SHA-1, SHA-256, and SHA3-256.</li>
              <li>Implement HMAC-SHA3-256 for authenticated message integrity.</li>
              <li>Design a backward-compatible wrapper that operates without modifying downstream legacy OCPP parsers.</li>
              <li>Simulate 7 practical attack vectors including payload tampering, replay, and downgrade attacks.</li>
            </ul>
          </div>
        )}

        {activeTab === 'architecture' && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-cyan-400" />
              2. System Architecture Blueprint
            </h4>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-cyan-300 text-[11px] overflow-x-auto leading-relaxed">
              <pre>{`+-------------------------------------------------------------+
|                 EV CHARGING STATION (EVSE)                  |
|  Legacy Firmware Controller [OCPP 1.6-J Message Generator]  |
+-------------------------------------------------------------+
                               |
                               | Transport: WebSocket / HTTPS
                               v
+-------------------------------------------------------------+
|             EVHashGuard INGRESS GATEWAY / WRAPPER           |
|                                                             |
|  1. Intercept Message Payload Frame:                        |
|     [MessageTypeId, UniqueId, Action, Payload]              |
|                                                             |
|  2. Check Cryptographic Envelope:                           |
|     - Legacy MD5 Fallback (Configurable Policy Lockout)     |
|     - SHA3-256 Integrity Verification                      |
|     - HMAC-SHA3-256 Constant-Time Key Authentication        |
|                                                             |
|  3. Reject Malformed / Tampered / Replayed Frames            |
|                                                             |
|  4. Log Security Event to SQLite Audit Engine               |
+-------------------------------------------------------------+
                               |
                               | (Unmodified Payload Dispatched)
                               v
+-------------------------------------------------------------+
|             LEGACY OCPP 1.6 PARSER & CSMS BACKEND           |
|  Zero modification required; standard OCPP frames processed |
+-------------------------------------------------------------+`}</pre>
            </div>
            <p>
              The wrapper isolates security upgrades to the communication boundary. Downstream enterprise CSMS
              components and charging billing systems process standard OCPP JSON arrays without requiring code modifications.
            </p>
          </div>
        )}

        {activeTab === 'wrapper' && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              3. Migration Wrapper Envelope Specification
            </h4>
            <p>
              The wrapper envelopes the original payload using deterministic JSON serialization (RFC 8785 canonical format):
            </p>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-cyan-300 text-xs overflow-x-auto">
              <pre>{`{
  "payload": {
    "station_id": "CS-NORDIC-001",
    "ocpp_message": [2, "uuid-1234", "MeterValues", { "connectorId": 1, ... }]
  },
  "crypto_metadata": {
    "wrapper_version": "2.1.0-sha3",
    "mode": "hmac_sha3_256",
    "algorithm": "HMAC-SHA3-256",
    "digest": "b8a4f910c2e...",
    "digest_bits": 256,
    "is_keyed_mac": true,
    "key_id": "key-active-csms-primary",
    "canonical_bytes_len": 312,
    "timestamp": "2026-11-13T22:45:00Z",
    "downgrade_protection": true
  },
  "wrapper_status": "ENVELOPED"
}`}</pre>
            </div>
            <p>
              The metadata contains explicit downgrade protection flags. If an attacker attempts to substitute an MD5
              envelope on an endpoint enforcing SHA-3, the wrapper immediately raises <code className="text-rose-400">DOWNGRADE_ATTACK_PREVENTED</code>.
            </p>
          </div>
        )}

        {activeTab === 'crypto' && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <Code className="w-5 h-5 text-blue-400" />
              4. Cryptographic Foundations & Keccak Sponge Function
            </h4>
            <p>
              Unlike MD5, SHA-1, and SHA-2 which are constructed on the Merkle-Damgård paradigm with Davies-Meyer
              compression functions, <strong>SHA-3 (FIPS 202)</strong> is built on the <em>Keccak sponge construction</em>.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <h5 className="font-bold text-white mb-2">Merkle-Damgård Construction</h5>
                <ul className="list-disc pl-4 space-y-1 text-slate-400">
                  <li>Iterative compression of fixed-size message blocks.</li>
                  <li>Susceptible to length-extension attacks without HMAC wrapper.</li>
                  <li>Structural vulnerability inherited across MD4, MD5, SHA-1, SHA-2.</li>
                </ul>
              </div>
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                <h5 className="font-bold text-white mb-2">Keccak Sponge Construction</h5>
                <ul className="list-disc pl-4 space-y-1 text-cyan-300">
                  <li>Absorbing phase absorbs message blocks into rate state.</li>
                  <li>Squeezing phase outputs variable-length pseudorandom digests.</li>
                  <li>Naturally immune to length-extension attacks by design.</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'api' && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <Terminal className="w-5 h-5 text-cyan-400" />
              5. Core REST API Endpoints
            </h4>
            <div className="space-y-3 font-mono text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-emerald-400 font-bold">GET /api/health</span>
                <span className="text-slate-400">System health & crypto engine status</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-blue-400 font-bold">POST /api/hash/compare</span>
                <span className="text-slate-400">Side-by-side multi-algorithm hashing</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-blue-400 font-bold">POST /api/collision/verify</span>
                <span className="text-slate-400">Verify MD5 collision test vectors</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-blue-400 font-bold">POST /api/ev/messages</span>
                <span className="text-slate-400">Generate realistic OCPP 1.6 frames</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-blue-400 font-bold">POST /api/migration/wrap</span>
                <span className="text-slate-400">Envelope payload with SHA-3 metadata</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-blue-400 font-bold">POST /api/migration/verify</span>
                <span className="text-slate-400">Verify envelope before legacy parser dispatch</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-rose-400 font-bold">POST /api/attacks/tampering</span>
                <span className="text-slate-400">Simulate OCPP in-flight meter tampering</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                <span className="text-cyan-400 font-bold">GET /api/dashboard/stats</span>
                <span className="text-slate-400">Real aggregate statistics from SQLite</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'research' && (
          <div className="space-y-4">
            <h4 className="text-base font-bold text-white flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-cyan-400" />
              6. Research Methodology & Authentic Citations
            </h4>
            <p>
              The EVHashGuard framework adopts empirical bench testing and formal differential cryptanalysis vectors:
            </p>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <h5 className="font-bold text-white">Peer-Reviewed Cryptographic References:</h5>
              <ol className="list-decimal pl-5 space-y-1.5 text-slate-400">
                <li>
                  <strong className="text-slate-200">Wang, X., Yu, H. (2005).</strong> "How to Break MD5 and Other Hash Functions."
                  <em>EUROCRYPT 2005</em>, Lecture Notes in Computer Science, vol 3494, Springer.
                </li>
                <li>
                  <strong className="text-slate-200">Stevens, M. (2007).</strong> "Fast Collision Attack on MD5."
                  <em>Cryptology ePrint Archive</em>, Report 2007/105.
                </li>
                <li>
                  <strong className="text-slate-200">NIST FIPS PUB 202 (2015).</strong> "SHA-3 Standard: Permutation-Based Hash and Extendable-Output Functions."
                  <em>National Institute of Standards and Technology</em>.
                </li>
                <li>
                  <strong className="text-slate-200">NIST SP 800-131A Rev. 2 (2019).</strong> "Transitioning the Use of Cryptographic Algorithms and Key Lengths."
                  <em>NIST Special Publication</em>.
                </li>
                <li>
                  <strong className="text-slate-200">Open Charge Alliance (2019).</strong> "Open Charge Point Protocol 1.6-J Specification."
                  <em>OCA Standardized Protocol Documentation</em>.
                </li>
                <li>
                  <strong className="text-slate-200">RFC 8785 (2020).</strong> "JSON Canonicalization Scheme (JCS)."
                  <em>Internet Engineering Task Force (IETF)</em>.
                </li>
              </ol>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
