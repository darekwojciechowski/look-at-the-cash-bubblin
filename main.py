"""Entry point: orchestrates the IPKO CSV import, transformation, and export pipeline."""

from pathlib import Path

from loguru import logger

from config.logging_setup import log_dataframe_preview, setup_logging
from config.paths import PROCESSED_INCOME_PATH, PROCESSED_TRANSACTIONS_PATH
from data_processing.data_core import process_dataframe, process_income_dataframe
from data_processing.data_imports import ipko_import, read_transaction_csv
from data_processing.exporter import (
    export_cleaned_data,
    export_cleaned_income_data,
    export_for_google_sheets,
    export_income_for_google_sheets,
    export_misc_transactions,
    export_unassigned_income,
)
from data_processing.transaction_id import assign_txn_ids

# Constants
CSV_INPUT_FILE: Path = Path("data/demo_ipko.csv")
CSV_ENCODING: str = "cp1250"
CSV_OUT_FILE: Path = PROCESSED_TRANSACTIONS_PATH
CSV_INCOME_OUT_FILE: Path = PROCESSED_INCOME_PATH


def main() -> None:
    """Run the full transaction processing pipeline.

    Reads the IPKO CSV export, normalizes and categorizes transactions,
    logs a preview, and writes six output files in parallel expense and
    income tracks:

    Expenses:
    - ``google_sheets_expenses.csv`` — full expense export for Google Sheets
    - ``data/processed_transactions.csv`` — all categorized expenses
    - ``unassigned_transactions.csv`` — MISC expense rows with Google Maps links

    Income:
    - ``google_sheets_income.csv`` — full income export for Google Sheets
    - ``data/processed_income.csv`` — all categorized income
    - ``unassigned_income.csv`` — INCOME_MISC rows for manual review
    """
    setup_logging()
    logger.info("[START] CSV import and processing workflow")

    # Read and process the CSV file
    df = read_transaction_csv(CSV_INPUT_FILE, CSV_ENCODING)
    df = ipko_import(df)
    df = assign_txn_ids(df)
    processed_df = process_dataframe(df)
    income_df = process_income_dataframe(df)

    # Log a preview of the processed DataFrame
    log_dataframe_preview(processed_df)

    # Expense exports
    export_misc_transactions(processed_df)
    export_for_google_sheets(processed_df)
    export_cleaned_data(processed_df, CSV_OUT_FILE)

    # Income exports
    export_unassigned_income(income_df)
    export_income_for_google_sheets(income_df)
    export_cleaned_income_data(income_df, CSV_INCOME_OUT_FILE)


if __name__ == "__main__":  # pragma: no cover
    main()
