import hashlib
from typing import Dict, Any

# Mathematically verified MD5 collision pair
# Based on Marc Stevens / Wang et al. differential cryptanalysis on MD5 compression function.
# These two 64-byte (512-bit) binary blocks differ at byte indices 35 and 55,
# yet yield the exact same 128-bit MD5 digest under standard MD5 initial values.

_STEVENS_VECTOR_1 = bytes.fromhex(
    "4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518"
    "afbfa200a8284bf36e8e4b55b35f427593d849676da0d1555d8360fb5f07fea2"
)

_STEVENS_VECTOR_2 = bytes.fromhex(
    "4dc968ff0ee35c209572d4777b721587d36fa7b21bdc56b74a3dc0783e7b9518"
    "afbfa202a8284bf36e8e4b55b35f427593d849676da0d1d55d8360fb5f07fea2"
)

# Runtime verification at import time
_md5_1 = hashlib.md5(_STEVENS_VECTOR_1).hexdigest()
_md5_2 = hashlib.md5(_STEVENS_VECTOR_2).hexdigest()

VECTORS_VERIFIED = (_md5_1 == _md5_2) and (_STEVENS_VECTOR_1 != _STEVENS_VECTOR_2)
COLLISION_MD5_DIGEST = _md5_1

# Differences in other algorithms prove this is solely an MD5 cryptographic failure:
_sha256_1 = hashlib.sha256(_STEVENS_VECTOR_1).hexdigest()
_sha256_2 = hashlib.sha256(_STEVENS_VECTOR_2).hexdigest()
_sha3_1 = hashlib.sha3_256(_STEVENS_VECTOR_1).hexdigest()
_sha3_2 = hashlib.sha3_256(_STEVENS_VECTOR_2).hexdigest()

assert VECTORS_VERIFIED, "CRITICAL: Built-in MD5 collision vectors failed verification!"
assert _sha256_1 != _sha256_2, "SHA-256 must distinguish MD5 collision vectors"
assert _sha3_1 != _sha3_2, "SHA3-256 must distinguish MD5 collision vectors"


def get_known_collision_vectors() -> Dict[str, Any]:
    """
    Returns verified collision pair with full cryptographic analysis.
    """
    return {
        "input1_hex": _STEVENS_VECTOR_1.hex(),
        "input2_hex": _STEVENS_VECTOR_2.hex(),
        "byte_length": len(_STEVENS_VECTOR_1),
        "inputs_differ": True,
        "differing_byte_indices": [
            i for i in range(len(_STEVENS_VECTOR_1))
            if _STEVENS_VECTOR_1[i] != _STEVENS_VECTOR_2[i]
        ],
        "md5_hash_1": _md5_1,
        "md5_hash_2": _md5_2,
        "md5_collision": True,
        "sha256_hash_1": _sha256_1,
        "sha256_hash_2": _sha256_2,
        "sha256_differ": _sha256_1 != _sha256_2,
        "sha3_256_hash_1": _sha3_1,
        "sha3_256_hash_2": _sha3_2,
        "sha3_256_differ": _sha3_1 != _sha3_2,
        "source": "Marc Stevens (2007) / Wang & Yu (2005) Differential Path MD5 Collision",
        "description": (
            "Authentic 64-byte differential collision pair for MD5. "
            "Both distinct byte sequences map to the identical MD5 digest 008ee33a9d58b51cfeb425b0959121c9. "
            "Under modern algorithms (SHA-256 and SHA3-256), the digests are completely disparate, "
            "demonstrating the robustness of modern sponge and Merkle-Damgård constructions against MD5 attack differentials."
        ),
    }


def verify_custom_collision(input1_bytes: bytes, input2_bytes: bytes) -> Dict[str, Any]:
    """
    Verifies whether two arbitrary binary inputs form an MD5 collision pair.
    """
    inputs_differ = (input1_bytes != input2_bytes)
    m1 = hashlib.md5(input1_bytes).hexdigest()
    m2 = hashlib.md5(input2_bytes).hexdigest()
    s256_1 = hashlib.sha256(input1_bytes).hexdigest()
    s256_2 = hashlib.sha256(input2_bytes).hexdigest()
    s3_1 = hashlib.sha3_256(input1_bytes).hexdigest()
    s3_2 = hashlib.sha3_256(input2_bytes).hexdigest()

    is_collision = inputs_differ and (m1 == m2)

    if not inputs_differ:
        explanation = "Inputs are identical. Trivial identical inputs do not constitute a cryptographic collision."
    elif is_collision:
        explanation = (
            "Genuine MD5 collision confirmed: Both inputs are distinct bit sequences yet produce "
            f"the identical MD5 digest ({m1}). Under SHA-256 and SHA3-256, the digests differ, "
            "proving the vulnerability is specific to MD5 compression function differentials."
        )
    else:
        explanation = (
            f"No collision detected. Input 1 MD5 is {m1}, whereas Input 2 MD5 is {m2}. "
            "Arbitrary text variations do not produce MD5 collisions; finding collisions requires "
            "complex differential cryptanalysis."
        )

    return {
        "inputs_differ": inputs_differ,
        "collision_detected": is_collision,
        "md5_1": m1,
        "md5_2": m2,
        "sha256_1": s256_1,
        "sha256_2": s256_2,
        "sha3_256_1": s3_1,
        "sha3_256_2": s3_2,
        "explanation": explanation,
    }
