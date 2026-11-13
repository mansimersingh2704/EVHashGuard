# EVHashGuard

### MD5-to-SHA-3 Migration and Collision Risk Analysis in Legacy EV Firmware
**Subtitle:** A Backward-Compatible Cryptographic Integrity Framework for Legacy OCPP 1.6 EV Charging Systems

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3+-61dafb.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-3178c6.svg)](https://www.typescriptlang.org/)
[![NIST FIPS 202](https://img.shields.io/badge/NIST-FIPS_202_(SHA3)-green.svg)](https://csrc.nist.gov/publications/detail/fips/202/final)
[![RFC 8785](https://img.shields.io/badge/RFC-8785_(JCS)-blueviolet.svg)](https://www.rfc-editor.org/rfc/rfc8785)
[![Tests Passing](https://img.shields.io/badge/pytest-66%20passed-brightgreen.svg)]()

---

> **CRITICAL PROTOCOL ACCURACY NOTICE:**  
> Standard OCPP 1.6-J (Open Charge Point Protocol JSON over WebSocket) specification published by the Open Charge Alliance (OCA) **does NOT mandate or specify MD5 integrity checks**. MD5 in this project is investigated as a **simulated, proprietary legacy vendor extension** commonly discovered in older field-deployed charging stations and legacy firmware download integrity routines.

---

## 1. Problem Statement

Legacy electric vehicle (EV) charging management systems (CSMS) and proprietary charging station firmware extensions frequently rely on outdated cryptographic hash algorithms such as **MD5** for integrity verification of telemetry messages, meter values, and firmware images.

MD5 is **cryptographically broken for collision resistance**. Adversaries can construct two disparate payloads ($M_1 \neq M_2$) that compute to the identical 128-bit MD5 digest. If a CSMS relies on MD5 for message verification:
1. An attacker can tamper with charging transactions (e.g., modifying `meterStop` in `StopTransaction` to defraud billing).
2. An attacker can replace legitimate firmware with backdoored binaries while preserving the legacy MD5 digest.
3. Simple hashing provides no origin authentication and is vulnerable to length-extension and replay attacks.

### Objectives of EVHashGuard
- Demonstrate practical MD5 collision vulnerabilities using mathematically verified differential cryptanalysis vectors.
- Provide multi-algorithm benchmarking (MD5, SHA-1, SHA-256, SHA3-256).
- Implement a **backward-compatible cryptographic migration wrapper** utilizing **SHA3-256** and **HMAC-SHA3-256**.
- Enforce cryptographic verification at the gateway without requiring changes to legacy message parsers.
- Detect in-flight tampering, replay attacks, missing metadata, and downgrade attempts.
- Provide a real-time cybersecurity SOC dashboard powered by live SQLite audit telemetry.

---

## 2. System Architecture

```
+-------------------------------------------------------------+
|               EV CHARGING STATION (EVSE)                    |
|   Legacy Firmware Controller [OCPP 1.6-J Frame Generator]   |
+-------------------------------------------------------------+
                               |
                               | (WSS / HTTPS Frame)
                               v
+-------------------------------------------------------------+
|            EVHashGuard CRYPTOGRAPHIC WRAPPER                |
|                                                             |
|   1. Envelope Validation (Preserve OCPP Payload Intact)     |
|   2. RFC 8785 Deterministic Canonicalization                |
|   3. SHA3-256 / HMAC-SHA3-256 Integrity Verification        |
|   4. Anti-Downgrade & Anti-Replay Policy Enforcement        |
|   5. Security Audit Telemetry Persistence (SQLite)          |
+-------------------------------------------------------------+
                               |
                               | (Verified Standard Payload)
                               v
+-------------------------------------------------------------+
|            LEGACY OCPP 1.6 PARSER & CSMS BACKEND            |
|   Standard [MessageType, ID, Action, Payload] JSON Ingest   |
|   * ZERO Parser Code Modifications Required *               |
+-------------------------------------------------------------+
```

---

## 3. Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Backend Core** | Python 3.11+, FastAPI | High-performance asynchronous REST API with automatic OpenAPI specs |
| **Cryptography** | Python standard `hashlib`, `hmac`, `secrets`, `cryptography` | Constant-time comparisons, NIST FIPS 202 SHA-3 and FIPS 198-1 HMAC |
| **Database** | SQLite + SQLAlchemy 2.0 Async (`aiosqlite`) | Zero-configuration, ACID-compliant local audit journal |
| **Frontend Framework** | React 18, TypeScript, Vite | Strongly typed, modular Single Page Application |
| **UI Design System** | Tailwind CSS (Dark SOC Theme), Lucide React | Professional cybersecurity SaaS interface |
| **Data Visualization** | Recharts | Interactive SVG bar charts, radar profiles, and telemetry timelines |
| **Automated Testing** | Pytest, FastAPI TestClient | 34 automated unit, integration, and cryptanalytic test vectors |
| **Containerization** | Docker, Docker Compose | Reproducible multi-service deployment |

---

## 4. Project Structure

```
EVHashGuard/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application entrypoint & lifecycle
│   │   ├── api/                        # REST API route handlers
│   │   │   ├── hash_routes.py          # Cryptographic lab comparisons
│   │   │   ├── collision_routes.py     # MD5 collision verification
│   │   │   ├── ev_routes.py            # Simulated EVSE & OCPP messages
│   │   │   ├── legacy_routes.py        # Legacy MD5 verification
│   │   │   ├── migration_routes.py     # SHA-3 wrapper wrap/verify endpoints
│   │   │   ├── attack_routes.py        # 7 Red-Team simulation handlers
│   │   │   ├── risk_routes.py          # Qualitative risk analysis engine
│   │   │   ├── dashboard_routes.py     # Live SQLite aggregate metrics
│   │   │   └── audit_routes.py         # Paginated security audit logs
│   │   ├── core/
│   │   │   └── config.py               # Settings and ephemeral HMAC key generation
│   │   ├── crypto/
│   │   │   ├── hash_engine.py          # MD5, SHA-1, SHA-256, SHA3-256 engines
│   │   │   ├── hmac_engine.py          # Constant-time HMAC-SHA3-256
│   │   │   └── collision_vectors.py    # Verified differential MD5 collision pairs
│   │   ├── ev_simulator/
│   │   │   ├── message_generator.py    # OCPP 1.6-J realistic frames
│   │   │   └── ocpp_parser.py          # Minimal OCPP 1.6 frame structure parser
│   │   ├── migration/
│   │   │   ├── wrapper.py              # Backward-compatible wrapper & RFC 8785 canonicalization
│   │   │   └── replay.py               # Persistent SQLite replay protection & nonce deduplication
│   │   ├── attacks/
│   │   │   └── simulator.py            # Red-team attack vectors (real verification pipeline)
│   │   ├── risk_engine/
│   │   │   └── analyzer.py             # NIST SP 800-131A qualitative risk matrix
│   │   ├── database/
│   │   │   └── db.py                   # Async SQLAlchemy models (Messages, Nonces, Audits)
│   │   └── models/
│   │       └── schemas.py              # Pydantic v2 validation models
│   ├── tests/
│   │   ├── test_crypto.py              # Known test vectors for all 4 hash algorithms
│   │   ├── test_collision.py           # Mathematical verification of collision vectors
│   │   ├── test_migration.py           # Wrapper envelope and downgrade prevention
│   │   ├── test_attacks.py             # All 7 attack scenarios verified
│   │   ├── test_api.py                 # Full integration test suite for REST routes
│   │   └── test_regression_audit.py    # 20 Critical Security Remediation Regression Tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/                 # Sidebar, TopNav, StatCard, JsonViewer, etc.
│   │   ├── pages/                      # 10 dedicated functional views
│   │   ├── services/api.ts             # Typed Axios HTTP client
│   │   ├── types/index.ts              # TypeScript interface contracts
│   │   ├── App.tsx                     # Main layout & state routing
│   │   ├── main.tsx
│   │   └── index.css                   # Tailwind styling
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── Dockerfile
├── sample_data/
│   ├── ocpp_messages.json              # 10 representative OCPP 1.6 test messages
│   └── collision_vectors.json          # Documented verified MD5 collision vectors
├── research/
│   ├── methodology.md                  # Research methodology & experimental design
│   ├── threat_model.md                 # STRIDE threat model & asset security
│   └── experimental_results_template.md# Micro-benchmark latency measurements
├── docs/
│   ├── architecture.md                 # In-depth architectural specification
│   └── api_reference.md                # Comprehensive endpoint reference
├── scripts/
│   ├── run_backend.bat                 # Windows backend launcher
│   ├── run_frontend.bat                # Windows frontend launcher
│   └── run_tests.bat                   # Test runner script
├── docker-compose.yml
└── README.md
```

---

## 5. Getting Started & Execution

### Prerequisites
- Python 3.11 or newer
- Node.js 18+ and npm
- (Optional) Docker and Docker Compose

### Option A: Local Execution (Recommended for Development)

#### 1. Start the Backend API
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend Swagger API documentation will be available at:* [http://localhost:8000/docs](http://localhost:8000/docs)

#### 2. Start the Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```
*Frontend SOC Dashboard will be accessible at:* [http://localhost:5173](http://localhost:5173)

---

### Option B: Docker Compose Deployment
```bash
docker-compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API: `http://localhost:8000/docs`

---

## 6. Running Automated Tests

EVHashGuard includes 66 comprehensive automated tests covering all cryptographic vectors, collision pairs, attack scenarios, REST API routes, normative RFC 8785 vectors, and 22 specific security regression audit tests:

```bash
cd backend
python -m pytest tests/ -v
```

**Expected Output:**
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1
collected 66 items

tests/test_api.py ............                               [ 18%]
tests/test_attacks.py ........                               [ 30%]
tests/test_collision.py ...                                  [ 34%]
tests/test_crypto.py ......                                  [ 43%]
tests/test_migration.py .......                              [ 54%]
tests/test_regression_audit.py ......................        [ 87%]
tests/test_rfc8785_canonicalization.py ........             [100%]

======================== 66 passed in 2.46s ========================
```

### Security Regression Audit Suite (tests/test_regression_audit.py)
1. `test_01_md5_digest_verification`: Legacy MD5 baseline verification.
2. `test_02_sha3_256_verification`: Unkeyed SHA3-256 integrity validation.
3. `test_03_hmac_sha3_256_verification`: Authenticated HMAC-SHA3-256 validation.
4. `test_04_malformed_digest`: Safe rejection of odd-length, non-hex, or truncated digests.
5. `test_05_metadata_modification`: Strict rejection on missing, unsupported, or modified envelope version.
6. `test_06_algorithm_field_substitution`: Prevention of algorithm claim substitution.
7. `test_07_key_id_substitution`: Prevention of unauthorized key ID tampering.
8. `test_08_timestamp_modification`: Rejection of modified envelope timestamps.
9. `test_09_nonce_modification`: Rejection of modified envelope nonces.
10. `test_10_sha3_to_md5_downgrade`: Prevention of downgrade from SHA3-256 to MD5.
11. `test_11_hmac_to_sha3_downgrade`: Prevention of downgrade from HMAC-SHA3-256 to unkeyed SHA3.
12. `test_12_replay_of_identical_message`: Persistent SQLite duplicate nonce detection.
13. `test_13_replay_after_backend_restart`: Replay rejection persists across backend restarts.
14. `test_14_concurrent_duplicate_nonce_requests`: Atomic duplicate nonce handling under concurrency via SAVEPOINT.
15. `test_15_invalid_ocpp_call`: Frame length and type enforcement on OCPP CALL frames.
16. `test_16_invalid_ocpp_callresult`: Frame length and type enforcement on CALLRESULT frames.
17. `test_17_invalid_ocpp_callerror`: Frame length and type enforcement on CALLERROR frames.
18. `test_18_parser_rejection_after_successful_hash_verification`: Separation of crypto vs parser validation (dispatch dropped).
19. `test_19_tampered_payload`: Payload bit-flip detection over RFC 8785 canonical bytes.
20. `test_20_unknown_key_rejection`: Rejection of unknown or unconfigured key identifiers.
21. `test_21_malformed_key_registry_prevents_silent_fallback`: Fails fast (RuntimeError) on malformed environment key configurations with zero silent fallbacks.
22. `test_22_unkeyed_digest_recomputation_fails_authenticity`: Demonstrates unkeyed hash recomputation vulnerability and HMAC authenticity defense.

---

## 7. Empirical Research Findings & Reproducible Benchmarks

All benchmark metrics are genuinely reproducible using the committed benchmark runner script:

```bash
cd backend
python scripts/run_benchmarks.py
```

### Empirical Measurements ($N=1000$ trials, StopTransaction frame):

| Operation | Mean ($\mu$s) | Median ($\mu$s) | StdDev ($\mu$s) | P95 ($\mu$s) | Mean (ms) | Iterations |
|---|---|---|---|---|---|---|
| **MD5 (Raw Digest)** | 1.733 | 1.700 | 0.516 | 1.800 | 0.00173 | 1,000 |
| **SHA-1 (Raw Digest)** | 1.309 | 1.300 | 0.417 | 1.400 | 0.00131 | 1,000 |
| **SHA-256 (Raw Digest)** | 1.342 | 1.300 | 0.436 | 1.400 | 0.00134 | 1,000 |
| **SHA3-256 (Raw Keccak)** | 2.581 | 2.500 | 0.689 | 3.100 | 0.00258 | 1,000 |
| **HMAC-SHA3-256 (Raw MAC)** | 6.294 | 6.200 | 0.672 | 6.400 | 0.00629 | 1,000 |
| **RFC 8785 Canonicalization** | 48.641 | 47.600 | 5.380 | 54.500 | 0.04864 | 1,000 |
| **CryptoWrapper.wrap (HMAC-SHA3)** | 95.011 | 88.100 | 20.016 | 134.400 | 0.09501 | 1,000 |
| **CryptoWrapper.verify (In-Memory)** | 114.192 | 104.150 | 25.925 | 159.300 | 0.11419 | 1,000 |
| **CryptoWrapper.verify_async (SQLite Replay)** | 4,318.285 | 4,133.900 | 1,079.816 | 6,178.700 | 4.31828 | 500 |

*Raw benchmark outputs are version-controlled in `research/benchmark_results.json`.*

---

## 8. Limitations & Security Scope

> **RESEARCH & EDUCATIONAL DISCLAIMER:**  
> EVHashGuard is an experimental research and educational framework. It is **NOT** formally certified under Common Criteria, FIPS 140-3, or ISO 15118-20, and is **NOT** recommended for direct unvetted deployment in production EV charging networks without hardware-backed root-of-trust (TPM/HSM) integration.

### Core Architectural Distinctions:
1. **Unkeyed Hashing vs. Keyed Authentication**:
   - `sha3_256` mode provides **integrity only** against transmission bit flips. An active in-flight adversary can modify the payload and recompute a matching SHA3-256 digest without keys.
   - `hmac_sha3_256` mode provides **sender authenticity and tamper resistance** because computing valid tags requires knowledge of the pre-shared 256-bit secret key.
2. **Structural Frame Validation vs. Full PDU Schema Validation**:
   - EVHashGuard's `OCPPParser` performs **structural frame validation** (verifying JSON array format, message type IDs [2, 3, 4], frame element count, and string `UniqueId`).
   - It **does not** perform full PDU JSON Schema semantic validation of action-specific payloads (e.g. verifying internal `BootNotification` or `MeterValues` fields). Full application semantics remain the responsibility of downstream CSMS parsers.
3. **Key Management Scope**:
   - While environment configuration (`EV_KEY_REGISTRY_JSON`) and fail-fast validation are implemented, production systems require automated key rotation via PKI certificates or cloud KMS rather than static environment variables.

### Future Scope
- **Post-Quantum Cryptography (PQC):** Integration of ML-DSA (Dilithium) and ML-KEM (Kyber) for quantum-resistant firmware signing per NIST FIPS 204 and FIPS 203.
- **OCPP 2.0.1 Transition:** Adapting the envelope pipeline to native OCPP 2.0.1 security profiles (Security Profile 3 - TLS with client certificates).

---

## 9. Academic & Technical References

1. **Wang, X., & Yu, H. (2005).** "How to Break MD5 and Other Hash Functions." *EUROCRYPT 2005*, Lecture Notes in Computer Science, vol 3494, Springer, Berlin, Heidelberg.
2. **Stevens, M. (2007).** "Fast Collision Attack on MD5." *Cryptology ePrint Archive*, Report 2007/105.
3. **NIST FIPS PUB 202 (2015).** "SHA-3 Standard: Permutation-Based Hash and Extendable-Output Functions." *National Institute of Standards and Technology*.
4. **NIST SP 800-131A Rev. 2 (2019).** "Transitioning the Use of Cryptographic Algorithms and Key Lengths." *NIST Special Publication*.
5. **Open Charge Alliance (2019).** "Open Charge Point Protocol 1.6 Edition 2 (OCPP 1.6-J)." *OCA Specification*.
6. **RFC 1321 (1992).** "The MD5 Message-Digest Algorithm." *Internet Engineering Task Force*.
7. **RFC 8785 (2020).** "JSON Canonicalization Scheme (JCS)." *Internet Engineering Task Force*.

---

## 10. License
This project is licensed under the MIT License — see the LICENSE file for details.
