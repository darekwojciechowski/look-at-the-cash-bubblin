"""CSV export functions for processed and unassigned transactions."""

import datetime
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

from data_processing.expense import CATEGORY_DISPLAY
from data_processing.location_processor import (
    create_google_maps_link,
    extract_location_from_data,
)

# Characters that trigger formula execution in Google Sheets / Excel when at the
# start of a cell value. Prefix them with a single quote to neutralise the risk.
_FORMULA_INJECTION_CHARS: frozenset[str] = frozenset("=+-@\t\r")

_GOOGLE_SHEETS_COLUMNS: list[str] = ["Day", "Month", "Year", "Item", "Category", "Amount", "Importance"]
_CLEANED_COLUMNS: list[str] = ["day", "month", "year", "category", "amount"]


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


def _write_google_sheets_csv(output_df: pd.DataFrame, output_path: Path) -> Path:
    """Write *output_df* as a tab-separated Google Sheets export.

    Sanitizes cells against formula injection, refuses to overwrite a symlink
    (TOCTOU guard), writes with a tab separator, and restricts file permissions
    to owner-only read/write on POSIX (PII protection).
    """
    output_df = _sanitize_dataframe(output_df)

    if output_path.is_symlink():
        raise OSError(f"Refusing to write to symlink: {output_path}")

    output_df.to_csv(output_path, sep="\t", index=False)

    if sys.platform != "win32":
        output_path.chmod(0o600)

    return output_path


def _write_cleaned_csv(df: pd.DataFrame, columns: list[str], output_path: Path | str) -> None:
    """Write *df* as a comma-separated utf-8-sig CSV restricted to *columns*.

    Refuses to write outside the project directory (path-traversal guard).
    """
    resolved = Path(output_path).resolve()
    try:
        resolved.relative_to(Path.cwd())
    except ValueError as err:
        raise ValueError(
            f"Output path {output_path!r} must resolve within the project directory {Path.cwd()!r}"
        ) from err

    sanitized = _sanitize_dataframe(df)
    sanitized.to_csv(output_path, columns=columns, index=False, encoding="utf-8-sig")


def export_for_google_sheets(processed_df: pd.DataFrame) -> Path:
    """Write the processed expense DataFrame to ``google_sheets_expenses.csv``.

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
        cat, imp = CATEGORY_DISPLAY[str(row.category)]
        rows.append({
            "Day": row.day,
            "Month": row.month,
            "Year": row.year,
            "Item": row.category,
            "Category": cat.value,
            "Amount": str(row.amount).replace(".", ","),
            "Importance": imp.value,
        })

    output_df = pd.DataFrame(rows, columns=_GOOGLE_SHEETS_COLUMNS)
    output_file = _write_google_sheets_csv(output_df, Path("google_sheets_expenses.csv"))

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
    """Write the ``[day, month, year, category, amount]`` columns to a CSV file.

    Uses ``utf-8-sig`` encoding so the file opens correctly in Windows Excel.

    Args:
        df: Processed transaction DataFrame.
        output_file: Destination path. Defaults to
            ``data/processed_transactions.csv``.

    Raises:
        ValueError: If ``output_file`` resolves outside the current working directory.
    """
    _write_cleaned_csv(df, _CLEANED_COLUMNS, output_file)
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


def export_income_for_google_sheets(income_df: pd.DataFrame) -> Path:
    """Write the processed income DataFrame to ``google_sheets_income.csv``.

    Columns mirror the expense export schema:
    ``Day, Month, Year, Item, Category, Amount, Importance``. ``Item`` and
    ``Category`` both carry the income label (SALARY, SIDE_HUSTLE,
    EXTRA_INCOME, INCOME_MISC) since income has no separate display taxonomy.
    ``Importance`` is left blank — the expense importance scale does not apply
    to income.

    Args:
        income_df: Processed income transaction DataFrame.

    Returns:
        Path to the written CSV file.
    """
    logger.info("Exporting {} income rows for Google Sheets", len(income_df))

    rows = []
    for row in income_df.itertuples(index=False):
        rows.append({
            "Day": row.day,
            "Month": row.month,
            "Year": row.year,
            "Item": row.category,
            "Category": row.category,
            "Amount": str(row.amount).replace(".", ","),
            "Importance": "",
        })

    output_df = pd.DataFrame(rows, columns=_GOOGLE_SHEETS_COLUMNS)
    output_file = _write_google_sheets_csv(output_df, Path("google_sheets_income.csv"))

    logger.info(f"Exported income data for Google Sheets to '{output_file}'.")
    return output_file


def export_cleaned_income_data(df: pd.DataFrame, output_file: Path | str = Path("data/processed_income.csv")) -> None:
    """Write the ``[day, month, year, category, amount]`` columns to a CSV file.

    Mirrors ``export_cleaned_data`` for income — same schema, same encoding,
    same path-traversal guard, different destination.

    Args:
        df: Processed income DataFrame.
        output_file: Destination path. Defaults to ``data/processed_income.csv``.

    Raises:
        ValueError: If ``output_file`` resolves outside the current working directory.
    """
    _write_cleaned_csv(df, _CLEANED_COLUMNS, output_file)
    logger.info(f"[EXPORT] Cleaned income data saved to {output_file}")


def export_unassigned_income(df: pd.DataFrame) -> None:
    """Write INCOME_MISC rows to ``unassigned_income.csv`` for manual review.

    Unlike the expense MISC export, income unassigned rows carry **no**
    ``extracted_location`` or ``google_maps_link`` columns: paychecks,
    transfers, and refunds are not place-bound.

    Args:
        df: DataFrame containing all categorized income transactions.
    """
    unassigned_df = df[df["category"] == "INCOME_MISC"]

    sanitized = _sanitize_dataframe(unassigned_df)
    output_file = Path("unassigned_income.csv")
    sanitized.to_csv(
        output_file,
        columns=["day", "month", "year", "amount", "category", "data"],
        index=False,
        encoding="utf-8-sig",
    )
    logger.info(f"[EXPORT] Unassigned income saved to {output_file}")
