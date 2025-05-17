"""
Testy jednostkowe parsera JSON.

Cel:
* sprawdzić poprawne parsowanie różnych struktur,
* zweryfikować obsługę wymaganych kluczy i typów,
* upewnić się, że niepoprawne dane skutkują podniesieniem JSONParsingError
  z polskim komunikatem.
"""
import io                   # ← konieczny do StringIO
import json
import pytest
from src.ParserJson import ( # ← muszą być obie funkcje + klasa błędu
    parse_json,
    parse_json_file,
    JSONParsingError,
)
# ---------------------------------------------------------------------------
# Pomocnicze stałe – łatwiej zmienić wzorzec w jednym miejscu niż w wielu testach
# ---------------------------------------------------------------------------

_PL_MISSING_KEYS = "Brakujące klucze"
_PL_WRONG_TYPE   = "powinien być typu"
_PL_INVALID_JSON = "Nieprawidłowy JSON"

# ---------------------------------------------------------------------------
# Testy poprawnych scenariuszy
# ---------------------------------------------------------------------------

class TestPoprawneParsowanie:
    """Scenariusze, w których parse_json zwraca oczekiwany wynik."""

    def test_pusty_obiekt(self):
        assert parse_json("{}") == {}

    def test_pusta_lista(self):
        assert parse_json("[]") == []

    def test_prosty_slownik(self):
        res = parse_json('{"name": "Jan"}')
        assert res["name"] == "Jan"

    def test_zagniezdzony_slownik(self):
        data = '{"user": {"name": "Ala", "age": 30}}'
        res = parse_json(data)
        assert res["user"]["name"] == "Ala"

    def test_lista_slownikow(self):
        data = '[{"id": 1}, {"id": 2}]'
        res = parse_json(data)
        assert len(res) == 2 and res[0]["id"] == 1

    def test_rozne_typy(self):
        data = '{"str": "txt", "num": 7, "float": 3.14, "bool": true, "null": null}'
        res = parse_json(data)
        assert res == {"str": "txt", "num": 7, "float": 3.14, "bool": True, "null": None}

    def test_unicode(self):
        assert parse_json('{"emoji": "😊"}')["emoji"] == "😊"

    def test_notacja_naukowa(self):
        assert parse_json('{"big": 1e3}')["big"] == 1000.0

    def test_duza_lista(self):
        arr = list(range(500))
        assert parse_json(json.dumps(arr))[123] == 123

    def test_biale_znaki_w_jsonie(self):
        pretty = """
        {
            "active": true,
            "name": "Ala"
        }
        """
        res = parse_json(pretty)
        assert res["active"] is True and res["name"] == "Ala"


# ---------------------------------------------------------------------------
# Walidacja wymaganych kluczy / typów
# ---------------------------------------------------------------------------

class TestWalidacja:

    def test_brak_wymaganego_klucza(self):
        with pytest.raises(JSONParsingError, match=rf"{_PL_MISSING_KEYS}: age"):
            parse_json('{"name": "Jan"}', required_keys=["name", "age"])

    def test_wszystkie_wymagane_klucze(self):
        res = parse_json('{"name": "Jan", "age": 20}', required_keys=["name", "age"])
        assert res["age"] == 20

    def test_poprawny_typ(self):
        assert parse_json('{"age": 42}', key_types={"age": int})["age"] == 42

    def test_bledny_typ(self):
        pattern = rf"{_PL_WRONG_TYPE} int"
        with pytest.raises(JSONParsingError, match=pattern):
            parse_json('{"age": "wrong"}', key_types={"age": int})

    def test_typ_bool(self):
        assert parse_json('{"ok": true}', key_types={"ok": bool})["ok"] is True

    def test_brak_klucza_nie_wymaganego(self):
        res = parse_json('{"name": "Jan"}', key_types={"age": int})
        assert "age" not in res


# ---------------------------------------------------------------------------
# Scenariusze niepoprawnych danych wejściowych
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "zly_json",
    [
        "Losowy tekst",
        '{"key": "value"',            # brak nawiasu zamykającego
        "{'key': 'value'}",           # złe cudzysłowy
        '{"key": "value",}',          # przecinek na końcu
        '{"key" "value"}',            # brak dwukropka
        '{key: "value"}',             # brak cudzysłowów przy kluczu
        '[1, 2, 3,]',                 # przecinek w tablicy
        '{"text": "line\\x"}',        # zła sekwencja escape
        "",                           # pusty string
        None                          # brak stringa
    ]
)
def test_nieprawidlowy_format_json(zly_json):
    with pytest.raises(JSONParsingError, match=_PL_INVALID_JSON):
        parse_json(zly_json)


# ---------------------------------------------------------------------------
# Parsowanie pojedynczych literałów JSON (true/false/null/liczba/itd.)
# ---------------------------------------------------------------------------

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
    ]
)
def test_parsowanie_literalu(literal, expected):
    assert parse_json(literal) == expected







class TestParseJsonFileOK:
    """Poprawne wczytywanie danych z różnych „plików”."""

    def test_simple_object(self):
        buf = io.StringIO('{"name": "Ala"}')
        res = parse_json_file(buf)
        assert res == {"name": "Ala"}

    def test_with_required_keys(self):
        buf = io.StringIO('{"id": 1, "val": 42}')
        res = parse_json_file(buf, required_keys=["id", "val"])
        assert res["val"] == 42

    def test_type_validation(self, tmp_path):
        """Wersja z realnym plikiem na dysku."""
        p = tmp_path / "obj.json"
        p.write_text('{"active": true, "age": 21}', encoding="utf-8")

        res_plain = parse_json_file(p.open())
        res_valid = parse_json_file(
            p.open(),
            key_types={"active": bool, "age": int},
        )
        assert res_plain == res_valid


# ---------------------------------------------------------------------------
# Scenariusze negatywne
# ---------------------------------------------------------------------------

class TestParseJsonFileErrors:
    """Błędy przy wczytywaniu / walidacji."""

    @pytest.mark.parametrize(
        "bad_json",
        [
            '{"key": "value"',            # brak nawiasu
            "{'key': 'value'}",           # złe cudzysłowy
        ],
    )
    def test_invalid_json(self, bad_json):
        with pytest.raises(JSONParsingError):
            parse_json_file(io.StringIO(bad_json))

    def test_missing_required_key(self):
        with pytest.raises(JSONParsingError, match="Brakujące klucze: age"):
            parse_json_file(
                io.StringIO('{"name": "Jan"}'),
                required_keys=["name", "age"],
            )

    def test_wrong_type(self):
        with pytest.raises(JSONParsingError, match="powinien być typu int"):
            parse_json_file(
                io.StringIO('{"age": "not_int"}'),
                key_types={"age": int},
            )

    def test_unicode_decode_error(self):
        """Symulujemy plik, który rzuca UnicodeDecodeError przy read()."""

        class BadFile:
            def read(self, *a, **kw):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "boom")

        with pytest.raises(JSONParsingError, match="Nie udało się odczytać pliku"):
            parse_json_file(BadFile())