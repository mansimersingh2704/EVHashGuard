from typing import Dict, Any, List, Tuple


class OCPPParser:
    """
    Standard-compliant minimal parser for OCPP 1.6-J messages.
    Validates protocol frame structure without mutating the original payload.
    """

    MESSAGE_TYPES = {
        2: "CALL",
        3: "CALLRESULT",
        4: "CALLERROR",
    }

    VALID_ACTIONS = {
        "BootNotification",
        "Heartbeat",
        "StatusNotification",
        "Authorize",
        "StartTransaction",
        "StopTransaction",
        "MeterValues",
        "FirmwareStatusNotification",
        "DiagnosticsStatusNotification",
        "DataTransfer",
    }

    @classmethod
    def validate_and_parse(cls, frame: Any) -> Tuple[bool, Dict[str, Any], str]:
        """
        Validates standard OCPP 1.6 message array format:
        CALL: [2, "<UniqueId>", "<Action>", {<Payload>}]
        CALLRESULT: [3, "<UniqueId>", {<Payload>}]
        CALLERROR: [4, "<UniqueId>", "<ErrorCode>", "<ErrorDescription>", {<ErrorDetails>}]
        """
        if not isinstance(frame, list):
            return False, {}, "Message must be a JSON array per OCPP 1.6 specification"

        if len(frame) < 3:
            return False, {}, "Frame has insufficient elements for an OCPP 1.6 message"

        msg_type_id = frame[0]
        if msg_type_id not in cls.MESSAGE_TYPES:
            return False, {}, f"Invalid OCPP MessageTypeId: {msg_type_id} (expected 2, 3, or 4)"

        unique_id = str(frame[1])
        if not unique_id or not isinstance(unique_id, str):
            return False, {}, "UniqueId must be a non-empty string"

        if msg_type_id == 2:  # CALL
            if len(frame) != 4:
                return False, {}, f"OCPP CALL frame requires exactly 4 elements, got {len(frame)}"
            action = frame[2]
            payload = frame[3]

            if not isinstance(action, str):
                return False, {}, "Action must be a string"
            if not isinstance(payload, dict):
                return False, {}, "Payload must be a JSON object"

            return True, {
                "message_type_id": msg_type_id,
                "message_type_name": "CALL",
                "unique_id": unique_id,
                "action": action,
                "payload": payload,
                "is_known_action": action in cls.VALID_ACTIONS,
            }, "Valid OCPP 1.6 CALL message"

        elif msg_type_id == 3:  # CALLRESULT
            payload = frame[2]
            if not isinstance(payload, dict):
                return False, {}, "CALLRESULT payload must be a JSON object"
            return True, {
                "message_type_id": msg_type_id,
                "message_type_name": "CALLRESULT",
                "unique_id": unique_id,
                "payload": payload,
            }, "Valid OCPP 1.6 CALLRESULT message"

        else:  # CALLERROR
            error_code = frame[2]
            error_desc = frame[3] if len(frame) > 3 else ""
            error_details = frame[4] if len(frame) > 4 else {}
            return True, {
                "message_type_id": msg_type_id,
                "message_type_name": "CALLERROR",
                "unique_id": unique_id,
                "error_code": error_code,
                "error_description": error_desc,
                "error_details": error_details,
            }, "Valid OCPP 1.6 CALLERROR message"
