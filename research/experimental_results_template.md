# Empirical Research Benchmarks & Experimental Results Report

## 1. Experimental Methodology

The empirical performance evaluation of EVHashGuard was executed across 1,000 repeated trials ($N=1,000$) using realistic OCPP 1.6-J `StopTransaction` message frames generated from simulated hardware profiles.

All measurements were taken using Python's high-resolution `time.perf_counter_ns()` timer via the committed benchmark script `backend/scripts/run_benchmarks.py`. Raw benchmark data is preserved in `research/benchmark_results.json`.

---

## 2. Experimental Latency Benchmarks ($N=1,000$ Trials)

| Benchmark Metric | Sample Count ($N$) | Mean Latency ($\mu$s) | Median ($\mu$s) | Std. Deviation ($\mu$s) | P95 ($\mu$s) | Mean Latency (ms) | Security Designation |
|---|---|---|---|---|---|---|---|
| **MD5 Computation (Raw)** | 1,000 | 1.733 | 1.700 | 0.516 | 1.800 | 0.00173 | 0 bits (Broken Collision Resistance) |
| **SHA-1 Computation (Raw)** | 1,000 | 1.309 | 1.300 | 0.417 | 1.400 | 0.00131 | Deprecated (Broken Collision Resistance) |
| **SHA-256 Computation (Raw)** | 1,000 | 1.342 | 1.300 | 0.436 | 1.400 | 0.00134 | 128-bit collision / 256-bit preimage |
| **SHA3-256 Computation (Raw)** | 1,000 | 2.581 | 2.500 | 0.689 | 3.100 | 0.00258 | 128-bit collision / 256-bit preimage |
| **HMAC-SHA3-256 (Raw MAC)** | 1,000 | 6.294 | 6.200 | 0.672 | 6.400 | 0.00629 | Authenticated Origin & 256-bit Tag |
| **RFC 8785 Canonicalization** | 1,000 | 48.641 | 47.600 | 5.380 | 54.500 | 0.04864 | Deterministic JCS Byte Serialization |
| **CryptoWrapper.wrap (HMAC-SHA3)** | 1,000 | 95.011 | 88.100 | 20.016 | 134.400 | 0.09501 | Full Envelope Wrapping & MAC Binding |
| **CryptoWrapper.verify (In-Memory)** | 1,000 | 114.192 | 104.150 | 25.925 | 159.300 | 0.11419 | In-Memory Verification + Frame Parsing |
| **CryptoWrapper.verify_async (SQLite)**| 500 | 4,318.285 | 4,133.900 | 1,079.816 | 6,178.700 | 4.31828 | Persistent ACID Replay Nonce Check |

---

## 3. Computational Overhead Analysis

1. **Digest Latency Comparison:**
   - Raw SHA3-256 requires slightly more computational cycles than MD5 due to the 24-round Keccak-$f[1600]$ sponge permutation; however, at approximately **2.58 $\mu$s** (0.00258 ms), this overhead is negligible for embedded EVSE controllers running at 100–400 MHz.
2. **Wrapper Processing Overhead:**
   - In-memory cryptographic verification and structural frame validation completes in **~0.114 ms**.
   - With persistent SQLite nonce deduplication and ACID database journaling, end-to-end verification completes in **~4.32 ms**.
   - Compared against typical 4G/LTE cellular network roundtrip latency (20 ms – 100 ms) in field EVSE-to-CSMS communication, EVHashGuard introduces minimal overhead while providing robust cryptographic guarantees.

---

## 4. Message Compatibility Matrix Before and After Migration

| OCPP 1.6-J Message Action | Raw Legacy Parser Compatibility | Pre-Migration MD5 Status | Post-Migration Wrapper Status | Downstream Parser Modification Required? |
|---|---|---|---|---|
| `BootNotification` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |
| `Heartbeat` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |
| `StatusNotification` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |
| `Authorize` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |
| `StartTransaction` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |
| `StopTransaction` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |
| `MeterValues` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |
| `FirmwareStatusNotification` | 100% Passed | Vulnerable | Enveloped & Verified | **None (0% code change)** |

---

## 5. Collision Verification Results

| Differential Vector | Length | MD5 Digest | MD5 Match? | SHA-256 Digest Match? | SHA3-256 Digest Match? |
|---|---|---|---|---|---|
| Input 1 (`4dc968ff...`) | 64 bytes | `008ee33a9d58b51cfeb425b0959121c9` | **YES (Collision)** | **NO (Differ completely)** | **NO (Differ completely)** |
| Input 2 (`4dc968ff...`) | 64 bytes | `008ee33a9d58b51cfeb425b0959121c9` | **YES (Collision)** | **NO (Differ completely)** | **NO (Differ completely)** |
