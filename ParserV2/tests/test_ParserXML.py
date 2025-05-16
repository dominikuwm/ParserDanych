import pytest
import re
from src.ParserXML import parse_xml, XMLParsingError

class TestXMLParserBasic:

    def test_parse_simple_element(self):
        xml = "<root></root>"
        root = parse_xml(xml)
        assert root.tag == "root"

    def test_parse_nested_elements(self):
        xml = "<root><child></child></root>"
        root = parse_xml(xml)
        assert root.find("child") is not None

    def test_parse_element_with_attributes(self):
        xml = '<root attr="value"></root>'
        root = parse_xml(xml)
        assert root.attrib["attr"] == "value"

    def test_parse_with_required_tags_success(self):
        xml = "<root><required></required></root>"
        parse_xml(xml, required_tags=["required"])

    def test_parse_with_missing_required_tag(self):
        xml = "<root></root>"
        with pytest.raises(XMLParsingError, match="Missing required tags: required"):
            parse_xml(xml, required_tags=["required"])

class TestXMLParserAttributes:

    def test_parse_required_attributes_success(self):
        xml = '<root><item id="1"/></root>'
        parse_xml(xml, required_attributes={"item": ["id"]})

    def test_missing_required_attribute(self):
        xml = '<root><item/></root>'
        with pytest.raises(XMLParsingError, match="Element <item> is missing required attributes: id"):
            parse_xml(xml, required_attributes={"item": ["id"]})

    def test_attribute_type_validation_success(self):
        xml = '<root><item id="10"/></root>'
        parse_xml(xml, attribute_types={"item@id": int})

    def test_attribute_type_validation_failure(self):
        xml = '<root><item id="abc"/></root>'
        with pytest.raises(XMLParsingError, match="Attribute 'id' in <item> should be of type"):
            parse_xml(xml, attribute_types={"item@id": int})

    def test_attribute_boolean_validation_success(self):
        xml = '<root><item flag="true"/></root>'
        parse_xml(xml, attribute_types={"item@flag": bool})

    def test_attribute_boolean_validation_failure(self):
        xml = '<root><item flag="notboolean"/></root>'
        with pytest.raises(XMLParsingError, match="Invalid boolean string: notboolean"):
            parse_xml(xml, attribute_types={"item@flag": bool})

class TestXMLParserUniqueness:

    def test_unique_elements_success(self):
        xml = '<root><unique/></root>'
        parse_xml(xml, unique_elements=["unique"])

    def test_unique_elements_failure(self):
        xml = '<root><unique/><unique/></root>'
        with pytest.raises(XMLParsingError, match="Element 'unique' should be unique"):
            parse_xml(xml, unique_elements=["unique"])

class TestXMLParserErrors:

    @pytest.mark.parametrize("bad_xml", [
        "<root><unclosed></root>",
        "<root><1tag></1tag></root>",
        '<root id=1></root>',
        '<root id="1></root>',
        "<root>&invalid;</root>",
        "<a><b></a></b>",
    ])
    def test_invalid_xml_formats(self, bad_xml):
        with pytest.raises(XMLParsingError, match="Invalid XML format"):
            parse_xml(bad_xml)

    def test_unexpected_input_type(self):
        with pytest.raises(XMLParsingError, match="Input must be a string or file-like object"):
            parse_xml(12345)

    def test_invalid_attribute_type_format(self):
        xml = '<root><item/></root>'
        with pytest.raises(XMLParsingError, match="Invalid attribute_types key format"):
            parse_xml(xml, attribute_types={"invalid_format": int})

class TestXMLParserEdgeCases:

    def test_parse_empty_document(self):
        with pytest.raises(XMLParsingError, match="Invalid XML format"):
            parse_xml("")

    def test_parse_with_unicode(self):
        xml = '<root><item text="✓"/></root>'
        root = parse_xml(xml)
        item = root.find("item")
        assert item.attrib["text"] == "✓"

    def test_parse_boolean_values_case_insensitive(self):
        xml = '<root><item flag="TrUe"/></root>'
        parse_xml(xml, attribute_types={"item@flag": bool})

    def test_parse_large_document(self):
        children = "".join(f'<child id="{i}"/>' for i in range(1000))
        xml = f"<root>{children}</root>"
        root = parse_xml(xml)
        assert len(root.findall("child")) == 1000

    def test_unexpected_exception_handling(self):
        class FakeFile:
            def read(self, *args, **kwargs):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "reason")

        with pytest.raises(XMLParsingError, match="Unable to decode XML"):
            parse_xml(FakeFile())
