import io
import time

import pytest

from src.ParserCSV import CSVParsingError, parse_csv, parse_csv_file


# Poprawne dane wejściowe



class TestCSVParserValidData:
    """Scenariusze, w których parser zwraca poprawne wyniki."""

    @pytest.mark.parametrize(
        ("csv_content", "separator"),
        [
            ("id,name,age\n1,Alice,30\n2,Bob,25", ","),
            ("id|name|age\n1|Alice|30\n2|Bob|25", "|"),
            ("id;name;age\n1;Alice;30\n2;Bob;25", ";"),
            ("id\tname\tage\n1\tAlice\t30\n2\tBob\t25", "\t"),
            ("id#name#age\n1#Alice#30\n2#Bob#25", "#"),
            ("id~name~age\n1~Alice~30\n2~Bob~25", "~"),
        ],
    )
    def test_various_separators(
        self,
        csv_content: str,
        separator: str,
    ) -> None:
        file_obj = io.StringIO(csv_content)
        result = parse_csv(
            file_obj,
            wymagane_pola=["id", "name", "age"],
            separator=separator,
        )
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["age"] == "25"

    def test_large_file(self) -> None:
        header = "id,name,age"
        rows = [f"{i},User{i},{20 + i}" for i in range(1000)]
        content = "\n".join([header] + rows)
        result = parse_csv(
            io.StringIO(content),
            wymagane_pola=["id", "name", "age"],
        )
        assert len(result) == 1000
        assert result[500]["name"] == "User500"

    def test_quoted_fields_with_commas(self) -> None:
        csv_ = (
            'id,name,comment\n1,Alice,"Hello, World!"\n2,Bob,"Nice : )"'
        )
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "name", "comment"],
        )
        assert result[0]["comment"] == "Hello, World!"
        assert result[1]["comment"] == "Nice : )"

    def test_optional_empty_column(self) -> None:
        csv_ = (
            "id,name,email\n1,Alice,alice@example.com\n2,Bob,"
        )
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "name"],
        )
        assert result[1]["email"] == ""

    def test_types_as_strings(self) -> None:
        csv_ = (
            "id,name,is_active,age\n1,Alice,True,30\n2,Bob,False,25"
        )
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "name", "is_active", "age"],
        )
        assert isinstance(result[0]["is_active"], str)
        assert result[0]["is_active"] == "True"
        assert result[1]["age"] == "25"

    def test_unicode_and_emoji(self) -> None:
        csv_ = "id,name,emoji\n1,Alice,🌍\n2,Bob,✓"
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "name", "emoji"],
        )
        assert result[0]["emoji"] == "🌍"
        assert result[1]["emoji"] == "✓"

    def test_very_long_field(self) -> None:
        long_str = "x" * 1200
        csv_ = f"id,name,long\n1,Alice,{long_str}"
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "name", "long"],
        )
        assert len(result[0]["long"]) == 1200

    def test_mixed_case_data(self) -> None:
        csv_ = "id,Name,Age\n1,alice,30\n2,BOB,25"
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "Name", "Age"],
        )
        assert result[0]["Name"] == "alice"
        assert result[1]["Age"] == "25"



# Walidacja nagłówka



class TestCSVParserHeaderValidation:
    """Błędy związane z wierszem nagłówka."""

    def test_no_header_raises(self) -> None:
        csv_ = "1,Alice,30\n2,Bob,25"
        with pytest.raises(
            CSVParsingError,
            match=r"Niewłaściwe nazwy kolumn",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
            )

    def test_header_only_digits(self) -> None:
        csv_ = "1,2,3\n1,Alice,30"
        with pytest.raises(
            CSVParsingError,
            match=r"tylko liczby",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["1", "2", "3"],
            )

    def test_header_starts_with_digit(self) -> None:
        csv_ = "1col,name,age\n1,Alice,30"
        with pytest.raises(
            CSVParsingError,
            match=r"Nazwy nie mogą zaczynać się od cyfry",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["1col", "name", "age"],
            )

    def test_header_contains_space(self) -> None:
        csv_ = "id,first name,age\n1,Alice,30"
        with pytest.raises(
            CSVParsingError,
            match=r"zawierają spacje",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "first name", "age"],
            )

    def test_header_with_duplicates(self) -> None:
        csv_ = "id,name,name\n1,Alice,30"
        with pytest.raises(
            CSVParsingError,
            match=r"Powtórzone nazwy kolumn",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
            )

    def test_missing_required_field(self) -> None:
        csv_ = "id,name\n1,Alice"
        with pytest.raises(
            CSVParsingError,
            match=r"Brakujące pola",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
            )

    def test_header_with_special_chars(self) -> None:
        csv_ = "id,na$me,age\n1,Alice,30"
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "na$me", "age"],
        )
        assert result[0]["na$me"] == "Alice"

    def test_case_sensitive_header(self) -> None:
        csv_ = "ID,Name,Age\n1,Alice,30"
        with pytest.raises(
            CSVParsingError,
            match=r"Brakujące pola",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "Name", "Age"],
            )



# Walidacja pojedynczych wierszy



class TestCSVParserRowValidation:
    """Błędy dotyczące wierszy danych."""

    def test_empty_line_in_middle(self) -> None:
        csv_ = "id,name,age\n1,Alice,30\n\n2,Bob,25"
        with pytest.raises(
            CSVParsingError,
            match=r"wierszu 3",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
            )

    def test_row_with_too_few_columns(self) -> None:
        csv_ = "id,name,age\n1,Alice"
        with pytest.raises(
            CSVParsingError,
            match=r"Brak wartości w polach: age w wierszu 2",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
            )

    def test_row_with_extra_columns(self) -> None:
        csv_ = "id,name,age\n1,Alice,30,extra"
        with pytest.raises(
            CSVParsingError,
            match=r"Dodatkowe kolumny w wierszu 2",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
            )

    def test_required_field_blank_or_spaces(self) -> None:
        csv_ = "id,name,age\n1,   ,30"
        with pytest.raises(
            CSVParsingError,
            match=r"Brak wartości w polach: name w wierszu 2",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
            )

    def test_separator_mismatch(self) -> None:
        csv_ = "id,name,age\n1,Alice,30"
        with pytest.raises(
            CSVParsingError,
            match=r"Brakujące pola",
        ):
            parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name", "age"],
                separator=";",
            )

    def test_numeric_string_not_converted(self) -> None:
        csv_ = "id,age\n1,not_a_number"
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "age"],
        )
        assert result[0]["age"] == "not_a_number"

    def test_boolean_1_0_as_string(self) -> None:
        csv_ = "id,is_active\n1,1\n2,0"
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "is_active"],
        )
        assert result[0]["is_active"] == "1"
        assert result[1]["is_active"] == "0"

    def test_date_ddmmyyyy_kept(self) -> None:
        csv_ = "id,join_date\n1,15-01-2021"
        result = parse_csv(
            io.StringIO(csv_),
            wymagane_pola=["id", "join_date"],
        )
        assert result[0]["join_date"] == "15-01-2021"



# I/O i inne przypadki brzegowe



class TestCSVParserIOAndEdge:
    """Obsługa wyjątków związanych z plikami i wydajnością."""

    def test_parse_csv_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_csv_file("does_not_exist.csv", wymagane_pola=["id"])

    def test_bytesio_raises_parsing_error(self) -> None:
        fake = io.BytesIO(b"id,name\n1,Alice")
        with pytest.raises(
            CSVParsingError,
            match=r"Błąd parsowania CSV",
        ):
            parse_csv(fake, wymagane_pola=["id", "name"])

    def test_file_like_without_readlines_seek(self) -> None:
        class LineIter:  # noqa: D401
            def __init__(self, text: str) -> None:
                self.lines = text.splitlines(True)

            def __iter__(self):
                return iter(self.lines)

        data = "id,name\n1,Alice"
        result = parse_csv(
            LineIter(data),
            wymagane_pola=["id", "name"],
        )
        assert result[0]["name"] == "Alice"

    def test_unicode_decode_error(self) -> None:
        class Fake:  # noqa: D401
            def readlines(self):  # noqa: D401
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "err")

        with pytest.raises(
            CSVParsingError,
            match=r"Nie można odczytać pliku CSV",
        ):
            parse_csv(Fake(), wymagane_pola=["id"])

    def test_invalid_type_argument(self) -> None:
        with pytest.raises(
            CSVParsingError,
            match=r"Nieprawidłowy obiekt pliku CSV",
        ):
            parse_csv(12345, wymagane_pola=["id"])

    def test_empty_file(self) -> None:
        with pytest.raises(
            CSVParsingError,
            match=r"Brak wiersza nagłówka",
        ):
            parse_csv(io.StringIO(""), wymagane_pola=["id"])

    def test_repeated_calls_stability(self) -> None:
        csv_ = "id,name\n1,Alice\n2,Bob"
        for _ in range(50):
            result = parse_csv(
                io.StringIO(csv_),
                wymagane_pola=["id", "name"],
            )
            assert result[1]["name"] == "Bob"

    def test_performance_proxy(self) -> None:
        num = 100_000
        header = "id,name"
        rows = [f"{i},User{i}" for i in range(1, num + 1)]
        content = "\n".join([header] + rows)

        start = time.time()
        result = parse_csv(
            io.StringIO(content),
            wymagane_pola=["id", "name"],
        )
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Za wolno: {elapsed:.2f}s"
        assert len(result) == num
