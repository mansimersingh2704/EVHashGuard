# EVHashGuard: System Architecture & Technical Specification

## 1. Executive Summary

**EVHashGuard** is a research-oriented backward-compatible cryptographic migration framework designed for legacy Electric Vehicle Charging Management Systems (CSMS) running OCPP 1.6-J.

The primary innovation is an **in-transit cryptographic wrapper** that envelopes incoming OCPP messages with NIST FIPS 202 SHA3-256 and FIPS 198-1 HMAC-SHA3-256 integrity and authentication metadata without modifying the original message structure, payload fields, or downstream legacy message parsers.

---

## 2. Architectural Blueprint

```
+-----------------------------------------------------------------------------------+
|                        ELECTRIC VEHICLE CHARGING STATION (EVSE)                   |
|                                                                                   |
|  Legacy Firmware Controller (e.g., v1.4.2-legacy-md5)                             |
|  Standard OCPP 1.6-J Frame: [MessageTypeId, UniqueId, Action, Payload]            |
|  Legacy Extension: Simulated out-of-band MD5 integrity check                      |
+-----------------------------------------------------------------------------------+
                                         |
                                         | In-Transit Communication (WSS / HTTPS)
                                         v
+-----------------------------------------------------------------------------------+
|                         EVHashGuard MIGRATION WRAPPER GATEWAY                     |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | STAGE 1: Envelope Extraction & Format Validation                            |  |
|  | - Extracts outer cryptographic metadata envelope                           |  |
|  | - Verifies presence of required header attributes                          |  |
|  | - Preserves inner standard OCPP JSON payload completely intact             |  |
|  +-----------------------------------------------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | STAGE 2: Deterministic Canonicalization (RFC 8785 JCS)                      |  |
|  | - Serializes payload dictionary with sorted keys and stripped whitespace   |  |
|  | - Guarantees byte-for-byte platform independence                            |  |
|  +-----------------------------------------------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | STAGE 3: Cryptographic Verification & Downgrade Prevention                  |  |
|  | - Mode "legacy_md5": Quarantined; warns of collision vulnerability         |  |
|  | - Mode "sha3_256": Verifies Keccak sponge digest (preimage & collision)    |  |
|  | - Mode "hmac_sha3_256": Constant-time tag verification (endpoint origin)   |  |
|  | - Enforces downgrade lockout policy: Disallows MD5 on SHA-3 channels       |  |
|  | - Timestamp freshness check (300s window) + unique message ID deduplication|  |
|  +-----------------------------------------------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | STAGE 4: Security Audit Journaling                                          |  |
|  | - Asynchronous persistence to SQLite: events, timestamps, digest matches   |  |
|  | - Real-time metrics streaming to SOC dashboard                             |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
                                         |
                                         | Dispatches Verified, Unmodified Payload
                                         v
+-----------------------------------------------------------------------------------+
|                     LEGACY OCPP 1.6-J PARSER & CSMS BACKEND                       |
|                                                                                   |
|  - Ingests standard [MessageTypeId, UniqueId, Action, Payload] JSON array         |
|  - Zero parser code modifications required                                        |
|  - Transparent security enforcement at the network boundary                       |
+-----------------------------------------------------------------------------------+
```

---

## 3. Core Modules Decomposition

### Module A: Cryptographic Hash Laboratory
- Supports MD5, SHA-1, SHA-256, and SHA3-256.
- Measures microsecond-precision execution latency.
- Evaluates output bit lengths and transparent NIST security designations.

### Module B: MD5 Collision Demonstration
- Loads mathematically verified collision vectors (Marc Stevens / Wang & Yu differential cryptanalysis).
- Verifies that two distinct 64-byte inputs ($M_1 \neq M_2$) produce the identical 128-bit MD5 digest (`008ee33a9d58b51cfeb425b0959121c9`).
- Demonstrates that modern algorithms (SHA-256 and SHA3-256) cleanly differentiate the vectors.

### Module C: EV Firmware & OCPP 1.6 Message Simulator
- Simulates realistic charging stations: NordicVolt, AlpinGrid, VoltDynamics, SuperWatt, and HarborPower.
- Generates standard OCPP 1.6 frames for all 8 standard action types:
  `BootNotification`, `Heartbeat`, `StatusNotification`, `Authorize`, `StartTransaction`, `StopTransaction`, `MeterValues`, `FirmwareStatusNotification`.
- Keeps vendor legacy MD5 integrity blocks separate from standard protocol arrays.

### Module D: Legacy MD5 Integrity System
- Simulates naive MD5 digest checks commonly found in older vendor extensions.
- Demonstrates how naive checks detect accidental transmission noise but fail completely against intentional collisions.

### Module E: SHA-3 Migration Wrapper
- Central research contribution.
- Transparently envelopes messages using deterministic JSON canonicalization.
- Implements strict downgrade prevention policy: MD5 fallbacks are quarantined and blocked when modern integrity is enforced.

### Module F: Attack Simulation Lab
- Controlled simulation of 7 distinct attack scenarios:
  1. In-flight meter tampering
  2. MD5 collision bypass
  3. Replay attack with expired timestamp
  4. Metadata envelope stripping
  5. Forged HMAC authentication tags
  6. Silent algorithm downgrade
  7. Firmware status spoofing

### Module G: Cryptographic Risk Analysis Engine
- Qualitative risk matrix compliant with NIST SP 800-131A Rev. 2 and FIPS 202.
- Multi-dimensional radar profile comparing collision resistance, preimage resistance, authentication capability, length-extension immunity, and EVSE hardware suitability.

### Module H: Security Audit Dashboard
- Real-time persisted SQLite telemetry.
- Dynamic aggregation of messages, verification passes/failures, and attack blocks.
