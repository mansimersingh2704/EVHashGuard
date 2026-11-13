import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Sample charging stations participating in the EVHashGuard network
CHARGING_STATIONS = [
    {
        "station_id": "CS-NORDIC-001",
        "vendor": "NordicVolt Systems",
        "model": "TerraCharge-DC50",
        "firmware_version": "v1.4.2-legacy-md5",
        "location": "Oslo Central Hub, Station 4",
        "supports_legacy": True,
        "migration_ready": True,
    },
    {
        "station_id": "CS-ALPIN-002",
        "vendor": "AlpinGrid Energy",
        "model": "EcoPoint-AC22",
        "firmware_version": "v1.2.0-legacy-md5",
        "location": "Zurich Tech Park, Bay 2",
        "supports_legacy": True,
        "migration_ready": True,
    },
    {
        "station_id": "CS-METRO-003",
        "vendor": "VoltDynamics",
        "model": "MetroRapid-150kW",
        "firmware_version": "v2.0.1-legacy-md5",
        "location": "London Victoria Depot",
        "supports_legacy": True,
        "migration_ready": True,
    },
    {
        "station_id": "CS-HIGHWAY-004",
        "vendor": "SuperWatt Mobility",
        "model": "HighwayUltra-350",
        "firmware_version": "v1.8.9-legacy-md5",
        "location": "Autobahn A8 Service Area",
        "supports_legacy": True,
        "migration_ready": True,
    },
    {
        "station_id": "CS-PORT-005",
        "vendor": "HarborPower Corp",
        "model": "MarineCharge-Dual",
        "firmware_version": "v1.1.5-legacy-md5",
        "location": "Rotterdam Freight Terminal B",
        "supports_legacy": True,
        "migration_ready": True,
    },
]


def generate_ocpp_payload(station_id: str, message_type: str) -> Dict[str, Any]:
    """
    Generates realistic OCPP 1.6 payload dictionaries conforming to OCA specification.
    """
    station = next((s for s in CHARGING_STATIONS if s["station_id"] == station_id), CHARGING_STATIONS[0])
    now_iso = datetime.now(timezone.utc).isoformat()

    if message_type == "BootNotification":
        return {
            "chargePointVendor": station["vendor"],
            "chargePointModel": station["model"],
            "chargePointSerialNumber": f"SN-{station_id[-4:]}-8829",
            "firmwareVersion": station["firmware_version"],
            "iccid": "89445012022093847291",
            "imsi": "204041103982019",
            "meterType": "LEM-DCBM-400A",
            "meterSerialNumber": f"LEM-{station_id[-3:]}-99",
        }
    elif message_type == "Heartbeat":
        return {
            "currentTime": now_iso,
        }
    elif message_type == "StatusNotification":
        return {
            "connectorId": 1,
            "errorCode": "NoError",
            "info": "Station operational and ready for vehicle connection",
            "status": "Available",
            "timestamp": now_iso,
            "vendorId": station["vendor"],
        }
    elif message_type == "Authorize":
        return {
            "idTag": "TAG-B8A1C294F0",
        }
    elif message_type == "StartTransaction":
        return {
            "connectorId": 1,
            "idTag": "TAG-B8A1C294F0",
            "meterStart": 142850,
            "reservationId": 1042,
            "timestamp": now_iso,
        }
    elif message_type == "StopTransaction":
        return {
            "idTag": "TAG-B8A1C294F0",
            "meterStop": 149320,
            "timestamp": now_iso,
            "transactionId": 883921,
            "reason": "EVDisconnected",
            "transactionData": [
                {
                    "timestamp": now_iso,
                    "sampledValue": [
                        {"value": "6470", "context": "Transaction.End", "format": "Raw", "measurand": "Energy.Active.Import.Register", "unit": "Wh"}
                    ]
                }
            ]
        }
    elif message_type == "MeterValues":
        return {
            "connectorId": 1,
            "transactionId": 883921,
            "meterValue": [
                {
                    "timestamp": now_iso,
                    "sampledValue": [
                        {"value": "398.4", "context": "Sample.Periodic", "format": "Raw", "measurand": "Voltage", "unit": "V"},
                        {"value": "124.6", "context": "Sample.Periodic", "format": "Raw", "measurand": "Current.Import", "unit": "A"},
                        {"value": "49640", "context": "Sample.Periodic", "format": "Raw", "measurand": "Power.Active.Import", "unit": "W"},
                        {"value": "48.2", "context": "Sample.Periodic", "format": "Raw", "measurand": "Temperature", "unit": "Celsius"},
                    ]
                }
            ]
        }
    elif message_type == "FirmwareStatusNotification":
        return {
            "status": "InstallationFailed",
            "firmwareVersion": station["firmware_version"],
            "timestamp": now_iso,
        }
    else:
        # Default generic diagnostic payload
        return {
            "stationId": station_id,
            "diagnosticData": "Operational test packet",
            "timestamp": now_iso,
        }


def generate_simulated_ev_message(station_id: str, message_type: str) -> Dict[str, Any]:
    """
    Generates a full simulated OCPP 1.6 message frame along with separate legacy MD5 integrity metadata.

    IMPORTANT NOTE:
    Standard OCPP 1.6 JSON over WebSocket defines frames as [MessageTypeId, UniqueId, Action, Payload].
    Standard OCPP 1.6 does NOT mandate or specify MD5 integrity fields.
    The 'legacy_integrity' block below simulates an outdated vendor-specific firmware extension.
    """
    message_id = str(uuid.uuid4())
    payload = generate_ocpp_payload(station_id, message_type)

    # Standard OCPP 1.6 CALL message is a 4-element JSON array: [2, UniqueId, Action, Payload]
    ocpp_frame = [2, message_id, message_type, payload]

    # Vendor-specific legacy MD5 computation on the canonical payload
    canonical_payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
    legacy_md5_digest = hashlib.md5(canonical_payload_bytes).hexdigest()

    legacy_integrity_metadata = {
        "extension_standard": "VENDOR_PROPRIETARY_LEGACY_EXTENSION",
        "disclaimer": "Simulated vendor extension; standard OCPP 1.6 does NOT mandate MD5 integrity checks.",
        "algorithm": "MD5",
        "digest": legacy_md5_digest,
        "digest_bits": 128,
        "canonical_bytes_length": len(canonical_payload_bytes),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "station_id": station_id,
        "security_advisory": "MD5 is cryptographically compromised. Subject to collision and forgery risks.",
    }

    return {
        "station_id": station_id,
        "message_id": message_id,
        "message_type": message_type,
        "ocpp_message": ocpp_frame,
        "legacy_integrity_metadata": legacy_integrity_metadata,
        "note": "Standard OCPP frame preserved intact; legacy integrity metadata transported in vendor wrapper.",
    }
