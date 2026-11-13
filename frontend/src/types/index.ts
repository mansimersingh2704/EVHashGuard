// TypeScript interfaces for all API response types

export interface HashResult {
  algorithm: string;
  digest: string;
  digest_length: number;
  execution_time_ms: number;
  security_status: string;
  security_description: string;
}

export interface HashCompareResponse {
  message: string;
  results: HashResult[];
}

export interface CollisionResult {
  input1_hex: string;
  input2_hex: string;
  md5_1: string;
  md5_2: string;
  collision_detected: boolean;
  sha256_1: string;
  sha256_2: string;
  sha3_256_1: string;
  sha3_256_2: string;
  explanation: string;
  inputs_differ: boolean;
}

export interface Station {
  station_id: string;
  vendor: string;
  model: string;
  firmware_version: string;
  location: string;
}

export interface LegacyIntegrityMetadata {
  _legacy_integrity: {
    algorithm: string;
    digest: string;
    timestamp: string;
    firmware_version: string;
  };
  _note: string;
}

export interface EVMessage {
  ocpp_message: unknown[];
  legacy_integrity_metadata: LegacyIntegrityMetadata;
  note: string;
}

export interface LegacyVerifyResult {
  verified: boolean;
  algorithm: string;
  expected_digest: string;
  computed_digest: string;
  status: string;
  message: string;
}

export interface WrappedMessage {
  wrapped_message: Record<string, unknown>;
  mode: string;
  algorithm: string;
}

export interface VerificationResult {
  verified: boolean;
  algorithm: string;
  mode: string;
  message: string;
  details: Record<string, unknown>;
}

export interface AttackResult {
  attack_type: string;
  detected: boolean;
  expected_outcome: string;
  actual_outcome: string;
  security_explanation: string;
  details: Record<string, unknown>;
}

export interface AlgorithmRisk {
  algorithm: string;
  collision_resistance: string;
  preimage_resistance: string;
  second_preimage_resistance: string;
  key_length: string;
  recommended: boolean;
  risk_level: string;
  description: string;
}

export interface RiskAnalysis {
  algorithms: AlgorithmRisk[];
  recommendations: string[];
  summary: string;
}

export interface DashboardStats {
  total_messages: number;
  integrity_checks: number;
  attacks_detected: number;
  migration_events: number;
  legacy_md5_usage: number;
  sha3_usage: number;
  security_events_timeline: Array<{ date: string; events: number; attacks: number }>;
  algorithm_distribution: Array<{ algorithm: string; count: number }>;
}

export interface AuditLog {
  id: number;
  event_type: string;
  station_id: string;
  algorithm: string;
  status: string;
  details: string;
  created_at: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
}
