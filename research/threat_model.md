# Threat Model: EVHashGuard — MD5-to-SHA-3 Migration in Legacy EV Firmware

**Project:** EVHashGuard  
**Version:** 1.0  
**Framework:** STRIDE  
**Scope:** Simulated OCPP 1.6 environment with hypothetical vendor-specific MD5 integrity extensions  
**Classification:** Academic Research — Educational Use Only

---

## 1. System Overview

EVHashGuard models a hypothetical EV charging ecosystem where a legacy vendor has added non-standard MD5-based integrity fields to OCPP 1.6 messages. The system consists of:

- **Charging stations** (EVCS): Embedded firmware generating OCPP 1.6 messages with optional vendor MD5 integrity fields.
- **Central Management System (CSMS)**: Backend server receiving and processing OCPP messages.
- **Migration Wrapper Service**: Middleware that validates legacy MD5 fields while producing SHA-3-256 digests.
- **Audit Database**: Records all integrity checks, migration events, and security alerts.
- **Dashboard**: Frontend visualization of hash performance, risk levels, and audit logs.

> **Note:** This is a simulation. No real OCPP infrastructure is targeted. Standard OCPP 1.6 does NOT mandate MD5; the MD5 usage modeled here is a hypothetical vendor extension.

---

## 2. Assets to Protect

| Asset | Description | Criticality |
|---|---|---|
| **Firmware images** | Software loaded onto charging station hardware | Critical |
| **OCPP message integrity** | Assurance that messages are unaltered in transit | High |
| **User authorization tokens** | RFID tag identifiers used to authorize charging sessions | High |
| **Transaction records** | Start/stop events, meter values, billing data | High |
| **Cryptographic configuration** | Algorithm selection, key material | Critical |
| **Audit log integrity** | Records of security events and migration activity | Medium |
| **CSMS availability** | Continuity of charging service | High |

---

## 3. Threat Actors

### 3.1 Insider Threat
- **Profile:** A rogue employee or contractor with access to firmware build pipelines or CSMS configuration.
- **Motivation:** Sabotage, financial gain (fraudulent charging), or espionage.
- **Capability:** High — can access signing keys, modify firmware before distribution, or weaken cryptographic configuration.

### 3.2 Man-in-the-Middle (MITM) Attacker
- **Profile:** An external attacker positioned on the network between a charging station and the CSMS.
- **Motivation:** Message tampering, replay attacks, unauthorized charging sessions.
- **Capability:** Medium — requires network access; easier on insecure Wi-Fi or cellular connections used by some legacy stations.

### 3.3 Supply Chain Attacker
- **Profile:** A compromised upstream vendor or component supplier.
- **Motivation:** Persistent access, long-term espionage, sabotage of large charging networks.
- **Capability:** High — can embed backdoors in firmware before delivery; difficult to detect without code signing.

### 3.4 Script Kiddie / Opportunist
- **Profile:** Low-skill attacker using published tools and exploits.
- **Motivation:** Free charging, curiosity, minor disruption.
- **Capability:** Low to Medium — relies on known, documented vulnerabilities (e.g., MD5 collision tools).

---

## 4. Attack Vectors and STRIDE Analysis

### 4.1 MD5 Collision Attack on Firmware Integrity

**Description:** An attacker crafts two firmware images M1 (legitimate) and M2 (malicious) such that MD5(M1) = MD5(M2). The CSMS accepts M2 because its MD5 digest matches the expected value.

| STRIDE Category | Assessment |
|---|---|
| **S**poofing | Attacker impersonates a legitimate firmware image |
| **T**ampering | Firmware content is altered without detection |
| **R**epudiation | Legitimate-looking MD5 checksum obscures tampering |
| **I**nformation Disclosure | Low direct risk; enables subsequent exploitation |
| **D**enial of Service | Corrupted firmware could brick a charging station |
| **E**levation of Privilege | Malicious firmware may gain elevated hardware access |

**Exploitability:** **High** (chosen-prefix MD5 collisions are feasible with commodity hardware as of 2009; see Stevens et al., 2009).  
**Impact:** **Critical**

### 4.2 MD5 Collision Attack on OCPP Message Integrity

**Description:** An attacker intercepts an OCPP StartTransaction message and replaces it with a crafted message having the same MD5 digest, authorizing a fraudulent transaction.

| STRIDE Category | Assessment |
|---|---|
| **S**poofing | Fake transaction appears authorized |
| **T**ampering | Transaction payload modified in transit |
| **R**epudiation | No reliable way to prove message was not original |
| **I**nformation Disclosure | Session tokens exposed |
| **D**enial of Service | Legitimate sessions could be blocked |
| **E**levation of Privilege | Unauthorized users gain charging access |

**Exploitability:** **Medium** (requires MITM position + MD5 collision computation)  
**Impact:** **High**

### 4.3 Replay Attack

**Description:** An attacker captures a valid OCPP Authorize or StartTransaction message and replays it later to gain unauthorized charging access.

| STRIDE Category | Assessment |
|---|---|
| **S**poofing | Replayed message impersonates original sender |
| **T**ampering | Not applicable (message is unmodified) |
| **R**epudiation | Victim denies initiating the replayed session |
| **I**nformation Disclosure | Timestamps and session IDs exposed |
| **D**enial of Service | Exhaustion of authorized sessions |
| **E**levation of Privilege | Unauthorized charging access |

**Exploitability:** **Medium** (requires message capture; easier on legacy HTTP/WS without TLS)  
**Impact:** **High**

### 4.4 Supply Chain Firmware Tampering

**Description:** A malicious vendor ships firmware with a backdoor, relying on MD5 for integrity verification which does not detect the modification.

| STRIDE Category | Assessment |
|---|---|
| **S**poofing | Legitimate-looking firmware with embedded malicious code |
| **T**ampering | Firmware altered before delivery |
| **R**epudiation | Vendor denies knowledge of modification |
| **I**nformation Disclosure | Backdoor exfiltrates operational data |
| **D**enial of Service | Backdoor can disable charging on command |
| **E**levation of Privilege | Full firmware-level control of charging hardware |

**Exploitability:** **Low to Medium** (requires insider or compromised vendor)  
**Impact:** **Critical**

### 4.5 Downgrade Attack on Cryptographic Algorithm

**Description:** An attacker manipulates the CSMS configuration (or exploits a misconfiguration) to force the migration wrapper to operate in `legacy` mode, accepting MD5 indefinitely.

| STRIDE Category | Assessment |
|---|---|
| **S**poofing | Not directly applicable |
| **T**ampering | Configuration tampered to weaken security |
| **R**epudiation | Misconfiguration provides plausible deniability |
| **I**nformation Disclosure | Downgraded security enables subsequent attacks |
| **D**enial of Service | Not applicable |
| **E**levation of Privilege | Attacker gains ability to forge messages |

**Exploitability:** **Medium** (requires configuration access or insider)  
**Impact:** **High**

---

## 5. Existing Mitigations

| Mitigation | Addresses | Effectiveness |
|---|---|---|
| TLS 1.2+ on OCPP WebSocket | MITM, Replay | High (when enforced) |
| Timestamp fields in OCPP messages | Replay | Medium (requires window enforcement) |
| OCPP-S/OCPP-J authentication | Spoofing | Medium |
| Firmware version tracking | Supply chain | Low (does not verify integrity) |
| Network segmentation | Lateral movement | Medium |

**Gaps:**  
- No standard OCPP 1.6 mechanism mandates strong cryptographic integrity at the message payload level.
- MD5-based vendor extensions (like those modeled here) are cryptographically broken.
- No standardized key management or code signing is specified in OCPP 1.6.

---

## 6. Proposed Mitigations (SHA-3 Migration Wrapper)

| Mitigation | Attack Addressed | Implementation |
|---|---|---|
| **SHA-3-256 message integrity** | MD5 collision attacks | Replace MD5 with SHA3-256 in vendor extension field |
| **Migration wrapper (dual-mode)** | Backward compatibility | Accept MD5 during transition, always compute SHA-3 |
| **Replay window enforcement** | Replay attacks | Reject messages with timestamps > 5 minutes old |
| **Algorithm downgrade prevention** | Downgrade attacks | Configuration flag `DOWNGRADE_ALLOWED=False` |
| **Audit logging** | Repudiation | Immutable log of all integrity checks and migration events |
| **SHA-3 for firmware verification** | Supply chain | Publish SHA-3-256 digests alongside firmware images |
| **STRIDE-informed monitoring** | All categories | Alert on legacy-mode usage, failed verifications, replay attempts |

---

## 7. Residual Risks

| Risk | Likelihood | Impact | Notes |
|---|---|---|---|
| Chosen-prefix collision against SHA-3 | Negligible | Critical | No known attacks; Keccak design resists differential cryptanalysis |
| Side-channel attacks on hash computation | Low | Medium | Outside scope of this simulation |
| Key management failure (HMAC) | Low | High | In-memory key; production would require HSM |
| Insider abuse of migration `legacy` mode | Medium | High | Mitigated by audit logging and downgrade prevention flag |
| TLS stripping on legacy station connections | Medium | High | Requires network-level enforcement outside this system |
| Zero-day in Python `hashlib` | Very Low | Critical | Mitigated by keeping runtime updated |

---

## 8. References

1. Wang, X., Yu, H. (2005). *How to Break MD5 and Other Hash Functions*. EUROCRYPT 2005.
2. National Institute of Standards and Technology. (2015). *SHA-3 Standard* (FIPS PUB 202).
3. National Institute of Standards and Technology. (2019). *Transitioning the Use of Cryptographic Algorithms and Key Lengths* (NIST SP 800-131A Rev 2).
4. Open Charge Alliance. (2015). *Open Charge Point Protocol 1.6*.
5. Microsoft. (2006). *The STRIDE Threat Model*. Microsoft Developer Network.
