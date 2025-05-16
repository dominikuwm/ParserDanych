import json

class JSONParsingError(Exception):
    """Custom exception for JSON parsing errors."""
    pass

def parse_json(data, required_keys=None, key_types=None):
    """
    Parses JSON data and performs validation.

    :param data: JSON string to parse.
    :param required_keys: List of required top-level keys.
    :param key_types: Dict specifying expected types for keys, e.g., {"age": int}.
    :return: Parsed JSON object.
    :raises JSONParsingError: On parsing or validation failure.
    """
    try:
        result = json.loads(data)
    except (json.JSONDecodeError, TypeError) as e:
        raise JSONParsingError(f"Invalid JSON: {e}")

    if required_keys and isinstance(result, dict):
        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            raise JSONParsingError(f"Missing required keys: {', '.join(missing_keys)}")

    if key_types and isinstance(result, dict):
        for key, expected_type in key_types.items():
            value = result.get(key)
            if value is not None and not isinstance(value, expected_type):
                raise JSONParsingError(
                    f"Key '{key}' should be of type {expected_type.__name__}, "
                    f"but got {type(value).__name__}."
                )

    return result
