import pytest
import io
from src.ParserCSV import parse_csv, CSVParsingError
import time


#testy dla poprawnych danych
class TestCSVParserCorrectData:

    @pytest.mark.parametrize("csv_content, delimiter", [
        # Test 1: Standardowy CSV z przecinkiem jako separatorem
        ("id,name,age\n1,Alice,30\n2,Bob,25", ","),

        # Test 2: CSV z separatorem '|'
        ("id|name|age\n1|Alice|30\n2|Bob|25", "|"),

        # Test 3: CSV z separatorem ';'
        ("id;name;age\n1;Alice;30\n2;Bob;25", ";"),

        # Test 4: CSV z separatorem tabulacji
        ("id\tname\tage\n1\tAlice\t30\n2\tBob\t25", "\t"),

        # Test 5: CSV z separatorem '#'
        ("id#name#age\n1#Alice#30\n2#Bob#25", "#"),

        # Test 6: CSV z separatorem '~'
        ("id~name~age\n1~Alice~30\n2~Bob~25", "~"),
    ])
    def test_valid_csv_with_various_separators(self, csv_content: str, delimiter: str):
        """Test poprawnych danych z różnymi separatorami."""
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "age"], delimiter=delimiter)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["age"] == "25"

    def test_large_csv_file(self):
        """Test poprawnego działania na dużym pliku (1000+ rekordów)."""
        csv_content = "\n".join(["id,name,age"] + [f"{i},User{i},{20+i}" for i in range(1000)])
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "age"])
        assert len(result) == 1000
        assert result[500]["name"] == "User500"

    def test_csv_with_special_characters(self):
        """Test poprawnego działania z nietypowymi znakami w polach (przecinki, emoji, cudzysłowy)."""
        csv_content = 'id,name,comment\n1,Alice,"Hello, World! 🌍"\n2,Bob,"Nice : )"'
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "comment"])
        assert result[0]["comment"] == "Hello, World! 🌍"
        assert result[1]["comment"] == "Nice : )"

    def test_csv_with_various_data_types(self):
        """Test poprawnych danych z różnymi typami danych (int, bool, str)."""
        csv_content = "id,name,is_active,age\n1,Alice,True,30\n2,Bob,False,25"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "is_active", "age"])
        assert result[0]["is_active"] == "True"
        assert result[1]["age"] == "25"

    def test_csv_with_optional_empty_columns(self):
        """Test poprawnych plików z pustymi nieobowiązkowymi kolumnami."""
        csv_content = "id,name,email\n1,Alice,alice@example.com\n2,Bob,"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name"], delimiter=",")
        assert len(result) == 2
        assert result[1]["email"] == ""  # Pole opcjonalne jest puste, ale parser nie zgłasza błędu
#testy dla niepoprawnych naglowkow
class TestCSVParserInvalidHeaders:

    def test_missing_header(self):
        """Test braku nagłówka — pierwszy wiersz wygląda jak dane, nie jak nazwy kolumn."""
        csv_content = "1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="header"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_header_with_only_numbers(self):
        """Test, gdy nagłówki zawierają wyłącznie liczby — parser powinien uznać to za brak nagłówka."""
        csv_content = "1,2,3\n1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="header"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_empty_header_fields(self):
        """Test pustych nagłówków (brak nazw kolumn)."""
        csv_content = ",,\n1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="header"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_header_with_invalid_characters(self):
        """Test nagłówków z niedozwolonymi znakami (np. znaki specjalne)."""
        csv_content = "id,na$me,ag@e\n1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        # Parser powinien pozwolić na dziwne nagłówki lub rzucić błąd — zależnie od założeń.
        with pytest.raises(CSVParsingError):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_header_starting_with_digit(self):
        """Test nagłówków zaczynających się od cyfry (np. '1name')."""
        csv_content = "1name,name,age\n1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="invalid column names"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_duplicate_column_names(self):
        """Test duplikujących się nazw kolumn."""
        csv_content = "id,name,name\n1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="duplicate"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_missing_required_columns(self):
        """Test braku wymaganych kolumn w nagłówku."""
        csv_content = "id,name\n1,Alice\n2,Bob"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="Missing required fields"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_additional_unnecessary_columns(self):
        """Test nadmiarowych, niepotrzebnych kolumn. Parser powinien je ignorować, jeśli nie są wymagane."""
        csv_content = "id,name,age,extra_column\n1,Alice,30,something\n2,Bob,25,extra"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "age"])
        # Nie powinno być błędu, ale dodatkowa kolumna powinna istnieć w danych.
        assert "extra_column" in result[0]
        assert result[0]["extra_column"] == "something"

    def test_header_with_spaces_in_names(self):
        """Test nagłówków zawierających spacje (np. 'first name')."""
        csv_content = "id,first name,age\n1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        # Parser powinien zgłosić błąd lub poprawnie sparsować, jeśli obsługuje takie przypadki.
        with pytest.raises(CSVParsingError, match="header"):
            parse_csv(file_obj, required_fields=["id", "first name", "age"])

    def test_header_with_different_case_formats(self):
        """Test nagłówków z różnymi formatami wielkości liter (np. 'First_Name' vs 'first_name')."""
        csv_content = "ID,First_Name,Age\n1,Alice,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        # Jeśli parser jest case-sensitive, zgłosi błąd dla wymaganych pól w innym formacie.
        with pytest.raises(CSVParsingError, match="Missing required fields"):
            parse_csv(file_obj, required_fields=["id", "first_name", "age"])

#Nieprawidlowe dane
class TestCSVParserInvalidData:

    def test_required_field_empty_value(self):
        """Test pustych wymaganych pól."""
        csv_content = "id,name,age\n1,,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="Missing required values"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_empty_lines_in_middle_of_file(self):
        """Test pustych linii w środku pliku."""
        csv_content = "id,name,age\n1,Alice,30\n\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_incomplete_columns_in_row(self):
        """Test niepełnej liczby kolumn w jednym z wierszy."""
        csv_content = "id,name,age\n1,Alice,30\n2,Bob"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_empty_file(self):
        """Test pustego pliku."""
        csv_content = ""
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="header"):
            parse_csv(file_obj)

    def test_invalid_numeric_value(self):
        """Test nieprawidłowego formatu wartości (wiek jako tekst)."""
        csv_content = "id,name,age\n1,Alice,trzydzieści"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "age"])
        assert result[0]["age"] == "trzydzieści"

    def test_boolean_value_format(self):
        """Test poprawności formatu wartości bool (True/False vs 1/0)."""
        csv_content = "id,name,is_active\n1,Alice,1\n2,Bob,0"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "is_active"])
        assert result[0]["is_active"] == "1"
        assert result[1]["is_active"] == "0"

    def test_additional_columns_in_data_row(self):
        """Test nadmiarowych kolumn w wierszu danych."""
        csv_content = "id,name,age\n1,Alice,30,extra\n2,Bob,25,extra"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_invalid_date_format(self):
        """Test niepoprawnego formatu daty (jeśli parser miałby to sprawdzać)."""
        csv_content = "id,name,join_date\n1,Alice,15-01-2021"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "join_date"])
        assert result[0]["join_date"] == "15-01-2021"

    def test_spaces_instead_of_empty_values(self):
        """Test wartości zawierających tylko spacje zamiast pustych wartości."""
        csv_content = "id,name,age\n1,   ,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_very_large_numeric_values(self):
        """Test bardzo dużych wartości liczbowych."""
        csv_content = f"id,name,age\n{2**31},Alice,30"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "age"])
        assert result[0]["id"] == str(2**31)

    def test_newline_character_in_field(self):
        """Test znaku nowej linii w polu (np. w komentarzu)."""
        csv_content = 'id,name,comment\n1,Alice,"Line1\\nLine2"'
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "comment"])
        assert "\\n" in result[0]["comment"]

    def test_very_long_field_value(self):
        """Test bardzo długiego ciągu znaków w polu (1000+ znaków)."""
        long_comment = "a" * 1000
        csv_content = f"id,name,comment\n1,Alice,{long_comment}"
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "comment"])
        assert len(result[0]["comment"]) == 1000

    def test_invalid_encoding_simulation(self):
        """Symulacja błędu kodowania (UnicodeDecodeError)."""

        class FakeFile:
            def __iter__(self):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

        with pytest.raises(CSVParsingError, match="Unable to decode"):
            parse_csv(FakeFile())

    def test_invalid_separator_in_data(self):
        """Test błędnego separatora w danych (np. ';' zamiast ',')."""
        csv_content = "id;name;age\n1;Alice;30"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError):
            parse_csv(file_obj, required_fields=["id", "name", "age"], delimiter=",")

    def test_large_file_with_one_bad_line(self):
        """Test dużego pliku z błędem w jednej linii (np. brak kolumn w linii 999)."""
        rows = [f"{i},User{i},{20+i}" for i in range(2, 999)] + ["999,BadLine"] + ["1000,User1000,30"]
        csv_content = "\n".join(["id,name,age"] + rows)
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="line 999"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

class TestCSVParserPerformance:

    def test_parse_very_large_file(self):
        """Test parsowania bardzo dużego pliku (100k rekordów)."""
        num_records = 100_000
        header = "id,name,age"
        rows = [f"{i},User{i},{20+i%50}" for i in range(1, num_records + 1)]
        csv_content = "\n".join([header] + rows)
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "age"])
        assert len(result) == num_records
        assert result[0]["name"] == "User1"
        assert result[-1]["age"] == str(20 + (num_records % 50))

    def test_parse_large_file_time(self):
        """Pomiar czasu wykonania dla dużego pliku - powinno być poniżej 1 sekundy."""
        num_records = 100_000
        header = "id,name,age"
        rows = [f"{i},User{i},{20+i%50}" for i in range(1, num_records + 1)]
        csv_content = "\n".join([header] + rows)
        file_obj = io.StringIO(csv_content)

        start_time = time.time()
        result = parse_csv(file_obj, required_fields=["id", "name", "age"])
        end_time = time.time()
        elapsed = end_time - start_time

        assert elapsed < 1, f"Parsing took too long: {elapsed:.2f} seconds"
        assert len(result) == num_records

    def test_parser_memory_simple_check(self):
        """Prosty test, czy parser nie zwraca pustych wyników dla dużych danych (proxy test na pamięć)."""
        num_records = 50_000
        header = "id,name,age"
        rows = [f"{i},User{i},{20+i%50}" for i in range(1, num_records + 1)]
        csv_content = "\n".join([header] + rows)
        file_obj = io.StringIO(csv_content)
        result = parse_csv(file_obj, required_fields=["id", "name", "age"])
        assert len(result) == num_records

    def test_multiple_calls_parser(self):
        """Test wielokrotnego wywołania parsera w pętli (100 razy)."""
        num_records = 1000
        header = "id,name,age"
        rows = [f"{i},User{i},{20+i%50}" for i in range(1, num_records + 1)]
        csv_content = "\n".join([header] + rows)

        for _ in range(100):
            file_obj = io.StringIO(csv_content)
            result = parse_csv(file_obj, required_fields=["id", "name", "age"])
            assert len(result) == num_records

    def test_stability_under_repeated_parse(self):
        """Test stabilności działania parsera przy powtarzanym parsowaniu tego samego pliku."""
        csv_content = "id,name,age\n1,Alice,30\n2,Bob,25"
        for _ in range(1000):
            file_obj = io.StringIO(csv_content)
            result = parse_csv(file_obj, required_fields=["id", "name", "age"])
            assert result[0]["name"] == "Alice"
            assert result[1]["age"] == "25"

class TestCSVParserExceptions:

    def test_exception_type_and_message_contains_line_number(self):
        """Test, czy wyjątek zawiera numer linii w komunikacie."""
        csv_content = "id,name,age\n1,Alice,30\n2,Bob"  # brak wartości w 3. kolumnie w 3. linii
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError) as excinfo:
            parse_csv(file_obj, required_fields=["id", "name", "age"])
        assert "line 3" in str(excinfo.value)

    def test_unicode_decode_error_handling(self):
        """Test obsługi błędu kodowania UnicodeDecodeError."""
        class FakeFile:
            def __iter__(self):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")

        with pytest.raises(CSVParsingError, match="Unable to decode"):
            parse_csv(FakeFile())

    def test_file_not_found_error_handling(self):
        """Test obsługi błędu przy próbie otwarcia nieistniejącego pliku (jeśli dotyczy)."""
        import os
        from src.ParserCSV import parse_csv_file  # jeśli masz funkcję czytającą z pliku

        with pytest.raises(FileNotFoundError):
            parse_csv_file("nieistniejacy_plik.csv")

    def test_binary_file_as_csv(self):
        """Test próby wczytania pliku binarnego jako CSV (powinien rzucić błąd)."""
        binary_data = b"\x00\x01\x02\x03\x04"
        fake_file = io.BytesIO(binary_data)
        with pytest.raises(CSVParsingError):
            # Trzeba przekonwertować na TextIO lub wywołać parser bezpośrednio na tym obiekcie
            parse_csv(fake_file)

    def test_required_fields_empty_or_none(self):
        """Test obsługi sytuacji gdy wymagane pola są puste lub None."""
        csv_content = "id,name,age\n1,,30\n2,Bob,25"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="Missing required values"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_invalid_delimiter(self):
        """Test rzucenia błędu dla złego delimiter'a."""
        csv_content = "id;name;age\n1;Alice;30"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError):
            parse_csv(file_obj, required_fields=["id", "name", "age"], delimiter=",")

    def test_duplicate_headers_error(self):
        """Test błędu przy nagłówkach z duplikatami."""
        csv_content = "id,name,name\n1,Alice,30"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="duplicate"):
            parse_csv(file_obj, required_fields=["id", "name", "age"])

    def test_parsing_empty_file(self):
        """Test próby parsowania pustego pliku."""
        csv_content = ""
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError, match="no header"):
            parse_csv(file_obj)

    def test_parser_with_wrong_type_input(self):
        """Test podania niepoprawnego typu (np. int zamiast TextIO)."""
        with pytest.raises(CSVParsingError):
            parse_csv(12345)

    def test_exception_message_readability(self):
        """Test czy komunikaty błędów są czytelne."""
        csv_content = "id,name,age\n1,Alice,30\n2,Bob"
        file_obj = io.StringIO(csv_content)
        with pytest.raises(CSVParsingError) as excinfo:
            parse_csv(file_obj, required_fields=["id", "name", "age"])
        msg = str(excinfo.value)
        assert "Missing required values" in msg and "line 3" in msg
