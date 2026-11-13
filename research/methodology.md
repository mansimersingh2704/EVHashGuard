# Research Methodology: MD5-to-SHA-3 Migration and Collision Risk Analysis in Legacy EV Firmware

**Project:** EVHashGuard  
**Version:** 1.0  
**Date:** 2024  
**Classification:** Academic Research — Educational Use Only

---

## 1. Research Questions

This study addresses the following specific research questions:

**RQ1.** To what extent are legacy MD5-based integrity checks in hypothetical OCPP 1.6 vendor extensions vulnerable to known collision attacks, and what is the practical exploitability of such vulnerabilities in a simulated EV charging environment?

**RQ2.** What are the measurable performance trade-offs (latency, throughput, overhead) when replacing MD5 with SHA-3-256 for per-message integrity verification in OCPP 1.6 message flows?

**RQ3.** Can a backward-compatible migration wrapper be designed that (a) produces SHA-3-256 digests for all new messages while (b) gracefully verifying legacy MD5 fields during a transitional period, without breaking existing OCPP 1.6 protocol semantics?

**RQ4.** What residual risks remain after migrating from MD5 to SHA-3-256, and how should a formal threat model categorize and prioritize them using the STRIDE framework?

---

## 2. Experimental Design

### 2.1 Laboratory Setup

All experiments are conducted in an entirely **local, isolated simulation environment** with no connection to real EV infrastructure, real charging stations, real payment systems, or any live OCPP network. The simulation consists of:

- A Python 3.11 FastAPI backend service running on `localhost:8000`
- A React/TypeScript frontend dashboard running on `localhost:5173`
- An SQLite database for persisting audit logs, hash records, and migration events
- Synthetic OCPP 1.6 messages generated from the `sample_data/ocpp_messages.json` fixture

No real personally identifiable information, real RFID tokens, real financial transactions, or real vehicle identifiers are used at any point. All data is fabricated for demonstration purposes.

### 2.2 Controlled Simulation Parameters

| Parameter | Value |
|---|---|
| Simulation platform | Local machine (no external network) |
| Backend language | Python 3.11 |
| Cryptographic library | Python `hashlib` (stdlib) |
| Database | SQLite (aiosqlite) |
| OCPP version simulated | OCPP 1.6 (message structure only) |
| Legacy integrity field | Hypothetical vendor extension (NOT standard OCPP) |
| Collision vectors | Wang-Yu 2004 (publicly documented, academic) |

### 2.3 Ethical Boundaries

- **No real infrastructure is targeted.** All experiments run against synthetic data.
- **No exploit is deployed against any real system.** The collision demonstration uses publicly known, decades-old academic vectors.
- **No OCPP-compliant system behavior is subverted.** The MD5 field is explicitly framed as a hypothetical vendor extension, not a standard OCPP field.

---

## 3. Hash Algorithm Comparison Methodology

### 3.1 Algorithms Under Study

| Algorithm | Standard | Output Length | Security Status |
|---|---|---|---|
| MD5 | RFC 1321 (1992) | 128 bits | **Broken** — collision attacks known since 2004 |
| SHA-256 | FIPS 180-4 | 256 bits | Secure — No practical collision attack known |
| SHA-3-256 | NIST FIPS 202 (2015) | 256 bits | Secure — Keccak sponge, independent design |
| SHA-3-512 | NIST FIPS 202 (2015) | 512 bits | Secure — Higher margin, recommended for long-term |

### 3.2 Qualitative Comparison Criteria

Each algorithm is evaluated against:
- **Collision resistance:** No two distinct inputs should produce the same digest (broken for MD5).
- **Preimage resistance:** Given a digest, it should be computationally infeasible to find the input.
- **Second preimage resistance:** Given input M1, it should be infeasible to find M2 such that H(M1) = H(M2).
- **Length extension attack resistance:** SHA-3 uses a sponge construction immune to length extension; MD5 and SHA-2 are vulnerable.
- **NIST approval status:** Per NIST SP 800-131A Rev 2, MD5 is disallowed for digital signature generation; SHA-3 is approved.

### 3.3 Performance Benchmarks

Performance is measured by hashing the serialized JSON payload of each synthetic OCPP 1.6 message type. For each algorithm:

1. Each message payload is hashed **1,000 times** (warm-up: first 10 runs discarded).
2. Wall-clock time is measured using Python's `time.perf_counter_ns()` for nanosecond precision.
3. The following statistics are recorded: **mean**, **median**, **standard deviation**, **min**, **max**.
4. Measurements are taken in a single-threaded context to eliminate scheduling jitter.
5. Results are normalized to milliseconds per operation.

---

## 4. Collision Demonstration Approach

### 4.1 Vector Source

The collision demonstration uses the **Wang-Yu 2004 MD5 collision pair**, published in:

> Wang, X., Yu, H. (2005). *How to Break MD5 and Other Hash Functions*. In: Cramer, R. (eds) Advances in Cryptology – EUROCRYPT 2005. Lecture Notes in Computer Science, vol 3494. Springer, Berlin, Heidelberg.

These are **identical-prefix collisions**: two 128-byte binary inputs that differ in specific bit positions but produce the same MD5 digest. They are part of the public academic record and have been reproduced independently by numerous researchers.

### 4.2 Demonstration Procedure

1. Load `sample_data/collision_vectors.json` containing `input1_hex` and `input2_hex`.
2. Decode both hex strings to raw bytes using `bytes.fromhex()`.
3. Assert that `input1_bytes != input2_bytes` (inputs are genuinely distinct).
4. Compute `hashlib.md5(input1_bytes).hexdigest()` and `hashlib.md5(input2_bytes).hexdigest()`.
5. Assert that both MD5 digests are **equal** (collision confirmed).
6. Compute SHA-256 and SHA-3-256 digests of both inputs.
7. Assert that SHA-256 and SHA-3-256 digests are **different** between the two inputs (modern algorithms resist the collision).
8. Log all results to the audit database.

This procedure is entirely computational — no network communication, no real message injection.

---

## 5. Migration Wrapper Design Rationale

### 5.1 Backward Compatibility Requirements

A realistic migration in production EV infrastructure cannot immediately replace all MD5 usage because:
- Legacy firmware versions may still produce MD5 integrity fields.
- Central Management Systems (CSMS) may not be updated simultaneously.
- OCPP 1.6 does not mandate a specific integrity mechanism; vendor extensions vary.

### 5.2 Wrapper Design

The migration wrapper implements a **dual-mode verification pipeline**:

```
Incoming Message
      |
      v
[Parse vendor_legacy_integrity field]
      |
      +---> If field present and algorithm == "MD5":
      |         Verify MD5 digest (legacy path)
      |         Simultaneously compute SHA-3-256 digest
      |         Log migration event
      |         Return: {legacy_verified: bool, sha3_digest: str, mode: "migration"}
      |
      +---> If field absent or algorithm == "SHA3-256":
                Verify SHA-3-256 digest only
                Log audit event
                Return: {verified: bool, mode: "modern"}
```

**Transition modes:**
- `legacy`: Accept MD5 only (not recommended, for diagnostics)
- `migration`: Accept MD5 but always compute and log SHA-3-256
- `modern`: Reject MD5, require SHA-3-256

---

## 6. Performance Measurement Methodology

### 6.1 Trial Design

- **Warm-up trials:** 10 iterations discarded before recording
- **Measurement trials:** 1,000 iterations per message type per algorithm
- **Precision:** `time.perf_counter_ns()` (nanosecond resolution)
- **Environment:** Single-threaded Python process, no I/O during measurement loop

### 6.2 Statistical Measures

All results are reported as:

| Statistic | Description |
|---|---|
| N | Number of valid trials |
| Mean (μ) | Arithmetic mean of execution times (ms) |
| Median | 50th percentile (robust to outliers) |
| Std Dev (σ) | Population standard deviation |
| Min | Minimum observed time |
| Max | Maximum observed time (may indicate GC pause) |

### 6.3 Wrapper Overhead

Wrapper overhead is computed as:
```
overhead_ms = wrapper_total_ms - sha3_hash_ms
```
where `wrapper_total_ms` includes JSON serialization, field extraction, digest computation, and database logging.

---

## 7. Ethical Considerations

1. **No real infrastructure is harmed or tested.** All experiments are offline simulations.
2. **Collision vectors are public academic knowledge** published in 2005. Their disclosure and demonstration serve education, not exploitation.
3. **No novel attack is developed.** The research replicates and demonstrates existing, well-documented vulnerabilities.
4. **Data minimization:** No real user data, real identifiers, or real payment information is used.
5. **Responsible framing:** The limitation of MD5 in legacy OCPP vendor extensions is presented to motivate migration, not to enable attacks.

---

## 8. Limitations

1. **Simulation only.** Results may not fully reflect performance on embedded firmware hardware.
2. **SQLite concurrency.** Real deployments would use PostgreSQL or similar for concurrent access.
3. **Single-machine benchmarks.** Network latency between CSMS and charging stations is not modeled.
4. **Hypothetical vendor extension.** Real OCPP 1.6 does NOT mandate MD5; this scenario models a specific class of non-standard implementations.
5. **No hardware security module (HSM).** Key management in production would involve HSMs, not in-memory keys.
6. **Wang-Yu vectors only.** The collision demonstration covers identical-prefix collisions; chosen-prefix collisions (more dangerous) are not demonstrated but are referenced.

---

## 9. References

1. Wang, X., Yu, H. (2005). *How to Break MD5 and Other Hash Functions*. EUROCRYPT 2005. LNCS 3494, pp. 19–35. Springer, Berlin, Heidelberg.
2. National Institute of Standards and Technology. (2015). *SHA-3 Standard: Permutation-Based Hash and Extendable-Output Functions* (FIPS PUB 202). NIST.
3. National Institute of Standards and Technology. (2019). *Transitioning the Use of Cryptographic Algorithms and Key Lengths* (NIST SP 800-131A Rev 2). NIST.
4. Open Charge Alliance. (2015). *Open Charge Point Protocol 1.6*. Open Charge Alliance.
5. Rivest, R. (1992). *The MD5 Message-Digest Algorithm* (RFC 1321). Internet Engineering Task Force.
