import pytest
import json

from src.ParserJson import parse_json, JSONParsingError  # Załóżmy, że masz takie elementy


class TestJSONParserValidData:

    def test_parse_empty_object(self):
        data = "{}"
        result = parse_json(data)
        assert isinstance(result, dict)
        assert result == {}

    def test_parse_empty_array(self):
        data = "[]"
        result = parse_json(data)
        assert isinstance(result, list)
        assert result == []

    def test_parse_nested_objects(self):
        data = '{"person": {"name": "Alice", "age": 30}}'
        result = parse_json(data)
        assert "person" in result
        assert result["person"]["name"] == "Alice"

    def test_parse_array_of_objects(self):
        data = '[{"id": 1}, {"id": 2}]'
        result = parse_json(data)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == 1

    @pytest.mark.parametrize("input_json, expected_type", [
        ('{"string": "text"}', str),
        ('{"int": 123}', int),
        ('{"float": 12.34}', float),
        ('{"bool": true}', bool),
        ('{"null": null}', type(None)),
    ])
    def test_various_data_types(self, input_json, expected_type):
        result = parse_json(input_json)
        key = list(result.keys())[0]
        assert isinstance(result[key], expected_type)

    def test_unicode_characters(self):
        data = '{"text": "Hello 🌍"}'
        result = parse_json(data)
        assert result["text"] == "Hello 🌍"

    def test_exponential_numbers(self):
        data = '{"number": 1.23e4}'
        result = parse_json(data)
        assert isinstance(result["number"], float)
        assert result["number"] == 12300.0

    def test_large_array(self):
        array = list(range(1000))
        data = json.dumps(array)
        result = parse_json(data)
        assert isinstance(result, list)
        assert len(result) == 1000
        assert result[500] == 500

    def test_json_with_whitespace_and_newlines(self):
        data = '''
        {
            "name": "Alice",
            "age": 30,
            "active": true
        }
        '''
        result = parse_json(data)
        assert result["name"] == "Alice"
        assert result["age"] == 30
        assert result["active"] is True

    @pytest.mark.parametrize("data, expected", [
        ('{"field": ""}', ""),
        ('{"field": null}', None),
    ])
    def test_empty_and_null_fields(self, data, expected):
        result = parse_json(data)
        assert result["field"] == expected


@pytest.mark.parametrize("bad_json", [
    'just some text',          # brak nawiasów {}
    '{"key": "value"',         # niedomknięty nawias {
    "{'key': 'value'}",        # pojedyncze cudzysłowy zamiast podwójnych
    '{"key": "value",}',       # przecinek na końcu listy
    '{"key" "value"}',         # brak dwukropka
    '{key: "value"}',          # klucz bez cudzysłowów
    '[1, 2, 3,]',              # przecinek na końcu tablicy
    '{"text": "line1\\x"}',    # nieprawidłowy escape sequence
    '',                        # puste wejście
])
def test_invalid_json_formats(bad_json):
    with pytest.raises(JSONParsingError):
        parse_json(bad_json)

class TestJSONParserAdditionalCases:

    def test_parse_boolean_true_false(self):
        data = '{"is_active": true, "is_deleted": false}'
        result = parse_json(data)
        assert result["is_active"] is True
        assert result["is_deleted"] is False

    def test_parse_empty_nested_array(self):
        data = '{"items": []}'
        result = parse_json(data)
        assert isinstance(result["items"], list)
        assert len(result["items"]) == 0

    def test_parse_empty_nested_object(self):
        data = '{"config": {}}'
        result = parse_json(data)
        assert isinstance(result["config"], dict)
        assert result["config"] == {}

    def test_parse_number_as_string(self):
        data = '{"number_str": "12345"}'
        result = parse_json(data)
        assert isinstance(result["number_str"], str)
        assert result["number_str"] == "12345"

    def test_parse_mixed_array(self):
        data = '[123, "abc", true, null, {"key": "value"}, [1,2,3]]'
        result = parse_json(data)
        assert isinstance(result, list)
        assert result[0] == 123
        assert result[1] == "abc"
        assert result[2] is True
        assert result[3] is None
        assert isinstance(result[4], dict)
        assert isinstance(result[5], list)

    def test_parse_large_number(self):
        data = '{"big_number": 12345678901234567890}'
        result = parse_json(data)
        assert result["big_number"] == 12345678901234567890

    def test_parse_string_with_escaped_characters(self):
        data = '{"text": "Line1\\nLine2\\tTabbed"}'  # podwójne escape!
        result = parse_json(data)
        assert result["text"] == "Line1\nLine2\tTabbed"

    def test_parse_boolean_as_string_should_not_parse(self):
        data = '{"flag": "true"}'
        result = parse_json(data)
        assert isinstance(result["flag"], str)
        assert result["flag"] == "true"

    def test_parse_null_in_array(self):
        data = '[null, null, null]'
        result = parse_json(data)
        assert all(x is None for x in result)

    def test_invalid_json_extra_closing_brace(self):
        bad_json = '{"key": "value"}}'
        with pytest.raises(JSONParsingError):
            parse_json(bad_json)

class TestJSONParserExtraCases:

    def test_parse_empty_string(self):
        data = '""'
        result = parse_json(data)
        assert result == ""

    def test_parse_number_zero(self):
        data = '0'
        result = parse_json(data)
        assert result == 0

    def test_parse_true_literal(self):
        data = 'true'
        result = parse_json(data)
        assert result is True

    def test_parse_false_literal(self):
        data = 'false'
        result = parse_json(data)
        assert result is False

    def test_parse_null_literal(self):
        data = 'null'
        result = parse_json(data)
        assert result is None

    def test_parse_array_of_booleans(self):
        data = '[true, false, true]'
        result = parse_json(data)
        assert result == [True, False, True]

    def test_parse_object_with_numeric_string_keys(self):
        data = '{"1": "one", "2": "two"}'
        result = parse_json(data)
        assert result["1"] == "one"
        assert result["2"] == "two"

    def test_parse_nested_empty_structures(self):
        data = '{"empty_list": [], "empty_dict": {}}'
        result = parse_json(data)
        assert isinstance(result["empty_list"], list)
        assert isinstance(result["empty_dict"], dict)

    def test_parse_string_with_unicode_escape(self):
        data = '{"char": "\\u2764"}'  # Unicode heart symbol ❤
        result = parse_json(data)
        assert result["char"] == "❤"

    def test_parse_object_with_additional_unexpected_fields(self):
        data = '{"expected": 1, "unexpected": "field"}'
        result = parse_json(data)
        assert result["expected"] == 1
        assert result["unexpected"] == "field"