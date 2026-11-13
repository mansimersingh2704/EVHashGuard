from typing import List, Dict, Any


ALGORITHM_EVALUATIONS: List[Dict[str, Any]] = [
    {
        "algorithm": "MD5",
        "family": "MD4-derivative (Merkle-Damgård)",
        "digest_size_bits": 128,
        "collision_resistance": "BROKEN",
        "collision_complexity": "Real-time (<1 second using Marc Stevens HashClash / Wang et al.)",
        "preimage_resistance": "THEORETICALLY_WEAKENED",
        "second_preimage_resistance": "VULNERABLE (via chosen-prefix techniques)",
        "authentication_capability": "NONE (unkeyed digest; vulnerable to length extension when used naively)",
        "known_weaknesses": [
            "Practical identical-prefix and chosen-prefix collision attacks",
            "Flame malware exploited MD5 collision in forged Microsoft code signing certificates (2012)",
            "Length extension vulnerability in Merkle-Damgård construction",
        ],
        "nist_status": "DISALLOWED (NIST SP 800-131A Rev 2 prohibits MD5 for digital signatures and integrity)",
        "overall_risk": "CRITICAL",
        "migration_priority": "P0_IMMEDIATE_DEPRECATION",
        "operational_considerations": (
            "Legacy firmware implementations using MD5 must be isolated or wrapped with backwards-compatible "
            "envelopes immediately. Adversaries can generate collision payloads on consumer hardware in seconds."
        ),
        "suitable_for_ev_firmware": False,
    },
    {
        "algorithm": "SHA-1",
        "family": "SHA (Merkle-Damgård)",
        "digest_size_bits": 160,
        "collision_resistance": "BROKEN",
        "collision_complexity": "Practical (SHAttered attack, Stevens et al. 2017: 2^63.1 SHA-1 compressions)",
        "preimage_resistance": "UNDOCUMENTED_BREAK",
        "second_preimage_resistance": "SUSPECT",
        "authentication_capability": "NONE (unkeyed digest; vulnerable to length extension)",
        "known_weaknesses": [
            "SHAttered collision demonstrated in 2017 (two disparate PDFs with identical SHA-1)",
            "Chosen-prefix collision attack (Leurent & Peyrin 2020) with practical commercial cost",
            "Length extension vulnerability",
        ],
        "nist_status": "DEPRECATED (NIST announced complete phase-out of SHA-1 by Dec 31, 2030)",
        "overall_risk": "HIGH",
        "migration_priority": "P1_URGENT_PHASEOUT",
        "operational_considerations": (
            "Not suitable for new deployments. Transition to SHA-2 or SHA-3 required for regulatory compliance."
        ),
        "suitable_for_ev_firmware": False,
    },
    {
        "algorithm": "SHA-256",
        "family": "SHA-2 (Merkle-Damgård with Davis-Meyer compression)",
        "digest_size_bits": 256,
        "collision_resistance": "SECURE",
        "collision_complexity": "2^128 operations (infeasible with current and foreseeable classical computing)",
        "preimage_resistance": "SECURE (2^256 operations)",
        "second_preimage_resistance": "SECURE (2^256 operations)",
        "authentication_capability": "NONE (unkeyed digest; requires HMAC for authentication)",
        "known_weaknesses": [
            "Vulnerable to length-extension attacks if used directly as a MAC (H(key || msg))",
        ],
        "nist_status": "APPROVED (NIST FIPS 180-4 approved for all government and critical infrastructure)",
        "overall_risk": "LOW",
        "migration_priority": "P3_MAINTAIN_CURRENT",
        "operational_considerations": (
            "Hardware acceleration commonly available on modern ARM Cortex-M and embedded EVSE microcontrollers. "
            "Must be paired with HMAC (HMAC-SHA-256) when message authentication is required."
        ),
        "suitable_for_ev_firmware": True,
    },
    {
        "algorithm": "SHA3-256",
        "family": "Keccak (Sponge Construction)",
        "digest_size_bits": 256,
        "collision_resistance": "RECOMMENDED",
        "collision_complexity": "2^128 operations (maximum theoretical bound)",
        "preimage_resistance": "RECOMMENDED (2^256 operations)",
        "second_preimage_resistance": "RECOMMENDED (2^256 operations)",
        "authentication_capability": "NONE (unkeyed; use HMAC-SHA3-256 or KMAC for authentication)",
        "known_weaknesses": [
            "Zero known collision or preimage attacks against full 24-round Keccak-f[1600]",
            "Naturally immune to length-extension attacks due to sponge capacity termination",
        ],
        "nist_status": "RECOMMENDED (NIST FIPS 202 standard; modern cryptographic defense-in-depth)",
        "overall_risk": "LOW",
        "migration_priority": "P2_TARGET_MIGRATION_STANDARD",
        "operational_considerations": (
            "Provides structural diversity from Merkle-Damgård (SHA-2). Recommended target for EV charging "
            "firmware integrity frameworks to future-proof against structural cryptanalytic breakthroughs."
        ),
        "suitable_for_ev_firmware": True,
    },
    {
        "algorithm": "HMAC-SHA3-256",
        "family": "Keyed-Hash Message Authentication Code over Keccak Sponge",
        "digest_size_bits": 256,
        "collision_resistance": "EXCELLENT",
        "collision_complexity": "Keyed security bound (infeasible to forge without key)",
        "preimage_resistance": "EXCELLENT",
        "second_preimage_resistance": "EXCELLENT",
        "authentication_capability": "FULL_AUTHENTICATION (verifies origin and guarantees tamper-evident integrity)",
        "known_weaknesses": [
            "Zero known practical cryptanalytic vulnerabilities",
            "Requires robust key management and secure key distribution between EVSE and CSMS",
        ],
        "nist_status": "RECOMMENDED (NIST FIPS 198-1 / FIPS 202 compliant)",
        "overall_risk": "LOW",
        "migration_priority": "GOLD_STANDARD_AUTHENTICATION",
        "operational_considerations": (
            "Gold standard for EV charging message security. Protects against MITM tampering, message injection, "
            "and replay attacks when combined with fresh timestamps or sequence nonces."
        ),
        "suitable_for_ev_firmware": True,
    },
]


def get_risk_analysis_report() -> Dict[str, Any]:
    """
    Returns comprehensive qualitative cryptographic risk assessment.
    """
    return {
        "assessment_framework": "NIST SP 800-131A Rev 2 & FIPS 202 Cryptographic Risk Model",
        "evaluations": ALGORITHM_EVALUATIONS,
        "executive_summary": (
            "Legacy EV charging stations relying on MD5 for firmware and message integrity face CRITICAL "
            "operational risk due to practical, real-time collision generation. SHA-1 is HIGH risk and must "
            "be phased out. EVHashGuard recommends an immediate migration path to SHA3-256 for backward-compatible "
            "integrity envelopes, and HMAC-SHA3-256 for authenticated sessions."
        ),
        "migration_roadmap": [
            {
                "phase": "Phase 1: Edge Quarantine & Wrapping",
                "action": "Deploy EVHashGuard transparent wrapper to envelope legacy MD5 frames into SHA3-256 without modifying OCPP parsers.",
                "timeline": "Immediate (0-30 days)",
            },
            {
                "phase": "Phase 2: CSMS Key Distribution",
                "action": "Provision CSMS and EVSE shared credentials for HMAC-SHA3-256 authentication mode.",
                "timeline": "Short-term (30-90 days)",
            },
            {
                "phase": "Phase 3: Firmware Over-The-Air (FOTA) Native Upgrade",
                "action": "Reflash legacy EV charging controllers with native SHA-3 firmware verification routines.",
                "timeline": "Medium-term (90-180 days)",
            },
            {
                "phase": "Phase 4: Hard Downgrade Lockout",
                "action": "Disable legacy MD5 fallback entirely across all CSMS endpoints.",
                "timeline": "Final milestone",
            },
        ],
    }
