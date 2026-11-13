# EVHashGuard: REST API Technical Reference

## Base URL
Default local development: `http://localhost:8000/api`
Interactive Swagger Documentation: `http://localhost:8000/docs`
ReDoc Specification: `http://localhost:8000/redoc`

---

## 1. System Health & Cryptographic Capabilities

### `GET /api/health`
Checks server health and active cryptographic algorithm support.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "service": "EVHashGuard CSMS Cryptographic Wrapper",
  "version": "1.0.0",
  "timestamp": "2026-11-13T22:45:00.000000+00:00",
  "cryptography": {
    "sha3_supported": true,
    "hmac_sha3_supported": true,
    "legacy_md5_simulation": true
  }
}
```

---

## 2. Cryptographic Hash Laboratory

### `POST /api/hash/compare`
Computes cryptographic digests, execution time, and security ratings across requested algorithms.

**Request Body:**
```json
{
  "message": "EV_TELEMETRY_PACKET_2026",
  "algorithms": ["md5", "sha1", "sha256", "sha3_256"]
}
```

**Response (200 OK):**
```json
{
  "message": "EV_TELEMETRY_PACKET_2026",
  "results": [
    {
      "algorithm": "md5",
      "digest": "79054025255fb1a26e4bc422aef54eb4",
      "digest_length": 128,
      "execution_time_ms": 0.0412,
      "security_status": "BROKEN",
      "security_description": "MD5 is cryptographically broken..."
    },
    {
      "algorithm": "sha3_256",
      "digest": "076a500a465a0d86630dc77775ffab9bfa2909157ebfb82199ae7422532ef305",
      "digest_length": 256,
      "execution_time_ms": 0.0621,
      "security_status": "RECOMMENDED",
      "security_description": "SHA3-256 (Keccak sponge construction) is NIST-recommended..."
    }
  ]
}
```

---

## 3. MD5 Collision Verification

### `POST /api/collision/verify`
Evaluates two binary inputs for MD5 collision status. If inputs are omitted, loads the verified Wang/Stevens test vector.

**Request Body (Optional):**
```json
{
  "input1_hex": "4dc968ff0ee35c20...",
  "input2_hex": "4dc968ff0ee35c20..."
}
```

**Response (200 OK):**
```json
{
  "input1_hex": "4dc968ff...",
  "input2_hex": "4dc968ff...",
  "inputs_differ": true,
  "collision_detected": true,
  "md5_1": "008ee33a9d58b51cfeb425b0959121c9",
  "md5_2": "008ee33a9d58b51cfeb425b0959121c9",
  "sha256_1": "54bcb9a4fda31e4f...",
  "sha256_2": "90774a6455a2bdb7...",
  "sha3_256_1": "91a7b190812eb4f7...",
  "sha3_256_2": "5ab1b8119dfd9a51...",
  "explanation": "Authentic differential collision pair for MD5...",
  "source": "Marc Stevens (2007) / Wang & Yu (2005)"
}
```

---

## 4. EV Firmware Message Simulator

### `GET /api/simulator/stations`
Lists simulated charging station endpoints with firmware version and vendor metadata.

### `POST /api/ev/messages`
Generates a representative OCPP 1.6-J frame along with simulated legacy vendor MD5 integrity block.

**Request Body:**
```json
{
  "station_id": "CS-NORDIC-001",
  "message_type": "BootNotification"
}
```

---

## 5. SHA-3 Migration Wrapper

### `POST /api/migration/wrap`
Envelopes an incoming payload into an EVHashGuard cryptographic wrapper.

**Request Body:**
```json
{
  "payload": {
    "station_id": "CS-NORDIC-001",
    "action": "MeterValues",
    "meterStop": 142850
  },
  "mode": "hmac_sha3_256"
}
```

### `POST /api/migration/verify`
Verifies the cryptographic envelope and checks downgrade policy before forwarding to the legacy OCPP parser.

**Request Body:**
```json
{
  "wrapped_message": { ... },
  "mode": "hmac_sha3_256"
}
```

---

## 6. Attack Simulation Laboratory

- `POST /api/attacks/tampering`
- `POST /api/attacks/collision`
- `POST /api/attacks/replay`
- `POST /api/attacks/missing-metadata`
- `POST /api/attacks/invalid-tag`
- `POST /api/attacks/downgrade`
- `POST /api/attacks/firmware-mod`

---

## 7. Metrics & Security Audit Logs

### `GET /api/dashboard/stats`
Computes live aggregate counts from the SQLite database tables.

### `GET /api/audit/logs?limit=50&offset=0`
Returns paginated security event log records.
