import pytest
import json
from src.ParserJson import parse_json, JSONParsingError

class TestJSONParserBasic:

    def test_parse_valid_empty_object(self):
        assert parse_json('{}') == {}

    def test_parse_valid_empty_array(self):
        assert parse_json('[]') == []

    def test_parse_simple_object(self):
        result = parse_json('{"name": "John"}')
        assert result["name"] == "John"

    def test_parse_nested_object(self):
        data = '{"user": {"name": "Alice", "age": 30}}'
        result = parse_json(data)
        assert "user" in result and result["user"]["name"] == "Alice"

    def test_parse_array_of_objects(self):
        data = '[{"id": 1}, {"id": 2}]'
        result = parse_json(data)
        assert len(result) == 2 and result[0]["id"] == 1

    def test_parse_various_data_types(self):
        data = '{"str": "text", "num": 123, "float": 1.5, "bool": true, "null_val": null}'
        result = parse_json(data)
        assert result["str"] == "text"
        assert result["num"] == 123
        assert result["float"] == 1.5
        assert result["bool"] is True
        assert result["null_val"] is None

    def test_parse_with_unicode(self):
        data = '{"emoji": "😊"}'
        result = parse_json(data)
        assert result["emoji"] == "😊"

    def test_parse_exponential_number(self):
        data = '{"big_number": 1e5}'
        result = parse_json(data)
        assert result["big_number"] == 100000.0

    def test_parse_large_array(self):
        array = list(range(1000))
        data = json.dumps(array)
        result = parse_json(data)
        assert len(result) == 1000 and result[500] == 500

    def test_json_with_whitespace(self):
        data = '''
        {
            "name": "Alice",
            "active": true
        }
        '''
        result = parse_json(data)
        assert result["name"] == "Alice" and result["active"] is True


class TestJSONParserValidations:

    def test_missing_required_keys_raises(self):
        data = '{"name": "John"}'
        with pytest.raises(JSONParsingError, match="Missing required keys: age"):
            parse_json(data, required_keys=["name", "age"])

    def test_all_required_keys_present(self):
        data = '{"name": "John", "age": 25}'
        result = parse_json(data, required_keys=["name", "age"])
        assert result["name"] == "John"

    def test_type_validation_success(self):
        data = '{"age": 30}'
        result = parse_json(data, key_types={"age": int})
        assert result["age"] == 30

    def test_type_validation_failure(self):
        data = '{"age": "not_a_number"}'
        with pytest.raises(JSONParsingError, match="should be of type int"):
            parse_json(data, key_types={"age": int})

    def test_type_validation_boolean(self):
        data = '{"active": true}'
        result = parse_json(data, key_types={"active": bool})
        assert result["active"] is True

    def test_type_validation_missing_key(self):
        data = '{"name": "John"}'
        # Should not raise error if the key is missing and validation does not require it to be present
        result = parse_json(data, key_types={"age": int})
        assert "age" not in result


class TestJSONParserInvalidInputs:

    @pytest.mark.parametrize("bad_json", [
        'Just random text',
        '{"key": "value"',  # Unclosed JSON
        "{'key': 'value'}",  # Wrong quotes
        '{"key": "value",}',  # Trailing comma
        '{"key" "value"}',  # Missing colon
        '{key: "value"}',  # Key without quotes
        '[1, 2, 3,]',  # Trailing comma in array
        '{"text": "line\\x"}',  # Invalid escape
        '',  # Empty string
        None  # None instead of string
    ])
    def test_invalid_json_formats(self, bad_json):
        with pytest.raises(JSONParsingError):
            parse_json(bad_json)

    def test_parse_boolean_literals(self):
        assert parse_json('true') is True
        assert parse_json('false') is False

    def test_parse_null_literal(self):
        assert parse_json('null') is None

    def test_parse_number_zero(self):
        assert parse_json('0') == 0

    def test_parse_empty_string(self):
        assert parse_json('""') == ""

    def test_parse_unicode_escape(self):
        data = '{"symbol": "\\u2764"}'  # Heart symbol ❤
        result = parse_json(data)
        assert result["symbol"] == "❤"

    def test_unexpected_type_in_list(self):
        data = '[1, "text", true, null]'
        result = parse_json(data)
        assert result == [1, "text", True, None]

    def test_parse_complex_object_with_extra_fields(self):
        data = '{"expected": 1, "unexpected": "surprise"}'
        result = parse_json(data)
        assert "unexpected" in result


@pytest.mark.parametrize("literal, expected", [
    ('true', True),
    ('false', False),
    ('null', None),
    ('123', 123),
    ('"text"', "text"),
    ('[1, 2, 3]', [1, 2, 3]),
    ('{"key": "value"}', {"key": "value"})
])
def test_direct_literal_parsing(literal, expected):
    assert parse_json(literal) == expected
