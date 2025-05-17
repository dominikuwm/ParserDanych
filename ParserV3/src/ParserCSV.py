import csv
import re
from typing import List, Dict, Optional, TextIO

class CSVParsingError(Exception):
    """Błąd podczas parsowania CSV."""
    pass

def parse_csv_file(sciezka: str,
                   wymagane_pola: Optional[List[str]] = None,
                   separator: str = ',') -> List[Dict[str, str]]:
    """
    Otwiera plik o zadanej ścieżce i przekazuje go do głównej funkcji parse_csv.
    """
    try:
        with open(sciezka, 'r', encoding='utf-8') as plik:
            return parse_csv(plik, wymagane_pola, separator)
    except FileNotFoundError:
        # pozwalamy, by testy wychwyciły FileNotFoundError
        raise

def parse_csv(plik: TextIO,
              wymagane_pola: Optional[List[str]] = None,
              separator: str = ',') -> List[Dict[str, str]]:

    try:
        # 1) Pre-skanujemy w poszukiwaniu pustych linii (po nagłówku)
        try:
            linie = plik.readlines()
            for nr, linia in enumerate(linie, start=1):
                if not linia.strip() and nr != 1:
                    raise CSVParsingError(f"Pusta linia wykryta w wierszu {nr}.")
            plik.seek(0)
        except AttributeError:
            # jeśli plik nie ma readlines/seek, pomijamy pre-skan
            pass

        czytnik = csv.DictReader(plik, delimiter=separator, skipinitialspace=True)
        naglowki = czytnik.fieldnames
        if not naglowki:
            raise CSVParsingError("Brak wiersza nagłówka w pliku CSV.")

        # 2) Walidacja nagłówka
        if all(h.strip().isdigit() or not h.strip() for h in naglowki):
            raise CSVParsingError("Nagłówek wygląda niepoprawnie (tylko liczby lub puste).")

        if any(re.match(r"^\d", h.strip()) for h in naglowki):
            raise CSVParsingError(f"Niewłaściwe nazwy kolumn: {', '.join(naglowki)}. Nazwy nie mogą zaczynać się od cyfry.")

        if any(" " in h for h in naglowki):
            raise CSVParsingError(f"Nazwy kolumn zawierają spacje: {', '.join(naglowki)}.")

        if len(naglowki) != len(set(naglowki)):
            raise CSVParsingError(f"Powtórzone nazwy kolumn: {', '.join(naglowki)}.")

        # 3) Sprawdzenie wymaganych pól
        if wymagane_pola is None:
            wymagane_pola = naglowki.copy()

        brakujace = [p for p in wymagane_pola if p not in naglowki]
        if brakujace:
            raise CSVParsingError(f"Brakujące pola w nagłówku: {', '.join(brakujace)}.")

        # 4) Iteracja po wierszach danych
        dane = []
        for nr, wiersz in enumerate(czytnik, start=2):
            if None in wiersz:
                raise CSVParsingError(f"Dodatkowe kolumny w wierszu {nr}.")

            puste = [p for p in wymagane_pola if not wiersz.get(p) or not wiersz[p].strip()]
            if puste:
                raise CSVParsingError(f"Brak wartości w polach: {', '.join(puste)} w wierszu {nr}.")

            dane.append(wiersz)

        return dane

    except UnicodeDecodeError:
        raise CSVParsingError("Nie można odczytać pliku CSV (błąd kodowania).")
    except csv.Error as e:
        raise CSVParsingError(f"Błąd parsowania CSV: {e}")
    except TypeError:
        raise CSVParsingError("Nieprawidłowy obiekt pliku CSV.")
    except Exception as e:
        raise CSVParsingError(f"Nieoczekiwany błąd: {e}")
