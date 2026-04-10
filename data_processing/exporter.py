"""CSV export functions for processed and unassigned transactions."""

import csv
from pathlib import Path

import pandas as pd
from loguru import logger

from data_processing.data_loader import Expense
from data_processing.location_processor import (
    create_google_maps_link,
    extract_location_from_data,
)


def export_for_google_sheets(processed_df: pd.DataFrame) -> None:
    """Write the processed DataFrame to ``for_google_spreadsheet.csv``.

    Logs the full DataFrame before writing so the output is visible in
    the run log. The file uses the default pandas encoding in tests and
    ``utf-8-sig`` in production.

    Args:
        processed_df: Processed transaction DataFrame to export.
    """
    # Example logic for preparing data for Google Sheets
    google_sheets_df = processed_df.copy()
    # Add any transformations or filtering here if needed

    # Log the final DataFrame to the console (only once)
    logger.info("Final DataFrame for Google Sheets:\n{}", google_sheets_df.to_string())

    # Export the DataFrame to a CSV file
    output_file = Path("for_google_spreadsheet.csv")
    # Let pandas use default encoding in tests; main export uses utf-8-sig
    google_sheets_df.to_csv(output_file, index=False)
    logger.info(f"Exported data for Google Sheets to '{output_file}'.")


def export_misc_transactions(df: pd.DataFrame) -> None:
    """Filter MISC rows and delegate to ``export_unassigned_transactions_to_csv``.

    Args:
        df: DataFrame containing all categorized transactions.
    """
    misc_df = df[df["category"].str.contains("MISC", na=False)]
    export_unassigned_transactions_to_csv(misc_df)
    logger.info("[EXPORT] Unassigned (MISC) transactions exported")


def export_cleaned_data(df: pd.DataFrame, output_file: Path | str = Path("data/processed_transactions.csv")) -> None:
    """Write the ``[month, year, category, price]`` columns to a CSV file.

    Uses ``utf-8-sig`` encoding so the file opens correctly in Windows Excel.

    Args:
        df: Processed transaction DataFrame.
        output_file: Destination path. Defaults to
            ``data/processed_transactions.csv``.
    """
    df.to_csv(
        output_file,
        columns=["month", "year", "category", "price"],
        index=False,
        encoding="utf-8-sig",
    )
    logger.info(f"[EXPORT] Cleaned data saved to {output_file}")


def export_unassigned_transactions_to_csv(df: pd.DataFrame) -> None:
    """Write MISC transactions to ``unassigned_transactions.csv`` with location columns.

    Adds ``extracted_location`` and ``google_maps_link`` columns before
    writing. Uses ``utf-8-sig`` encoding for Windows Excel compatibility.

    Args:
        df: DataFrame containing uncategorized (MISC) transactions.
    """
    # Add location processing only for unassigned transactions
    df_copy = df.copy()
    df_copy["extracted_location"] = df_copy["data"].apply(extract_location_from_data)
    df_copy["google_maps_link"] = df_copy["extracted_location"].apply(create_google_maps_link)

    output_file = Path("unassigned_transactions.csv")
    # Keep BOM for Windows Excel when exporting unassigned transactions
    df_copy.to_csv(output_file, index=False, encoding="utf-8-sig")
    logger.info(f"[EXPORT] Unassigned transactions with location data saved to {output_file}")


def get_data(path: Path = Path("data/processed_transactions.csv")) -> list[Expense]:
    """Read a processed transactions CSV and return a list of Expense objects.

    Skips the header row. Columns must be in the order
    ``month, year, category, price``.

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
