import json
from typing import Any, Dict, List, Optional, TextIO


class JSONParsingError(Exception):
    """Błąd podczas parsowania lub walidacji JSON-a."""


def parse_json(
        data: str,
        required_keys: Optional[List[str]] = None,
        key_types: Optional[Dict[str, type]] = None,
) -> Any:
    try:
        result = json.loads(data)
    except (json.JSONDecodeError, TypeError) as exc:
        raise JSONParsingError(f"Nieprawidłowy JSON: {exc}") from None

    # klucze wymagane
    if required_keys and isinstance(result, dict):
        missing = [k for k in required_keys if k not in result]
        if missing:
            raise JSONParsingError(f"Brakujące klucze: {', '.join(missing)}")

    # sprawdzanie typów
    if key_types and isinstance(result, dict):
        for key, expected in key_types.items():
            val = result.get(key)
            if val is not None and not isinstance(val, expected):
                raise JSONParsingError(
                    f"Klucz '{key}' powinien być typu "
                    f"{expected.__name__}, a otrzymano "
                    f"{type(val).__name__}."
                )

    return result


def parse_json_file(
        file_obj: TextIO,
        required_keys: Optional[List[str]] = None,
        key_types: Optional[Dict[str, type]] = None,
) -> Any:
    try:
        content = file_obj.read()
    except UnicodeDecodeError as exc:
        raise JSONParsingError(
            f"Nie udało się odczytać pliku: {exc}"
        ) from None

    return parse_json(
        content,
        required_keys=required_keys,
        key_types=key_types,
    )
