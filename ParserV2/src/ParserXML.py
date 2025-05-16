import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, TextIO, Union
import re

class XMLParsingError(Exception):
    pass

def parse_xml(
    file_obj: Union[TextIO, str],
    required_tags: Optional[List[str]] = None,
    required_attributes: Optional[Dict[str, List[str]]] = None,
    attribute_types: Optional[Dict[str, Union[type, str]]] = None,
    unique_elements: Optional[List[str]] = None
) -> ET.Element:
    try:
        if hasattr(file_obj, 'read'):
            tree = ET.parse(file_obj)
            root = tree.getroot()
        elif isinstance(file_obj, str):
            root = ET.fromstring(file_obj)
        else:
            raise XMLParsingError("Input must be a string or file-like object.")

        if required_tags:
            missing_tags = [tag for tag in required_tags if not root.findall(f".//{tag}")]
            if missing_tags:
                raise XMLParsingError(f"Missing required tags: {', '.join(missing_tags)}")

        if required_attributes:
            for tag, attrs in required_attributes.items():
                elements = root.findall(f".//{tag}")
                if not elements:
                    raise XMLParsingError(f"Tag '{tag}' not found in XML.")
                for elem in elements:
                    missing_attrs = [a for a in attrs if a not in elem.attrib]
                    if missing_attrs:
                        raise XMLParsingError(
                            f"Element <{tag}> is missing required attributes: {', '.join(missing_attrs)}"
                        )

        if attribute_types:
            for key, expected_type in attribute_types.items():
                try:
                    tag, attr = key.split("@")
                except ValueError:
                    raise XMLParsingError(
                        f"Invalid attribute_types key format: '{key}'. Expected 'tag@attribute'."
                    )
                elements = root.findall(f".//{tag}")
                for elem in elements:
                    if attr in elem.attrib:
                        value = elem.attrib[attr]
                        try:
                            if expected_type == bool:
                                if value.lower() not in ("true", "false"):
                                    raise ValueError(f"Invalid boolean string: {value}")
                            elif expected_type == "date_iso8601":
                                pattern = r"^\d{4}-(0[1-9]|1[0-2])-\d{2}$"
                                if not re.match(pattern, value):
                                    raise ValueError(f"Invalid ISO8601 date: {value}")
                            else:
                                expected_type(value)
                        except (ValueError, TypeError) as err:
                            raise XMLParsingError(
                                f"Attribute '{attr}' in <{tag}> should be of type "
                                f"{expected_type if expected_type != 'date_iso8601' else 'ISO8601 date'}, "
                                f"but got value '{value}'. Error: {err}"
                            )

        if unique_elements:
            for tag in unique_elements:
                elems = root.findall(f".//{tag}")
                if len(elems) > 1:
                    raise XMLParsingError(
                        f"Element '{tag}' should be unique but found multiple occurrences."
                    )

        return root

    except ET.ParseError as e:
        raise XMLParsingError(f"Invalid XML format: {str(e)}")
    except UnicodeDecodeError:
        raise XMLParsingError("Unable to decode XML file. Please check encoding.")
    except Exception as e:
        raise XMLParsingError(f"An unexpected error occurred: {str(e)}")
