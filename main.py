from pathlib import Path
from loguru import logger
import pandas as pd
from data_processing.data_imports import read_transaction_csv, ipko_import
from data_processing.data_core import process_dataframe
from data_processing.exporter import export_misc_transactions, export_cleaned_data
from config.logging_setup import setup_logging

# Constants
CSV_INPUT_FILE: Path = Path('data/demo_ipko.csv')
CSV_ENCODING: str = 'cp1250'
CSV_OUT_FILE: Path = Path('data/processed_transactions.csv')


def main() -> None:
    """Main function to orchestrate the CSV import and processing workflow."""
    setup_logging()
    logger.info("[START] CSV import and processing workflow")

    # Read and process the CSV file
    df = read_transaction_csv(CSV_INPUT_FILE, CSV_ENCODING)
    df = ipko_import(df)
    processed_df = process_dataframe(df)

    # Print processed DataFrame to terminal (only once)
    logger.info("[DATA] Processed DataFrame preview:")

    # Export Misc transactions for manual review
    export_misc_transactions(processed_df)

    # Export cleaned data to CSV
    export_cleaned_data(processed_df, CSV_OUT_FILE)


if __name__ == "__main__":
    main()
