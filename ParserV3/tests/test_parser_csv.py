import pytest
import io
from src.ParserCSV import parse_csv, CSVParsingError, parse_csv_file
import time

# Testy dla poprawnych danych
class TestCSVParserValidData:

    @pytest.mark.parametrize("csv_content, separator", [
        ("id,name,age\n1,Alice,30\n2,Bob,25", ","),
        ("id|name|age\n1|Alice|30\n2|Bob|25", "|"),
        ("id;name;age\n1;Alice;30\n2;Bob;25", ";"),
        ("id\tname\tage\n1\tAlice\t30\n2\tBob\t25", "\t"),
        ("id#name#age\n1#Alice#30\n2#Bob#25", "#"),
        ("id~name~age\n1~Alice~30\n2~Bob~25", "~"),
    ])
    def test_various_separators(self, csv_content: str, separator: str):
        # Parametryzacja: różne separatory
        file_obj = io.StringIO(csv_content)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "name", "age"], separator=separator)
        assert len(wynik) == 2
        assert wynik[0]["name"] == "Alice"
        assert wynik[1]["age"] == "25"

    def test_large_file(self):
        # Duży plik: 1000 wierszy
        zawartosc = "\n".join(["id,name,age"] + [f"{i},User{i},{20+i}" for i in range(1000)])
        file_obj = io.StringIO(zawartosc)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "name", "age"])
        assert len(wynik) == 1000
        assert wynik[500]["name"] == "User500"

    def test_quoted_fields_with_commas(self):
        # Pole z cudzysłowami i przecinkami w środku
        csv = 'id,name,comment\n1,Alice,"Hello, World!"\n2,Bob,"Nice : )"'
        file_obj = io.StringIO(csv)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "name", "comment"])
        assert wynik[0]["comment"] == "Hello, World!"
        assert wynik[1]["comment"] == "Nice : )"

    def test_optional_empty_column(self):
        # Puste kolumny opcjonalne nie rzucają wyjątku
        csv = "id,name,email\n1,Alice,alice@example.com\n2,Bob,"
        file_obj = io.StringIO(csv)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "name"])
        assert wynik[1]["email"] == ""

    def test_types_as_strings(self):
        # Wszystkie wartości zwracane jako string
        csv = "id,name,is_active,age\n1,Alice,True,30\n2,Bob,False,25"
        file_obj = io.StringIO(csv)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "name", "is_active", "age"])
        assert isinstance(wynik[0]["is_active"], str)
        assert wynik[0]["is_active"] == "True"
        assert wynik[1]["age"] == "25"

    def test_unicode_and_emoji(self):
        # Emoji i Unicode w polach
        csv = 'id,name,emoji\n1,Alice,🌍\n2,Bob,✓'
        file_obj = io.StringIO(csv)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "name", "emoji"])
        assert wynik[0]["emoji"] == "🌍"
        assert wynik[1]["emoji"] == "✓"

    def test_very_long_field(self):
        # Bardzo długie pole (>1000 znaków)
        long_str = "x" * 1200
        csv = f"id,name,long\n1,Alice,{long_str}"
        file_obj = io.StringIO(csv)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "name", "long"])
        assert len(wynik[0]["long"]) == 1200

    def test_mixed_case_data(self):
        # Mieszane wielkości liter w danych nie wpływają na wartości
        csv = "id,Name,Age\n1,alice,30\n2,BOB,25"
        file_obj = io.StringIO(csv)
        wynik = parse_csv(file_obj, wymagane_pola=["id", "Name", "Age"])
        assert wynik[0]["Name"] == "alice"
        assert wynik[1]["Age"] == "25"


# Testy walidacji nagłówka
class TestCSVParserHeaderValidation:

    def test_no_header_raises(self):
        # Pierwszy wiersz zaczyna się od cyfry → błąd "Niewłaściwe nazwy kolumn"
        csv = "1,Alice,30\n2,Bob,25"
        with pytest.raises(CSVParsingError, match="Niewłaściwe nazwy kolumn"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"])

    def test_header_only_digits(self):
        # Nagłówki same cyfry → błąd o niepoprawnym nagłówku
        csv = "1,2,3\n1,Alice,30"
        with pytest.raises(CSVParsingError, match="tylko liczby"):
            parse_csv(io.StringIO(csv), wymagane_pola=["1", "2", "3"])

    def test_header_starts_with_digit(self):
        # Nagłówek zaczyna się od cyfry → błąd "Niewłaściwe nazwy kolumn"
        csv = "1col,name,age\n1,Alice,30"
        with pytest.raises(CSVParsingError, match="Nazwy nie mogą zaczynać się od cyfry"):
            parse_csv(io.StringIO(csv), wymagane_pola=["1col", "name", "age"])

    def test_header_contains_space(self):
        # Nagłówki zawierają spację → błąd
        csv = "id,first name,age\n1,Alice,30"
        with pytest.raises(CSVParsingError, match="zawierają spacje"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "first name", "age"])

    def test_header_with_duplicates(self):
        # Duplikaty nagłówków → błąd o powtórzonych nazwach
        csv = "id,name,name\n1,Alice,30"
        with pytest.raises(CSVParsingError, match="Powtórzone nazwy kolumn"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"])

    def test_missing_required_field(self):
        # Brakuje wymaganego pola → błąd "Brakujące pola w nagłówku"
        csv = "id,name\n1,Alice"
        with pytest.raises(CSVParsingError, match="Brakujące pola"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"])

    def test_header_with_special_chars(self):
        # Nagłówki z niedozwolonymi znakami są dozwolone → poprawne parsowanie
        csv = "id,na$me,age\n1,Alice,30"
        wynik = parse_csv(io.StringIO(csv), wymagane_pola=["id", "na$me", "age"])
        assert wynik[0]["na$me"] == "Alice"

    def test_case_sensitive_header(self):
        # Case-sensitive mismatch → brakujące pole
        csv = "ID,Name,Age\n1,Alice,30"
        with pytest.raises(CSVParsingError, match="Brakujące pola"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "Name", "Age"])

# --- Testy walidacji wierszy ---
class TestCSVParserRowValidation:

    def test_empty_line_in_middle(self):
        # Pusta linia w wierszu 3 powinna rzucić CSVParsingError z numerem wiersza
        csv = "id,name,age\n1,Alice,30\n\n2,Bob,25"
        with pytest.raises(CSVParsingError, match="wierszu 3"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"])

    def test_row_with_too_few_columns(self):
        # Za mało kolumn → brak wartości w polu 'age' w wierszu 2
        csv = "id,name,age\n1,Alice"
        with pytest.raises(CSVParsingError, match="Brak wartości w polach: age w wierszu 2"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"])

    def test_row_with_extra_columns(self):
        # Za dużo kolumn → Dodatkowe kolumny w wierszu 2
        csv = "id,name,age\n1,Alice,30,extra"
        with pytest.raises(CSVParsingError, match="Dodatkowe kolumny w wierszu 2"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"])

    def test_required_field_blank_or_spaces(self):
        # Pole 'name' zawiera same spacje → brak wartości w polu 'name'
        csv = "id,name,age\n1,   ,30"
        with pytest.raises(CSVParsingError, match="Brak wartości w polach: name w wierszu 2"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"])

    def test_separator_mismatch(self):
        # Niewłaściwy separator (używamy ';' zamiast ',') → brak wymaganych pól
        csv = "id,name,age\n1,Alice,30"
        with pytest.raises(CSVParsingError, match="Brakujące pola"):
            parse_csv(io.StringIO(csv), wymagane_pola=["id", "name", "age"], separator=";")

    def test_numeric_string_not_converted(self):
        # Nieparsowalna liczba zostaje stringiem
        csv = "id,age\n1,not_a_number"
        wynik = parse_csv(io.StringIO(csv), wymagane_pola=["id", "age"])
        assert isinstance(wynik[0]["age"], str)
        assert wynik[0]["age"] == "not_a_number"

    def test_boolean_1_0_as_string(self):
        # Boolean wyrażony jako 1/0 zostaje stringiem
        csv = "id,is_active\n1,1\n2,0"
        wynik = parse_csv(io.StringIO(csv), wymagane_pola=["id", "is_active"])
        assert wynik[0]["is_active"] == "1"
        assert wynik[1]["is_active"] == "0"

    def test_date_ddmmyyyy_kept(self):
        # Data w formacie DD-MM-YYYY nie jest walidowana, zwracana jako string
        csv = "id,join_date\n1,15-01-2021"
        wynik = parse_csv(io.StringIO(csv), wymagane_pola=["id", "join_date"])
        assert wynik[0]["join_date"] == "15-01-2021"


# --- Testy I/O i przypadki brzegowe ---
class TestCSVParserIOAndEdge:

    def test_parse_csv_file_not_found(self):
        # Nieistniejący plik → FileNotFoundError z parse_csv_file
        with pytest.raises(FileNotFoundError):
            parse_csv_file("does_not_exist.csv", wymagane_pola=["id"])

    def test_bytesio_raises_parsing_error(self):
        # BytesIO jako plik tekstowy → CSVParsingError o błędzie parsowania
        fake = io.BytesIO(b"id,name\n1,Alice")
        with pytest.raises(CSVParsingError, match="Błąd parsowania CSV"):
            parse_csv(fake, wymagane_pola=["id", "name"])

    def test_file_like_without_readlines_seek(self):
        # Obiekt iterator – poprawnie przejdzie, bo skipujemy pre-skan
        class LineIter:
            def __init__(self, text): self.lines = text.splitlines(True)
            def __iter__(self): return iter(self.lines)
        data = "id,name\n1,Alice"
        wynik = parse_csv(LineIter(data), wymagane_pola=["id", "name"])
        assert wynik[0]["name"] == "Alice"

    def test_unicode_decode_error(self):
        # UnicodeDecodeError podczas readlines → CSVParsingError o kodowaniu
        class Fake:
            def readlines(self): raise UnicodeDecodeError("utf-8", b"", 0, 1, "err")
        with pytest.raises(CSVParsingError, match="Nie można odczytać pliku CSV"):
            parse_csv(Fake(), wymagane_pola=["id"])

    def test_invalid_type_argument(self):
        # Nieprawidłowy typ argumentu (int) → CSVParsingError o obiekcie
        with pytest.raises(CSVParsingError, match="Nieprawidłowy obiekt pliku CSV"):
            parse_csv(12345, wymagane_pola=["id"])

    def test_empty_file(self):
        # Pusty plik → bez nagłówka, oczekujemy konkretnego komunikatu
        with pytest.raises(CSVParsingError, match="Brak wiersza nagłówka"):
            parse_csv(io.StringIO(""), wymagane_pola=["id"])

    def test_repeated_calls_stability(self):
        # Stabilność przy wielokrotnym parsowaniu
        csv = "id,name\n1,Alice\n2,Bob"
        for _ in range(50):
            wynik = parse_csv(io.StringIO(csv), wymagane_pola=["id", "name"])
            assert wynik[1]["name"] == "Bob"

    def test_performance_proxy(self):
        # Proxy test wydajności: 100k wierszy w <1s
        num = 100_000
        header = "id,name"
        rows = [f"{i},User{i}" for i in range(1, num+1)]
        content = "\n".join([header] + rows)
        start = time.time()
        wynik = parse_csv(io.StringIO(content), wymagane_pola=["id", "name"])
        elapsed = time.time() - start
        assert elapsed < 1.0, f"Za wolno: {elapsed:.2f}s"
        assert len(wynik) == num