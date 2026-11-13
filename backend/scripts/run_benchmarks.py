#!/usr/bin/env python3
"""
EVHashGuard Micro-Benchmark Reproducibility Runner.
Measures genuine execution latencies of all cryptographic algorithms,
RFC 8785 canonicalization, and the EVHashGuard envelope pipeline.
"""
import time
import math
import json
import statistics
import hashlib
import asyncio
import sys
import os
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.crypto.hash_engine import compute_hash
from app.crypto.hmac_engine import compute_hmac_sha3_256, verify_hmac_sha3_256
from app.migration.wrapper import CryptoWrapper
from app.core.config import get_key, settings
from app.database.db import async_engine, Base
from sqlalchemy.ext.asyncio import async_sessionmaker


SAMPLE_OCPP_PAYLOAD = {
    "ocpp_message": [
        2,
        "msg-benchmark-1001",
        "StopTransaction",
        {
            "transactionId": 142857,
            "meterStop": 28450,
            "timestamp": "2026-11-13T23:30:00Z",
            "idTag": "RFID-NORDIC-TAG-001",
            "reason": "Local",
            "transactionData": [
                {
                    "timestamp": "2026-11-13T23:30:00Z",
                    "sampledValue": [
                        {"value": "28450", "context": "Transaction.End", "measurand": "Energy.Active.Import.Register", "unit": "Wh"}
                    ]
                }
            ]
        }
    ],
    "station_id": "CS-NORDIC-001",
    "firmware_version": "v2.1.0-sha3"
}


def run_cpu_benchmarks(iterations: int = 1000) -> Dict[str, Dict[str, float]]:
    """Runs synchronous CPU micro-benchmarks over genuine payloads."""
    payload_bytes = CryptoWrapper.canonicalize(SAMPLE_OCPP_PAYLOAD)
    test_key = get_key("key-active-csms-primary")
    assert test_key is not None, "Active key not found"

    wrapped_msg = CryptoWrapper.wrap(SAMPLE_OCPP_PAYLOAD, mode="hmac_sha3_256")
    wrapped_canonical_bytes = CryptoWrapper.canonicalize(wrapped_msg)

    targets = {
        "MD5 (Raw Digest)": lambda: hashlib.md5(payload_bytes).hexdigest(),
        "SHA-1 (Raw Digest)": lambda: hashlib.sha1(payload_bytes).hexdigest(),
        "SHA-256 (Raw Digest)": lambda: hashlib.sha256(payload_bytes).hexdigest(),
        "SHA3-256 (Raw Keccak)": lambda: hashlib.sha3_256(payload_bytes).hexdigest(),
        "HMAC-SHA3-256 (Raw MAC)": lambda: compute_hmac_sha3_256(payload_bytes, test_key),
        "RFC 8785 Canonicalization": lambda: CryptoWrapper.canonicalize(SAMPLE_OCPP_PAYLOAD),
        "CryptoWrapper.wrap (HMAC-SHA3)": lambda: CryptoWrapper.wrap(SAMPLE_OCPP_PAYLOAD, mode="hmac_sha3_256"),
        "CryptoWrapper.verify (In-Memory)": lambda: CryptoWrapper.verify(wrapped_msg, enforce_mode="hmac_sha3_256"),
    }

    results = {}

    for name, fn in targets.items():
        # Warmup
        for _ in range(50):
            fn()

        latencies_ns: List[int] = []
        for _ in range(iterations):
            t0 = time.perf_counter_ns()
            fn()
            t1 = time.perf_counter_ns()
            latencies_ns.append(t1 - t0)

        latencies_us = [t / 1000.0 for t in latencies_ns]
        results[name] = {
            "mean_us": round(statistics.mean(latencies_us), 3),
            "median_us": round(statistics.median(latencies_us), 3),
            "stddev_us": round(statistics.stdev(latencies_us), 3),
            "min_us": round(min(latencies_us), 3),
            "max_us": round(max(latencies_us), 3),
            "p95_us": round(sorted(latencies_us)[int(0.95 * len(latencies_us))], 3),
            "mean_ms": round(statistics.mean(latencies_us) / 1000.0, 5),
            "iterations": iterations,
        }

    return results


async def run_async_pipeline_benchmark(iterations: int = 500) -> Dict[str, float]:
    """Runs end-to-end async verification benchmark with persistent SQLite replay protection."""
    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine)

    # Warmup
    async with Session() as session:
        msg = CryptoWrapper.wrap(SAMPLE_OCPP_PAYLOAD, mode="hmac_sha3_256")
        await CryptoWrapper.verify_async(msg, enforce_mode="hmac_sha3_256", db_session=session)

    latencies_us: List[float] = []
    async with Session() as session:
        for _ in range(iterations):
            # Unique message per iteration to test real consumption
            msg = CryptoWrapper.wrap(SAMPLE_OCPP_PAYLOAD, mode="hmac_sha3_256")
            t0 = time.perf_counter_ns()
            res = await CryptoWrapper.verify_async(msg, enforce_mode="hmac_sha3_256", db_session=session)
            t1 = time.perf_counter_ns()
            assert res["verified"] is True
            latencies_us.append((t1 - t0) / 1000.0)

    await engine.dispose()

    return {
        "mean_us": round(statistics.mean(latencies_us), 3),
        "median_us": round(statistics.median(latencies_us), 3),
        "stddev_us": round(statistics.stdev(latencies_us), 3),
        "min_us": round(min(latencies_us), 3),
        "max_us": round(max(latencies_us), 3),
        "p95_us": round(sorted(latencies_us)[int(0.95 * len(latencies_us))], 3),
        "mean_ms": round(statistics.mean(latencies_us) / 1000.0, 5),
        "iterations": iterations,
    }


def main():
    print("=" * 80)
    print("  EVHashGuard Empirical Micro-Benchmark Suite")
    print("  Payload: Realistic OCPP 1.6-J StopTransaction Frame")
    print("=" * 80)

    results = run_cpu_benchmarks(iterations=1000)
    async_res = asyncio.run(run_async_pipeline_benchmark(iterations=500))
    results["CryptoWrapper.verify_async (SQLite Replay)"] = async_res

    print("\n| Operation | Mean (us) | Median (us) | StdDev (us) | P95 (us) | Mean (ms) | Iterations |")
    print("|---|---|---|---|---|---|---|")
    for name, m in results.items():
        print(f"| **{name}** | {m['mean_us']} | {m['median_us']} | {m['stddev_us']} | {m['p95_us']} | {m['mean_ms']} | {m['iterations']} |")

    out_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "research",
        "benchmark_results.json",
    )
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Raw results saved to: {out_file}")


if __name__ == "__main__":
    main()
