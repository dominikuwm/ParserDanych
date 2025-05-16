import csv
import re
from typing import List, Dict, Optional, TextIO


class CSVParsingError(Exception):
    """Custom exception for CSV parsing errors."""
    pass

def parse_csv_file(file_path: str, required_fields: Optional[List[str]] = None, delimiter: str = ',') -> List[Dict[str, str]]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return parse_csv(f, required_fields=required_fields, delimiter=delimiter)
    except FileNotFoundError:
        raise  # Pozwól na propagację, by test mógł złapać ten wyjątek


def parse_csv(
    file_obj: TextIO,
    required_fields: Optional[List[str]] = None,
    delimiter: str = ','
) -> List[Dict[str, str]]:
    """
    Parses a CSV file and returns a list of dictionaries.

    :param file_obj: File-like object containing CSV data.
    :param required_fields: List of required fields to validate. If None, all header fields are treated as required.
    :param delimiter: Delimiter used in the CSV file.
    :return: List of dictionaries representing CSV rows.
    :raises CSVParsingError: If parsing fails or validation fails.
    """
    try:
        # Pre-scan for empty lines if possible
        try:
            lines = file_obj.readlines()
            for idx, line in enumerate(lines, start=1):
                if not line.strip() and idx != 1:  # Skip header line
                    raise CSVParsingError(f"Empty line detected at line {idx}.")
            file_obj.seek(0)
        except AttributeError:
            # File-like object doesn't support readlines or seek; ignore pre-scan
            pass

        reader = csv.DictReader(file_obj, delimiter=delimiter, skipinitialspace=True)

        if not reader.fieldnames:
            raise CSVParsingError("CSV file has no header row.")

        # --- Header validations ---
        if all(field.strip().isdigit() or not field.strip() for field in reader.fieldnames):
            raise CSVParsingError(
                "CSV header row looks invalid or missing (contains only numeric or empty values)."
            )

        if any(re.match(r"^\d", field.strip()) for field in reader.fieldnames):
            raise CSVParsingError(
                f"CSV header row contains invalid column names: {', '.join(reader.fieldnames)}. "
                "Column names should not start with a digit."
            )

        if any(" " in field.strip() for field in reader.fieldnames):
            raise CSVParsingError(
                f"CSV header row contains spaces in column names: {', '.join(reader.fieldnames)}."
            )

        if len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise CSVParsingError(
                f"CSV header row contains duplicate column names: {', '.join(reader.fieldnames)}."
            )

        if required_fields is None:
            required_fields = reader.fieldnames

        missing_fields = [field for field in required_fields if field not in reader.fieldnames]
        if missing_fields:
            raise CSVParsingError(f"Missing required fields in header: {', '.join(missing_fields)}")

        data = []
        for line_number, row in enumerate(reader, start=2):
            # 🛑 Check for extra columns
            if None in row:
                raise CSVParsingError(f"Extra columns found at line {line_number}.")

            # 🛑 Validate required fields are not empty or just spaces
            missing_values = [
                field for field in required_fields
                if not row.get(field) or not row.get(field).strip()
            ]
            if missing_values:
                raise CSVParsingError(
                    f"Missing required values in fields: {', '.join(missing_values)} at line {line_number}."
                )

            data.append(row)

        return data

    except UnicodeDecodeError:
        raise CSVParsingError("Unable to decode CSV file. Please check encoding.")
    except csv.Error as e:
        raise CSVParsingError(f"CSV parsing error: {str(e)}")
    except Exception as e:
        if isinstance(e, TypeError) and 'iterable' in str(e):
            raise CSVParsingError("Unable to decode CSV file. Please check encoding or file object validity.")
        raise CSVParsingError(f"An unexpected error occurred: {str(e)}")
