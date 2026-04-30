"""CSV export functions for processed and unassigned transactions."""

import csv
import datetime
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

from data_processing.data_loader import Expense
from data_processing.location_processor import (
    create_google_maps_link,
    extract_location_from_data,
)

# Characters that trigger formula execution in Google Sheets / Excel when at the
# start of a cell value. Prefix them with a single quote to neutralise the risk.
_FORMULA_INJECTION_CHARS: frozenset[str] = frozenset("=+-@\t\r")


def _today_str() -> str:
    return datetime.date.today().strftime("%Y-%m-%d")


def _sanitize_cell(value: object) -> object:
    """Prefix formula-injection chars with a literal quote so spreadsheets treat the cell as text."""
    if isinstance(value, str) and value and value[0] in _FORMULA_INJECTION_CHARS:
        return "'" + value
    return value


def _sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with all string cells sanitized against formula injection."""
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].map(_sanitize_cell)
    return df


def export_for_google_sheets(processed_df: pd.DataFrame) -> Path:
    """Write the processed DataFrame to ``for_google_spreadsheet.csv``.

    Columns: ``Day, Month, Year, Item, Category, Amount, Importance``.
    ``Amount`` uses a comma as the decimal separator (European format).
    The file is written with a tab separator and restricted to owner-only
    read/write permissions (PII protection).

    Args:
        processed_df: Processed transaction DataFrame to export.

    Returns:
        Path to the written CSV file.
    """
    logger.info("Exporting {} rows for Google Sheets", len(processed_df))

    rows = []
    for row in processed_df.itertuples(index=False):
        expense = Expense(str(row.month), str(row.year), str(row.category), str(row.price))
        rows.append({
            "Day": row.day,
            "Month": row.month,
            "Year": row.year,
            "Item": row.category,
            "Category": expense.category.value,
            "Amount": str(row.price).replace(".", ","),
            "Importance": expense.importance.value,
        })

    output_df = pd.DataFrame(rows, columns=["Day", "Month", "Year", "Item", "Category", "Amount", "Importance"])
    output_df = _sanitize_dataframe(output_df)

    output_file = Path("for_google_spreadsheet.csv")

    # Guard against symlink TOCTOU: refuse to overwrite a symlink target
    if output_file.is_symlink():
        raise OSError(f"Refusing to write to symlink: {output_file}")

    output_df.to_csv(output_file, sep="\t", index=False)

    # Restrict file permissions to owner-only read/write (PII protection)
    if sys.platform != "win32":
        output_file.chmod(0o600)

    logger.info(f"Exported data for Google Sheets to '{output_file}'.")
    return output_file


def export_misc_transactions(df: pd.DataFrame) -> None:
    """Export uncategorized (MISC) transactions to CSV.

    Args:
        df: DataFrame containing all categorized transactions.
    """
    misc_df = df[df["category"].str.contains("MISC", na=False)]
    export_unassigned_transactions_to_csv(misc_df)
    logger.info("[EXPORT] Unassigned (MISC) transactions exported")


def export_cleaned_data(df: pd.DataFrame, output_file: Path | str = Path("data/processed_transactions.csv")) -> None:
    """Write the ``[day, month, year, category, price]`` columns to a CSV file.

    Uses ``utf-8-sig`` encoding so the file opens correctly in Windows Excel.

    Args:
        df: Processed transaction DataFrame.
        output_file: Destination path. Defaults to
            ``data/processed_transactions.csv``.

    Raises:
        ValueError: If ``output_file`` resolves outside the current working directory.
    """
    # Guard against path traversal: output must resolve within the project directory
    resolved = Path(output_file).resolve()
    try:
        resolved.relative_to(Path.cwd())
    except ValueError:
        raise ValueError(f"Output path {output_file!r} must resolve within the project directory {Path.cwd()!r}")

    sanitized = _sanitize_dataframe(df)
    sanitized.to_csv(
        output_file,
        columns=["day", "month", "year", "category", "price"],
        index=False,
        encoding="utf-8-sig",
    )
    logger.info(f"[EXPORT] Cleaned data saved to {output_file}")


def export_unassigned_transactions_to_csv(df: pd.DataFrame) -> None:
    """Write MISC transactions to ``unassigned_transactions.csv``.

    The output includes ``extracted_location`` and ``google_maps_link`` columns.
    Uses ``utf-8-sig`` encoding for Windows Excel compatibility.

    Args:
        df: DataFrame containing uncategorized (MISC) transactions.
    """
    # Add location processing only for unassigned transactions
    df_copy = df.copy()
    df_copy["extracted_location"] = df_copy["data"].apply(extract_location_from_data)
    df_copy["google_maps_link"] = df_copy["extracted_location"].apply(create_google_maps_link)

    df_copy = _sanitize_dataframe(df_copy)
    output_file = Path("unassigned_transactions.csv")
    # Keep BOM for Windows Excel when exporting unassigned transactions
    df_copy.to_csv(output_file, index=False, encoding="utf-8-sig")
    logger.info(f"[EXPORT] Unassigned transactions with location data saved to {output_file}")


def get_data(path: Path = Path("data/processed_transactions.csv")) -> list[Expense]:
    """Read a processed transactions CSV and return a list of Expense objects.

    Columns must be in the order ``month, year, category, price``.

    Args:
        path: Path to the CSV file. Defaults to
            ``data/processed_transactions.csv``.

    Returns:
        List of ``Expense`` objects, one per row in the CSV.
    """
    expenses: list[Expense] = []
    with open(path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        next(reader)  # Skip the header row
        for row in reader:
            expenses.append(Expense(row[0], row[1], row[2], row[3]))
    return expenses
