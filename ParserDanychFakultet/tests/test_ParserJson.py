import io
import json

import pytest

from src.ParserJson import JSONParsingError, parse_json, parse_json_file


# Stałe z fragmentami komunikatów


_PL_MISSING_KEYS = "Brakujące klucze"
_PL_WRONG_TYPE = "powinien być typu"
_PL_INVALID_JSON = "Nieprawidłowy JSON"


# Poprawne scenariusze parsowania



class TestPoprawneParsowanie:
    """Przypadki, w których `parse_json` zwraca oczekiwany wynik."""

    def test_pusty_obiekt(self) -> None:
        assert parse_json("{}") == {}

    def test_pusta_lista(self) -> None:
        assert parse_json("[]") == []

    def test_prosty_slownik(self) -> None:
        result = parse_json('{"name": "Jan"}')
        assert result["name"] == "Jan"

    def test_zagniezdzony_slownik(self) -> None:
        data = '{"user": {"name": "Ala", "age": 30}}'
        result = parse_json(data)
        assert result["user"]["name"] == "Ala"

    def test_lista_slownikow(self) -> None:
        data = '[{"id": 1}, {"id": 2}]'
        result = parse_json(data)
        assert len(result) == 2 and result[0]["id"] == 1

    def test_rozne_typy(self) -> None:
        data = (
            '{"str":"txt","num":7,"float":3.14,'
            '"bool":true,"null":null}'
        )
        expected = {
            "str": "txt",
            "num": 7,
            "float": 3.14,
            "bool": True,
            "null": None,
        }
        assert parse_json(data) == expected

    def test_unicode(self) -> None:
        assert parse_json('{"emoji": "😊"}')["emoji"] == "😊"

    def test_notacja_naukowa(self) -> None:
        assert parse_json('{"big": 1e3}')["big"] == 1000.0

    def test_duza_lista(self) -> None:
        arr = list(range(500))
        assert parse_json(json.dumps(arr))[123] == 123

    def test_biale_znaki_w_jsonie(self) -> None:
        pretty = """
        {
            "active": true,
            "name": "Ala"
        }
        """
        result = parse_json(pretty)
        assert result["active"] is True and result["name"] == "Ala"



# Walidacja wymaganych kluczy i typów



class TestWalidacja:
    """Testy walidacji kluczy oraz typów wartości."""

    def test_brak_wymaganego_klucza(self) -> None:
        with pytest.raises(
            JSONParsingError,
            match=rf"{_PL_MISSING_KEYS}: age",
        ):
            parse_json('{"name": "Jan"}', required_keys=["name", "age"])

    def test_wszystkie_wymagane_klucze(self) -> None:
        result = parse_json(
            '{"name": "Jan", "age": 20}',
            required_keys=["name", "age"],
        )
        assert result["age"] == 20

    def test_poprawny_typ(self) -> None:
        assert parse_json('{"age": 42}', key_types={"age": int})["age"] == 42

    def test_bledny_typ(self) -> None:
        pattern = rf"{_PL_WRONG_TYPE} int"
        with pytest.raises(JSONParsingError, match=pattern):
            parse_json('{"age": "wrong"}', key_types={"age": int})

    def test_typ_bool(self) -> None:
        assert parse_json('{"ok": true}', key_types={"ok": bool})["ok"] is True

    def test_brak_klucza_nie_wymaganego(self) -> None:
        result = parse_json('{"name": "Jan"}', key_types={"age": int})
        assert "age" not in result



# Niepoprawne dane wejściowe



@pytest.mark.parametrize(
    "bad_json",
    [
        "Losowy tekst",
        '{"key": "value"',          # brak nawiasu
        "{'key': 'value'}",         # złe cudzysłowy
        '{"key": "value",}',        # przecinek na końcu
        '{"key" "value"}',          # brak dwukropka
        '{key: "value"}',           # brak cudzysłowów
        "[1, 2, 3,]",               # przecinek w tablicy
        '{"text": "line\\x"}',      # zła sekwencja escape
        "",
        None,
    ],
)
def test_nieprawidlowy_format_json(bad_json) -> None:
    with pytest.raises(JSONParsingError, match=_PL_INVALID_JSON):
        parse_json(bad_json)



# Parsowanie pojedynczych literałów



@pytest.mark.parametrize(
    "literal, expected",
    [
        ("true", True),
        ("false", False),
        ("null", None),
        ("123", 123),
        ('"tekst"', "tekst"),
        ("[1, 2, 3]", [1, 2, 3]),
        ('{"k": "v"}', {"k": "v"}),
    ],
)
def test_parsowanie_literalu(literal: str, expected) -> None:
    assert parse_json(literal) == expected



# Testy dla parse_json_file – przypadki poprawne



class TestParseJsonFileOK:
    """Poprawne wczytywanie danych z obiektów plikowych."""

    def test_simple_object(self) -> None:
        buf = io.StringIO('{"name": "Ala"}')
        assert parse_json_file(buf) == {"name": "Ala"}

    def test_with_required_keys(self) -> None:
        buf = io.StringIO('{"id": 1, "val": 42}')
        result = parse_json_file(buf, required_keys=["id", "val"])
        assert result["val"] == 42

    def test_type_validation(self, tmp_path) -> None:
        path = tmp_path / "obj.json"
        path.write_text('{"active": true, "age": 21}', encoding="utf-8")

        plain = parse_json_file(path.open())
        validated = parse_json_file(
            path.open(),
            key_types={"active": bool, "age": int},
        )
        assert plain == validated



# Testy dla parse_json_file – przypadki błędne



class TestParseJsonFileErrors:
    """Błędy przy wczytywaniu i walidacji plików JSON."""

    @pytest.mark.parametrize(
        "bad_json",
        [
            '{"key": "value"',          # brak nawiasu
            "{'key': 'value'}",         # złe cudzysłowy
        ],
    )
    def test_invalid_json(self, bad_json: str) -> None:
        with pytest.raises(JSONParsingError):
            parse_json_file(io.StringIO(bad_json))

    def test_missing_required_key(self) -> None:
        with pytest.raises(
            JSONParsingError,
            match=r"Brakujące klucze: age",
        ):
            parse_json_file(
                io.StringIO('{"name": "Jan"}'),
                required_keys=["name", "age"],
            )

    def test_wrong_type(self) -> None:
        with pytest.raises(
            JSONParsingError,
            match=r"powinien być typu int",
        ):
            parse_json_file(
                io.StringIO('{"age": "not_int"}'),
                key_types={"age": int},
            )

    def test_unicode_decode_error(self) -> None:
        """Symuluje plik, który rzuca UnicodeDecodeError przy read()."""

        class BadFile:
            def read(self, *_, **__):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "boom")

        with pytest.raises(
            JSONParsingError,
            match=r"Nie udało się odczytać pliku",
        ):
            parse_json_file(BadFile())
