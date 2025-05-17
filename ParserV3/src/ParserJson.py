#from __future__ import annotations

import json
from typing import Any, Dict, List, TextIO, Optional


class JSONParsingError(Exception):
    """Podnoszone przy błędach parsowania lub walidacji JSON‐a."""


def parse_json(
    data: str,
    required_keys: Optional[List[str]] = None,
    key_types: Optional[Dict[str, type]] = None,
) -> Any:
    """
    Parsuje łańcuch JSON i opcjonalnie waliduje jego strukturę.

    :param data: tekst w formacie JSON
    :param required_keys: lista kluczy, które muszą wystąpić (tylko top-level)
    :param key_types: np. {"age": int, "active": bool}
    :raises JSONParsingError: gdy JSON jest zły lub walidacja się nie powiedzie
    :return: dowolny obiekt Pythona zwrócony przez ``json.loads``
    """
    try:
        result = json.loads(data)
    except (json.JSONDecodeError, TypeError) as exc:
        raise JSONParsingError(f"Nieprawidłowy JSON: {exc}") from None

    # --- klucze wymagane ----------------------------------------------------
    if required_keys and isinstance(result, dict):
        missing = [k for k in required_keys if k not in result]
        if missing:
            raise JSONParsingError(f"Brakujące klucze: {', '.join(missing)}")

    # --- sprawdzanie typów --------------------------------------------------
    if key_types and isinstance(result, dict):
        for key, expected in key_types.items():
            val = result.get(key)
            if val is not None and not isinstance(val, expected):
                raise JSONParsingError(
                    f"Klucz '{key}' powinien być typu {expected.__name__}, "
                    f"a otrzymano {type(val).__name__}."
                )

    return result


def parse_json_file(
    file_obj: TextIO,
    required_keys: Optional[List[str]] = None,
    key_types: Optional[Dict[str, type]] = None,
) -> Any:
    """
    Wczytuje JSON bezpośrednio z pliku (lub innego obiektu pliko-podobnego).

    :param file_obj: otwarty plik w trybie tekstowym
    Reszta parametrów jak w :pyfunc:`parse_json`.
    """
    try:
        content = file_obj.read()
    except UnicodeDecodeError as exc:
        raise JSONParsingError(f"Nie udało się odczytać pliku: {exc}") from None

    return parse_json(content, required_keys=required_keys, key_types=key_types)
