import json
from typing import Any, Optional, List, Dict

class JSONParsingError(Exception):
    pass

def parse_json(
    file_obj: Any,  # akceptujemy str albo TextIO (plik)
    required_fields: Optional[List[str]] = None,
    expected_types: Optional[Dict[str, type]] = None
) -> Any:
    """
    Parses JSON data from a string or file-like object and returns the Python object.

    :param file_obj: JSON data as a string or file-like object.
    :param required_fields: List of required keys to validate at the root level (if dict).
    :param expected_types: Dict specifying expected types for certain fields.
    :return: Parsed JSON object (dict, list, or primitive)
    :raises JSONParsingError: On parse or validation errors.
    """
    try:
        if isinstance(file_obj, str):
            data = json.loads(file_obj)
        else:
            data = json.load(file_obj)

        # Teraz akceptujemy dowolny typ top-level JSON, nie tylko dict/list
        # Jeśli chcesz wymagać dict/list, to tu możesz dodać warunek

        # Jeśli data jest dict, to wykonujemy walidacje required_fields i expected_types
        if isinstance(data, dict):
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    raise JSONParsingError(f"Missing required fields: {', '.join(missing_fields)}")

            if expected_types:
                for field, expected_type in expected_types.items():
                    if field in data and not isinstance(data[field], expected_type):
                        raise JSONParsingError(
                            f"Field '{field}' expected to be of type {expected_type.__name__}, "
                            f"but got {type(data[field]).__name__}."
                        )

        return data

    except json.JSONDecodeError as e:
        raise JSONParsingError(f"Invalid JSON format: {str(e)}")
    except UnicodeDecodeError:
        raise JSONParsingError("Unable to decode JSON file. Please check encoding.")
    except (RecursionError, ValueError) as e:
        raise JSONParsingError(f"JSON too deeply nested or invalid structure: {str(e)}")
    except Exception as e:
        raise JSONParsingError(f"An unexpected error occurred: {str(e)}")
