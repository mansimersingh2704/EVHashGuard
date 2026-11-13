import hashlib
import time
from typing import List, Dict, Any

SECURITY_STATUS = {
    "md5": {
        "status": "BROKEN",
        "description": (
            "MD5 is cryptographically broken. Known collision attacks exist "
            "(Wang & Yu, 2005). Do NOT use for integrity verification."
        ),
    },
    "sha1": {
        "status": "WEAK",
        "description": (
            "SHA-1 has known practical collision vulnerabilities (SHAttered attack, 2017). "
            "Deprecated by NIST SP 800-131A Rev 2 for digital signatures."
        ),
    },
    "sha256": {
        "status": "SECURE",
        "description": (
            "SHA-256 is currently secure. No known practical attacks against "
            "collision resistance. Approved by NIST FIPS 180-4."
        ),
    },
    "sha3_256": {
        "status": "RECOMMENDED",
        "description": (
            "SHA3-256 (Keccak sponge construction) is NIST-recommended per FIPS 202. "
            "Different construction from SHA-2, provides defense-in-depth against "
            "structural weaknesses."
        ),
    },
}


def compute_hash(message: str, algorithm: str) -> Dict[str, Any]:
    algo = algorithm.lower().replace("-", "_")
    start = time.perf_counter()
    if algo == "md5":
        h = hashlib.md5(message.encode()).hexdigest()
    elif algo == "sha1":
        h = hashlib.sha1(message.encode()).hexdigest()
    elif algo == "sha256":
        h = hashlib.sha256(message.encode()).hexdigest()
    elif algo == "sha3_256":
        h = hashlib.sha3_256(message.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    elapsed = (time.perf_counter() - start) * 1000
    sec = SECURITY_STATUS.get(algo, {"status": "UNKNOWN", "description": "Unknown algorithm"})
    return {
        "algorithm": algorithm,
        "digest": h,
        "digest_length": len(h) * 4,  # hex chars × 4 = bits
        "execution_time_ms": round(elapsed, 4),
        "security_status": sec["status"],
        "security_description": sec["description"],
    }


def compare_hashes(message: str, algorithms: List[str]) -> List[Dict[str, Any]]:
    return [compute_hash(message, algo) for algo in algorithms]
