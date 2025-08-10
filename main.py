import logging
import pandas as pd
from data_processing.data_imports import read_transaction_csv, ipko_import
from data_processing.data_core import process_dataframe
from data_processing.exporter import export_misc_transactions
from config.logging_setup import setup_logging

# Constants
CSV_INPUT_FILE = 'data/demo_ipko.csv'
CSV_ENCODING = 'cp1250'
CSV_OUT_FILE = 'data/processed_transactions.csv'


def main():
    """Main function to orchestrate the CSV import and processing workflow."""
    setup_logging()
    logging.info("Starting CSV import and processing workflow.")

    # Read and process the CSV file
    df = read_transaction_csv(CSV_INPUT_FILE, CSV_ENCODING)
    df = ipko_import(df)
    processed_df = process_dataframe(df)

    # Print processed DataFrame to terminal (only once)
    logging.info("Processed DataFrame preview:")

    # Export Misc transactions for manual review
    export_misc_transactions(processed_df)

    # Export cleaned data to CSV
    processed_df.to_csv(
        CSV_OUT_FILE,
        columns=['month', 'year', 'category', 'price'],
        index=False,
        encoding='utf-8-sig',
    )
    logging.info(f"Exported cleaned data to {CSV_OUT_FILE}")


if __name__ == "__main__":
    main()
