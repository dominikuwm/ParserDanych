import pytest
from io import BytesIO
from src.ParserXML import parse_xml, XMLParsingError

class TestXMLParserBasicSyntax:

    def test_parse_empty_document_raises(self):
        # Pusty string powinien rzucić błąd
        with pytest.raises(XMLParsingError):
            parse_xml("")

        # Deklaracja XML bez treści też powinna rzucić błąd
        with pytest.raises(XMLParsingError):
            parse_xml('<?xml version="1.0"?>')

    def test_parse_simple_element_no_attributes(self):
        data = "<root></root>"
        root = parse_xml(data)
        assert root.tag == "root"
        assert len(root) == 0  # brak dzieci
        assert (root.text is None or root.text.strip() == "")

    def test_parse_simple_element_with_text(self):
        data = "<root>Hello</root>"
        root = parse_xml(data)
        assert root.tag == "root"
        assert root.text == "Hello"

    def test_parse_element_with_attributes(self):
        data = '<root id="1" name="test"></root>'
        root = parse_xml(data)
        assert root.tag == "root"
        assert root.attrib["id"] == "1"
        assert root.attrib["name"] == "test"

    def test_parse_nested_elements(self):
        data = "<root><child>Text</child></root>"
        root = parse_xml(data)
        assert root.tag == "root"
        assert len(root) == 1
        child = root[0]
        assert child.tag == "child"
        assert child.text == "Text"

    def test_parse_sibling_elements(self):
        data = "<root><a/><b/><c/></root>"
        root = parse_xml(data)
        assert root.tag == "root"
        assert len(root) == 3
        tags = [child.tag for child in root]
        assert tags == ["a", "b", "c"]

    def test_parse_element_with_empty_text(self):
        data = "<root></root>"
        root = parse_xml(data)
        assert root.text is None or root.text.strip() == ""

    def test_parse_element_with_whitespace_and_newlines(self):
        data = """
        <root>
            <child>
                Text with
                newlines and spaces
            </child>
        </root>
        """
        root = parse_xml(data)
        assert root.tag == "root"
        child = root.find("child")
        assert child is not None
        assert child.text is not None
        # Test ignoruje białe znaki na początku i końcu
        assert child.text.strip().startswith("Text with")
        assert "newlines" in child.text

class TestXMLParserSyntaxErrors:

    def test_unclosed_tag(self):
        data = "<root><child></root>"  # child niezamknięty
        with pytest.raises(XMLParsingError):
            parse_xml(data)

    def test_invalid_tag_name(self):
        data = "<1invalid>text</1invalid>"  # nazwa tagu nie może zaczynać się od cyfry
        with pytest.raises(XMLParsingError):
            parse_xml(data)

    def test_missing_quotes_in_attribute(self):
        data = "<root id=1></root>"  # brak cudzysłowów w atrybucie
        with pytest.raises(XMLParsingError):
            parse_xml(data)

    def test_unclosed_attribute_value(self):
        data = '<root id="1></root>'  # niezamknięty cudzysłów w atrybucie
        with pytest.raises(XMLParsingError):
            parse_xml(data)

    def test_invalid_special_character_usage(self):
        data = "<root>&invalid;</root>"  # niepoprawna encja XML
        with pytest.raises(XMLParsingError):
            parse_xml(data)

    def test_crossed_tags(self):
        data = "<a><b></a></b>"  # tagi się krzyżują
        with pytest.raises(XMLParsingError):
            parse_xml(data)

class TestXMLParserAttributes:

    def test_attributes_with_various_value_types(self):
        data = '<root num="123" text="hello" empty="" special="!@#$%^&amp;*()"></root>'
        root = parse_xml(data)
        assert root.attrib["num"] == "123"
        assert root.attrib["text"] == "hello"
        assert root.attrib["empty"] == ""
        assert root.attrib["special"] == "!@#$%^&*()"

    def test_attributes_with_xml_entities(self):
        data = '<root amp="&amp;" lt="&lt;" gt="&gt;"></root>'
        root = parse_xml(data)
        assert root.attrib["amp"] == "&"
        assert root.attrib["lt"] == "<"
        assert root.attrib["gt"] == ">"

    def test_multiple_attributes_in_element(self):
        # XML standard does NOT allow duplicate attribute names in the same element,
        # so we expect a parse error if that occurs.
        data = '<root attr="1" attr="2"></root>'
        with pytest.raises(XMLParsingError):
            parse_xml(data)

    def test_attributes_with_quotes_in_value(self):
        data = '<root quote="He said &quot;Hello&quot;"></root>'
        root = parse_xml(data)
        assert root.attrib["quote"] == 'He said "Hello"'

    def test_element_with_no_attributes(self):
        data = "<root></root>"
        root = parse_xml(data)
        assert root.attrib == {}

class TestXMLParserComplexStructures:

    def test_deeply_nested_elements(self):
        # 50 poziomów zagnieżdżenia
        depth = 50
        xml = "<root>"
        for i in range(depth):
            xml += f"<level{i}>"
        for i in reversed(range(depth)):
            xml += f"</level{i}>"
        xml += "</root>"

        root = parse_xml(xml)
        current = root
        for i in range(depth):
            assert len(current) == 1
            current = current[0]
            assert current.tag == f"level{i}"

    def test_many_sibling_elements(self):
        # 1000 rodzeństwa pod rootem
        xml = "<root>"
        for i in range(1000):
            xml += f"<item id='{i}'/>"
        xml += "</root>"

        root = parse_xml(xml)
        assert len(root) == 1000
        for i, child in enumerate(root):
            assert child.tag == "item"
            assert child.attrib["id"] == str(i)

    def test_mixed_nesting_and_text(self):
        xml = """
        <root>
            Some text
            <child>Child text</child>
            More text
        </root>
        """
        root = parse_xml(xml)
        assert root.tag == "root"
        # Tekst bezpośrednio w root (strip, bo może być whitespace)
        assert "Some text" in (root.text or "").strip()
        # Dziecko
        child = root.find("child")
        assert child is not None
        assert child.text == "Child text"
        # Tekst po dziecku (tail)
        assert "More text" in (child.tail or "").strip()

    def test_element_with_mixed_content(self):
        # Element z tekstem i podelementami mieszanymi
        xml = "<root>Start<child1>Text1</child1>Middle<child2>Text2</child2>End</root>"
        root = parse_xml(xml)
        assert root.text == "Start"
        child1 = root.find("child1")
        assert child1 is not None
        assert child1.text == "Text1"
        assert child1.tail == "Middle"
        child2 = root.find("child2")
        assert child2 is not None
        assert child2.text == "Text2"
        assert child2.tail == "End"

    def test_elements_with_comments(self):
        xml = "<root><!-- This is a comment --><child>Text</child><!-- Another comment --></root>"
        root = parse_xml(xml)
        # Komentarze nie są zwracane jako elementy, więc ich nie ma w root
        assert root.tag == "root"
        child = root.find("child")
        assert child is not None
        assert child.text == "Text"

    def test_elements_with_processing_instructions(self):
        xml = """<?xml version="1.0"?>
        <?processing instruction?>
        <root>
            <child>Text</child>
        </root>"""
        root = parse_xml(xml)
        assert root.tag == "root"
        child = root.find("child")
        assert child is not None
        assert child.text == "Text"

class TestXMLParserSpecialDataTypes:

    def test_parse_integer_values(self):
        xml = '<root int_attr="42">123</root>'
        root = parse_xml(xml)
        # Atrybut jako string, możemy sprawdzić czy jest cyfrą
        assert root.attrib["int_attr"].isdigit()
        # Tekst w elemencie jako liczba całkowita (jako string)
        assert root.text.isdigit()

    def test_parse_float_values(self):
        xml = '<root float_attr="3.1415">2.71828</root>'
        root = parse_xml(xml)
        # Sprawdzenie czy wartości mogą być konwertowane na float
        assert abs(float(root.attrib["float_attr"]) - 3.1415) < 1e-6
        assert abs(float(root.text) - 2.71828) < 1e-6

    def test_parse_iso8601_date_in_attribute(self):
        xml = '<root date_attr="2023-05-15T13:45:30Z"></root>'
        root = parse_xml(xml)
        date_str = root.attrib["date_attr"]
        # Prosta weryfikacja formatu (można użyć regex lub dateutil parser)
        assert "T" in date_str and "Z" in date_str

    def test_parse_boolean_as_text(self):
        xml_true = '<root flag="true"></root>'
        root_true = parse_xml(xml_true)
        assert root_true.attrib["flag"].lower() in ("true", "false")

        xml_false = '<root flag="false"></root>'
        root_false = parse_xml(xml_false)
        assert root_false.attrib["flag"].lower() in ("true", "false")

    def test_parse_null_equivalents(self):
        xml_empty_tag = '<root><empty/></root>'
        root_empty = parse_xml(xml_empty_tag)
        empty_elem = root_empty.find("empty")
        # Element pusty, tekst powinien być None lub pusty string
        assert empty_elem is not None
        assert empty_elem.text is None or empty_elem.text.strip() == ""

        xml_missing_tag = '<root></root>'
        root_missing = parse_xml(xml_missing_tag)
        # Sprawdzenie, że tag 'missing' nie istnieje
        assert root_missing.find("missing") is None

class TestXMLParserSyntaxVariants:

    def test_parse_with_xml_declaration(self):
        xml = '<?xml version="1.0" encoding="UTF-8"?><root><child>Text</child></root>'
        root = parse_xml(xml)
        assert root.tag == "root"
        child = root.find("child")
        assert child is not None
        assert child.text == "Text"

    def test_parse_without_xml_declaration(self):
        xml = '<root><child>Text</child></root>'
        root = parse_xml(xml)
        assert root.tag == "root"
        child = root.find("child")
        assert child is not None
        assert child.text == "Text"

    def test_parse_with_utf8_encoding(self):
        xml = '<?xml version="1.0" encoding="UTF-8"?><root>UTF-8 ✓</root>'
        data = xml.encode("utf-8")
        root = parse_xml(BytesIO(data))
        assert root.text == "UTF-8 ✓"

    def test_parse_with_utf16_encoding(self):
        xml = '<?xml version="1.0" encoding="UTF-16"?><root>UTF-16 ✓</root>'
        data = xml.encode("utf-16")
        root = parse_xml(BytesIO(data))
        assert root.text == "UTF-16 ✓"

    def test_parse_with_namespaces(self):
        xml = '''<?xml version="1.0"?>
        <root xmlns:h="http://www.w3.org/TR/html4/">
            <h:table>
                <h:tr>
                    <h:td>Apples</h:td>
                    <h:td>Bananas</h:td>
                </h:tr>
            </h:table>
        </root>'''
        root = parse_xml(xml)
        ns = {'h': 'http://www.w3.org/TR/html4/'}
        table = root.find('h:table', ns)
        assert table is not None
        td = table.find('h:tr/h:td', ns)
        assert td is not None
        assert td.text == "Apples"

    def test_parse_with_prefixes_and_namespaces(self):
        xml = '''<ns:root xmlns:ns="http://example.com/ns">
                    <ns:child>Content</ns:child>
                 </ns:root>'''
        root = parse_xml(xml)
        ns = {'ns': 'http://example.com/ns'}
        child = root.find('ns:child', ns)
        assert child is not None
        assert child.text == "Content"

    def test_parse_with_default_namespace(self):
        xml = '''<root xmlns="http://default.namespace/">
                    <child>Value</child>
                 </root>'''
        root = parse_xml(xml)
        # Domyślny namespace - wyszukiwanie wymaga namespace
        ns = {'d': 'http://default.namespace/'}
        child = root.find('d:child', ns)
        assert child is not None
        assert child.text == "Value"

class TestXMLParserLogicalErrors:

    def test_missing_required_root_element(self):
        data = '<notroot></notroot>'
        with pytest.raises(XMLParsingError, match="Missing required tags: root"):
            parse_xml(data, required_tags=["root"])

    def test_duplicate_elements_should_be_unique(self):
        data = '''
        <root>
            <unique>1</unique>
            <unique>2</unique>
        </root>
        '''
        with pytest.raises(XMLParsingError, match="should be unique"):
            parse_xml(data, unique_elements=["unique"])




