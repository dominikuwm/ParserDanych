import csv
import re
from typing import Dict, List, Optional, TextIO


class CSVParsingError(Exception):
    """Błąd podczas parsowania CSV."""
    pass


def parse_csv_file(
    sciezka: str,
    wymagane_pola: Optional[List[str]] = None,
    separator: str = ",",
) -> List[Dict[str, str]]:

    try:
        with open(sciezka, "r", encoding="utf-8") as plik:
            return parse_csv(plik, wymagane_pola, separator)
    except FileNotFoundError:
        # pozwalamy, by testy wychwyciły FileNotFoundError
        raise


def parse_csv(
    plik: TextIO,
    wymagane_pola: Optional[List[str]] = None,
    separator: str = ",",
) -> List[Dict[str, str]]:

    try:
        #1. Skan pustych wierszy
        try:
            for idx, line in enumerate(plik.readlines(), start=1):
                if not line.strip() and idx != 1:
                    raise CSVParsingError(
                        f"Pusta linia wykryta w wierszu {idx}."
                    )
            plik.seek(0)
        except AttributeError:
            # Obiekt nie wspiera readlines/seek pomijamy skan
            pass

        reader = csv.DictReader(
            plik,
            delimiter=separator,
            skipinitialspace=True,
        )
        naglowki = reader.fieldnames
        if not naglowki:
            raise CSVParsingError(
                "Brak wiersza nagłówka w pliku CSV."
            )

        #2. Walidacja nagłówka
        if all(h.strip().isdigit() or not h.strip() for h in naglowki):
            raise CSVParsingError(
                "Nagłówek wygląda niepoprawnie (tylko liczby lub puste)."
            )

        if any(re.match(r"^\d", h.strip()) for h in naglowki):
            raise CSVParsingError(
                f"Niewłaściwe nazwy kolumn: {', '.join(naglowki)}. "
                "Nazwy nie mogą zaczynać się od cyfry."
            )

        if any(" " in h for h in naglowki):
            raise CSVParsingError(
                f"Nazwy kolumn zawierają spacje: {', '.join(naglowki)}."
            )

        if len(naglowki) != len(set(naglowki)):
            raise CSVParsingError(
                f"Powtórzone nazwy kolumn: {', '.join(naglowki)}."
            )

        #3. Sprawdzenie wymaganych pól
        if wymagane_pola is None:
            wymagane_pola = naglowki.copy()

        brakujace = [p for p in wymagane_pola if p not in naglowki]
        if brakujace:
            raise CSVParsingError(
                f"Brakujące pola w nagłówku: {', '.join(brakujace)}."
            )

        #4. Iteracja po danych
        dane: List[Dict[str, str]] = []
        for idx, row in enumerate(reader, start=2):
            if None in row:
                raise CSVParsingError(
                    f"Dodatkowe kolumny w wierszu {idx}."
                )

            puste = [
                p
                for p in wymagane_pola
                if not row.get(p) or not row[p].strip()
            ]
            if puste:
                raise CSVParsingError(
                    f"Brak wartości w polach: {', '.join(puste)} "
                    f"w wierszu {idx}."
                )

            dane.append(row)

        return dane

    except UnicodeDecodeError as exc:
        raise CSVParsingError(
            "Nie można odczytać pliku CSV (błąd kodowania)."
        ) from exc
    except csv.Error as exc:
        raise CSVParsingError(
            f"Błąd parsowania CSV: {exc}"
        ) from exc
    except TypeError as exc:
        raise CSVParsingError(
            "Nieprawidłowy obiekt pliku CSV."
        ) from exc
    except Exception as exc:
        raise CSVParsingError(
            f"Nieoczekiwany błąd: {exc}"
        ) from exc
