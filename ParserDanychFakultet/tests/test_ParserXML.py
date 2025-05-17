import pytest

from src.ParserXML import XMLParsingError, parse_xml

#fragmenty komunikatów

_PL_BAD_XML = "Niepoprawny XML"
_PL_MISSING_TAG = "Brak wymaganego taga"
_PL_MISSING_ATTR = "nie ma atrybutu"
_PL_BOOL_ERROR = "nie jest bool-em"
_PL_WRONG_TYPE = "Zły typ atrybutu"
_PL_DATE_ERROR = "zły format (YYYY-MM-DD)"
_PL_FORMAT_DIRECTIVE = "Użyj formatu"
_PL_UNIQUE_TAG = "może być maksymalnie jeden"
_PL_BAD_INPUT_TYPE = "string z XML-em, albo otwarty plik"


# Podstawowe scenariusze parsowania



class TestXMLParserBasic:
    """Proste, poprawne przypadki."""

    def test_parse_simple_element(self) -> None:
        root = parse_xml("<root/>")
        assert root.tag == "root"

    def test_parse_nested_elements(self) -> None:
        xml = "<root><child/></root>"
        assert parse_xml(xml).find("child") is not None

    def test_parse_element_with_attributes(self) -> None:
        xml = '<root attr="value"/>'
        assert parse_xml(xml).attrib["attr"] == "value"

    def test_required_tag_ok(self) -> None:
        xml = "<root><req/></root>"

        parse_xml(xml, required_tags=["req"])

    def test_required_tag_missing(self) -> None:
        with pytest.raises(
            XMLParsingError,
            match=rf"{_PL_MISSING_TAG} <req>",
        ):
            parse_xml("<root/>", required_tags=["req"])



# Walidacja atrybutów i ich typów



class TestXMLParserAttributes:
    """Sprawdzanie obecności i typów atrybutów."""

    def test_required_attr_ok(self) -> None:
        xml = '<root><item id="1"/></root>'
        parse_xml(xml, required_attrs={"item": ["id"]})

    def test_required_attr_missing(self) -> None:
        xml = "<root><item/></root>"
        pattern = rf"<item> {_PL_MISSING_ATTR} 'id'"
        with pytest.raises(XMLParsingError, match=pattern):
            parse_xml(xml, required_attrs={"item": ["id"]})

    def test_attr_type_ok(self) -> None:
        xml = '<root><item id="42"/></root>'
        parse_xml(xml, attr_types={"item@id": int})

    def test_attr_type_wrong(self) -> None:
        xml = '<root><item id="abc"/></root>'
        with pytest.raises(XMLParsingError, match=_PL_WRONG_TYPE):
            parse_xml(xml, attr_types={"item@id": int})

    def test_bool_attr_ok(self) -> None:
        xml = '<root><item flag="true"/></root>'
        parse_xml(xml, attr_types={"item@flag": bool})

    def test_bool_attr_wrong(self) -> None:
        xml = '<root><item flag="maybe"/></root>'
        with pytest.raises(XMLParsingError, match=_PL_BOOL_ERROR):
            parse_xml(xml, attr_types={"item@flag": bool})



# Unikalność elementów



class TestXMLParserUniqueness:
    """Pilnowanie, by wybrane tagi nie powtarzały się."""

    def test_unique_tag_ok(self) -> None:
        xml = "<root><uniq/></root>"
        parse_xml(xml, unique_tags=["uniq"])

    def test_unique_tag_violation(self) -> None:
        xml = "<root><uniq/><uniq/></root>"
        with pytest.raises(XMLParsingError, match=_PL_UNIQUE_TAG):
            parse_xml(xml, unique_tags=["uniq"])



# Scenariusze błędne / wyjątkowe



class TestXMLParserErrors:
    """Różne formy błędnego wejścia."""

    @pytest.mark.parametrize(
        "bad_xml",
        [
            "<root><unclosed></root>",
            "<root><1tag></1tag></root>",
            "<root id=1></root>",
            '<root id="1></root>',
            "<root>&invalid;</root>",
            "<a><b></a></b>",
        ],
    )
    def test_bad_xml_formats(self, bad_xml: str) -> None:
        with pytest.raises(XMLParsingError, match=_PL_BAD_XML):
            parse_xml(bad_xml)

    def test_bad_input_type(self) -> None:
        with pytest.raises(XMLParsingError, match=_PL_BAD_INPUT_TYPE):
            parse_xml(123)

    def test_bad_attr_types_key_format(self) -> None:
        xml = "<root><x/></root>"
        with pytest.raises(XMLParsingError, match=_PL_FORMAT_DIRECTIVE):
            parse_xml(xml, attr_types={"wrong": int})


#
# Przypadki brzegowe



class TestXMLParserEdgeCases:
    """Nietypowe, ale poprawne lub obsługiwane sytuacje."""

    def test_empty_document(self) -> None:
        with pytest.raises(XMLParsingError, match=_PL_BAD_XML):
            parse_xml("")

    def test_unicode_in_attr(self) -> None:
        xml = '<root><item txt="✓"/></root>'
        assert parse_xml(xml).find("item").attrib["txt"] == "✓"

    def test_bool_case_insensitive(self) -> None:
        xml = '<root><item flag="TrUe"/></root>'
        parse_xml(xml, attr_types={"item@flag": bool})

    def test_large_document(self) -> None:
        children = "".join(f'<c id="{i}"/>' for i in range(1000))
        root = parse_xml(f"<root>{children}</root>")
        assert len(root.findall("c")) == 1000

    def test_unicode_decode_error_propagation(self) -> None:
        class BadFile:
            def read(self, *_):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "meh")

        with pytest.raises(UnicodeDecodeError):
            parse_xml(BadFile())



# Dodatkowe testy



class TestXMLParserExtra:
    """Edge-case’y dotyczące typów, unikalności i wymagań."""

    def test_required_attrs_tag_absent_passes(self) -> None:
        parse_xml("<root/>", required_attrs={"item": ["id"]})

    def test_attr_type_float_ok(self) -> None:
        xml = '<root><val num="3.1415"/></root>'
        parse_xml(xml, attr_types={"val@num": float})

    def test_attr_type_float_fail(self) -> None:
        xml = '<root><val num="pi"/></root>'
        with pytest.raises(XMLParsingError, match=_PL_WRONG_TYPE):
            parse_xml(xml, attr_types={"val@num": float})

    def test_attr_type_iso_date_ok(self) -> None:
        xml = '<root><ev date="2025-05-17"/></root>'
        parse_xml(xml, attr_types={"ev@date": "iso"})

    def test_attr_type_iso_date_bad(self) -> None:
        xml = '<root><ev date="2025-13-01"/></root>'
        with pytest.raises(XMLParsingError, match=_PL_DATE_ERROR):
            parse_xml(xml, attr_types={"ev@date": "iso"})

    def test_attr_type_missing_attribute_is_ignored(self) -> None:
        xml = '<root><item id="1"/><item/></root>'
        parse_xml(xml, attr_types={"item@id": int})

    def test_multiple_attr_type_rules(self) -> None:
        xml = '<root><row n="7" ok="false"/></root>'
        parse_xml(xml, attr_types={"row@n": int, "row@ok": bool})

    def test_unique_tag_not_present(self) -> None:
        parse_xml("<root/>", unique_tags=["once"])

    def test_unique_tag_nested_violation(self) -> None:
        xml = "<root><a><u/></a><b><u/></b></root>"
        with pytest.raises(XMLParsingError, match=_PL_UNIQUE_TAG):
            parse_xml(xml, unique_tags=["u"])

    def test_multiple_missing_required_tags_reports_first(self) -> None:
        with pytest.raises(
            XMLParsingError,
            match=rf"{_PL_MISSING_TAG} <first>",
        ):
            parse_xml("<root/>", required_tags=["first", "second"])
