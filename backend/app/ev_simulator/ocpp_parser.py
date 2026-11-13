from typing import Dict, Any, List, Tuple


class OCPPParser:
    """
    Standard-compliant strict validator and minimal parser for OCPP 1.6-J messages.
    Validates protocol frame structures without mutating the original payload.
    """

    MESSAGE_TYPES = {
        2: "CALL",
        3: "CALLRESULT",
        4: "CALLERROR",
    }

    # Standard OCPP 1.6 actions
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
        "ChangeAvailability",
        "ChangeConfiguration",
        "ClearCache",
        "GetConfiguration",
        "RemoteStartTransaction",
        "RemoteStopTransaction",
        "Reset",
        "UnlockConnector",
    }

    # Standard OCPP 1.6 Error Codes
    VALID_ERROR_CODES = {
        "NotImplemented",
        "NotSupported",
        "InternalError",
        "ProtocolError",
        "SecurityError",
        "FormationViolation",
        "PropertyConstraintViolation",
        "OccurrenceConstraintViolation",
        "TypeConstraintViolation",
        "GenericError",
    }

    @classmethod
    def validate_and_parse(cls, frame: Any) -> Tuple[bool, Dict[str, Any], str]:
        """
        Validates standard OCPP 1.6 message array format:
        CALL: [2, "<UniqueId>", "<Action>", {<Payload>}] (exactly 4 elements)
        CALLRESULT: [3, "<UniqueId>", {<Payload>}] (exactly 3 elements)
        CALLERROR: [4, "<UniqueId>", "<ErrorCode>", "<ErrorDescription>", {<ErrorDetails>}] (exactly 5 elements)
        """
        if not isinstance(frame, list):
            return False, {}, "PARSER_ERROR: Message must be a JSON array per OCPP 1.6 specification"

        if len(frame) < 3:
            return False, {}, "PARSER_ERROR: Frame has insufficient elements for an OCPP 1.6 message"

        msg_type_id = frame[0]
        if not isinstance(msg_type_id, int) or msg_type_id not in cls.MESSAGE_TYPES:
            return False, {}, f"PARSER_ERROR: Invalid OCPP MessageTypeId: {msg_type_id} (expected integer 2, 3, or 4)"

        # Strict UniqueId type validation - DO NOT coerce non-string values
        unique_id = frame[1]
        if not isinstance(unique_id, str):
            return False, {}, f"PARSER_ERROR: UniqueId must be a string, got {type(unique_id).__name__}"
        if not (1 <= len(unique_id) <= 36):
            return False, {}, f"PARSER_ERROR: UniqueId length must be between 1 and 36 characters, got {len(unique_id)}"

        if msg_type_id == 2:  # CALL: [2, UniqueId, Action, Payload]
            if len(frame) != 4:
                return False, {}, f"PARSER_ERROR: OCPP CALL frame requires exactly 4 elements, got {len(frame)}"
            
            action = frame[2]
            payload = frame[3]

            if not isinstance(action, str):
                return False, {}, f"PARSER_ERROR: Action must be a string, got {type(action).__name__}"
            if not action.strip():
                return False, {}, "PARSER_ERROR: Action cannot be empty"
            if not isinstance(payload, dict):
                return False, {}, f"PARSER_ERROR: CALL payload must be a JSON object (dict), got {type(payload).__name__}"

            return True, {
                "message_type_id": msg_type_id,
                "message_type_name": "CALL",
                "unique_id": unique_id,
                "action": action,
                "payload": payload,
                "is_standard_action": action in cls.VALID_ACTIONS,
            }, "Valid OCPP 1.6 CALL message"

        elif msg_type_id == 3:  # CALLRESULT: [3, UniqueId, Payload]
            if len(frame) != 3:
                return False, {}, f"PARSER_ERROR: OCPP CALLRESULT frame requires exactly 3 elements, got {len(frame)}"
            
            payload = frame[2]
            if not isinstance(payload, dict):
                return False, {}, f"PARSER_ERROR: CALLRESULT payload must be a JSON object (dict), got {type(payload).__name__}"

            return True, {
                "message_type_id": msg_type_id,
                "message_type_name": "CALLRESULT",
                "unique_id": unique_id,
                "payload": payload,
            }, "Valid OCPP 1.6 CALLRESULT message"

        elif msg_type_id == 4:  # CALLERROR: [4, UniqueId, ErrorCode, ErrorDescription, ErrorDetails]
            if len(frame) != 5:
                return False, {}, f"PARSER_ERROR: OCPP CALLERROR frame requires exactly 5 elements, got {len(frame)}"
            
            error_code = frame[2]
            error_desc = frame[3]
            error_details = frame[4]

            if not isinstance(error_code, str) or not error_code.strip():
                return False, {}, f"PARSER_ERROR: ErrorCode must be a non-empty string, got {type(error_code).__name__}"
            if not isinstance(error_desc, str):
                return False, {}, f"PARSER_ERROR: ErrorDescription must be a string, got {type(error_desc).__name__}"
            if not isinstance(error_details, dict):
                return False, {}, f"PARSER_ERROR: ErrorDetails must be a JSON object (dict), got {type(error_details).__name__}"

            return True, {
                "message_type_id": msg_type_id,
                "message_type_name": "CALLERROR",
                "unique_id": unique_id,
                "error_code": error_code,
                "error_description": error_desc,
                "error_details": error_details,
                "is_standard_error_code": error_code in cls.VALID_ERROR_CODES,
            }, "Valid OCPP 1.6 CALLERROR message"

        return False, {}, "PARSER_ERROR: Unhandled frame structure"
