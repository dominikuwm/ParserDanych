import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional, TextIO


class XMLParsingError(Exception):
    """Używane, gdy cokolwiek pójdzie nie tak przy parsowaniu/walidacji."""


def parse_xml(
    xml_input: TextIO | str,
    required_tags: Optional[List[str]] = None,
    required_attrs: Optional[Dict[str, List[str]]] = None,
    attr_types: Optional[Dict[str, Any]] = None,
    unique_tags: Optional[List[str]] = None,
) -> ET.Element:

    #wczytanie danych
    try:
        if hasattr(xml_input, "read"):
            root = ET.parse(xml_input).getroot()
        elif isinstance(xml_input, str):
            root = ET.fromstring(xml_input)
        else:
            raise XMLParsingError(
                "Podaj albo string z XML-em, albo otwarty plik."
            )
    except ET.ParseError as exc:
        raise XMLParsingError(f"Niepoprawny XML: {exc}") from None

    #wymóg obecności konkretnych tagów
    if required_tags:
        for tag in required_tags:
            if not root.findall(f".//{tag}"):
                raise XMLParsingError(f"Brak wymaganego taga <{tag}>.")

    #sprawdzanie atrybutów
    if required_attrs:
        for tag, attrs in required_attrs.items():
            for elem in root.findall(f".//{tag}"):
                for attr in attrs:
                    if attr not in elem.attrib:
                        raise XMLParsingError(
                            f"<{tag}> nie ma atrybutu '{attr}'."
                        )

    #kontrola typów atrybutów
    if attr_types:
        for key, expected in attr_types.items():
            if "@" not in key:
                raise XMLParsingError(
                    "Użyj formatu 'tag@attr' w attr_types."
                )

            tag, attr = key.split("@", maxsplit=1)
            for elem in root.findall(f".//{tag}"):
                if attr not in elem.attrib:
                    continue  # brak atrybutu – nic nie sprawdzamy

                val = elem.attrib[attr]

                # a) bool zapisany jako "true"/"false"
                if expected is bool:
                    if val.lower() not in ("true", "false"):
                        raise XMLParsingError(
                            f"Atrybut {attr} w <{tag}> nie jest bool-em."
                        )

                # b) data ISO (YYYY-MM-DD)
                elif expected == "iso":
                    try:
                        datetime.strptime(val, "%Y-%m-%d")
                    except ValueError:
                        raise XMLParsingError(
                            f"Data '{val}' w <{tag}> "
                            "ma zły format YYYY-MM-DD."
                        )

                # c) zwykłe typy (int, float, str…)
                else:
                    try:
                        expected(val)  # rzutowanie testowe
                    except (ValueError, TypeError):
                        raise XMLParsingError(
                            f"Zły typ atrybutu {attr} w <{tag}> "
                            f"(oczekiwano {expected})."
                        )

    #tagi, które muszą być unikalne
    if unique_tags:
        for tag in unique_tags:
            if len(root.findall(f".//{tag}")) > 1:
                raise XMLParsingError(
                    f"Tego taga <{tag}> może być maksymalnie jeden."
                )

    return root


def parse_xml_file(
    file_obj: TextIO,
    required_tags: Optional[List[str]] = None,
    required_attrs: Optional[Dict[str, List[str]]] = None,
    attr_types: Optional[Dict[str, Any]] = None,
    unique_tags: Optional[List[str]] = None,
) -> ET.Element:

    try:
        xml_text = file_obj.read()
    except UnicodeDecodeError as exc:
        raise XMLParsingError(
            f"Nie udało się odczytać pliku XML: {exc}"
        ) from None

    return parse_xml(
        xml_text,
        required_tags=required_tags,
        required_attrs=required_attrs,
        attr_types=attr_types,
        unique_tags=unique_tags,
    )
