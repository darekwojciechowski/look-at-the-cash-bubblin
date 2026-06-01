"""CSV export functions for processed and unassigned transactions."""

import errno
import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from config.paths import (
    GOOGLE_SHEETS_EXPENSES_PATH,
    GOOGLE_SHEETS_INCOME_PATH,
    PROCESSED_INCOME_PATH,
    PROCESSED_TRANSACTIONS_PATH,
    UNASSIGNED_INCOME_PATH,
    UNASSIGNED_TRANSACTIONS_PATH,
)
from data_processing.expense import CATEGORY_DISPLAY
from data_processing.location_processor import (
    create_google_maps_link,
    extract_location_from_data,
)

# Characters that trigger formula execution in Google Sheets / Excel when at the
# start of a cell value. Prefix them with a single quote to neutralise the risk.
_FORMULA_INJECTION_CHARS: frozenset[str] = frozenset("=+-@\t\r")

_GOOGLE_SHEETS_COLUMNS: list[str] = ["Txn_Id", "Day", "Month", "Year", "Item", "Category", "Amount", "Importance"]
_CLEANED_COLUMNS: list[str] = ["txn_id", "day", "month", "year", "category", "amount"]
_UNASSIGNED_EXPENSE_COLUMNS: list[str] = [
    "txn_id",
    "day",
    "month",
    "year",
    "amount",
    "category",
    "data",
    "extracted_location",
    "google_maps_link",
]
_UNASSIGNED_INCOME_COLUMNS: list[str] = ["txn_id", "day", "month", "year", "amount", "category", "data"]


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


def _prepare_for_export(df: pd.DataFrame, *, ensure_txn_id: bool = True) -> pd.DataFrame:
    """Return a sanitized copy of *df*, optionally backfilling an empty txn_id column."""
    if ensure_txn_id and "txn_id" not in df.columns:
        df = df.copy()
        df["txn_id"] = ""
    return _sanitize_dataframe(df)


def _write_google_sheets_csv(output_df: pd.DataFrame, output_path: Path) -> Path:
    """Write *output_df* as a tab-separated Google Sheets export.

    Sanitizes cells against formula injection, writes with a tab separator,
    and restricts file permissions to owner-only read/write on POSIX
    (PII protection).

    On POSIX, uses ``os.open(..., O_NOFOLLOW)`` where available to reject
    symlinks atomically at open-time and close the symlink race window.
    """
    output_df = _sanitize_dataframe(output_df)

    if sys.platform == "win32":
        # Windows fallback: no O_NOFOLLOW equivalent in the stdlib open path.
        if output_path.is_symlink():
            raise OSError(f"Refusing to write to symlink: {output_path}")
        output_df.to_csv(output_path, sep="\t", index=False)
        return output_path

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        fd = os.open(output_path, flags, 0o600)
    except OSError as err:
        if err.errno == errno.ELOOP:
            raise OSError(f"Refusing to write to symlink: {output_path}") from err
        raise

    with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
        os.fchmod(fh.fileno(), 0o600)
        output_df.to_csv(fh, sep="\t", index=False)

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

    sanitized = _prepare_for_export(df, ensure_txn_id="txn_id" in columns)
    sanitized.to_csv(output_path, columns=columns, index=False, encoding="utf-8-sig")


def _build_expense_row(row: Any) -> dict[str, object]:
    """Build one Google Sheets export row from an expense DataFrame row."""
    cat, imp = CATEGORY_DISPLAY[str(row.category)]
    return {
        "Txn_Id": getattr(row, "txn_id", ""),
        "Day": row.day,
        "Month": row.month,
        "Year": row.year,
        "Item": row.category,
        "Category": cat.value,
        "Amount": str(row.amount).replace(".", ","),
        "Importance": imp.value,
    }


def _build_income_row(row: Any) -> dict[str, object]:
    """Build one Google Sheets export row from an income DataFrame row."""
    return {
        "Txn_Id": getattr(row, "txn_id", ""),
        "Day": row.day,
        "Month": row.month,
        "Year": row.year,
        "Item": row.category,
        "Category": row.category,
        "Amount": str(row.amount).replace(".", ","),
        "Importance": "",
    }


def _export_google_sheets(
    df: pd.DataFrame,
    path: Path,
    row_builder: Callable[[Any], dict[str, object]],
) -> Path:
    """Shared Google Sheets export template parameterised by *row_builder*."""
    logger.info("Exporting {} rows for Google Sheets", len(df))
    rows = [row_builder(row) for row in df.itertuples(index=False)]
    output_df = pd.DataFrame(rows, columns=_GOOGLE_SHEETS_COLUMNS)
    output_file = _write_google_sheets_csv(output_df, path)
    logger.info(f"Exported data for Google Sheets to '{output_file}'.")
    return output_file


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
    return _export_google_sheets(processed_df, GOOGLE_SHEETS_EXPENSES_PATH, _build_expense_row)


def export_misc_transactions(df: pd.DataFrame) -> None:
    """Export uncategorized (MISC) transactions to CSV.

    Args:
        df: DataFrame containing all categorized transactions.
    """
    misc_df = df[df["category"].str.contains("MISC", na=False)]
    export_unassigned_transactions_to_csv(misc_df)
    logger.info("[EXPORT] Unassigned (MISC) transactions exported")


def export_cleaned_data(df: pd.DataFrame, output_file: Path | str = PROCESSED_TRANSACTIONS_PATH) -> None:
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

    df_copy = _prepare_for_export(df_copy)
    output_file = UNASSIGNED_TRANSACTIONS_PATH
    # Keep BOM for Windows Excel when exporting unassigned transactions.
    # Explicit columns= guarantees txn_id is first and the header is stable
    # against any DataFrame column-order drift.
    df_copy.to_csv(output_file, columns=_UNASSIGNED_EXPENSE_COLUMNS, index=False, encoding="utf-8-sig")
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
    return _export_google_sheets(income_df, GOOGLE_SHEETS_INCOME_PATH, _build_income_row)


def export_cleaned_income_data(df: pd.DataFrame, output_file: Path | str = PROCESSED_INCOME_PATH) -> None:
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
    sanitized = _prepare_for_export(unassigned_df)
    output_file = UNASSIGNED_INCOME_PATH
    sanitized.to_csv(
        output_file,
        columns=_UNASSIGNED_INCOME_COLUMNS,
        index=False,
        encoding="utf-8-sig",
    )
    logger.info(f"[EXPORT] Unassigned income saved to {output_file}")
