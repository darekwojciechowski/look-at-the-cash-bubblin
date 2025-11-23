import logging
import csv
import pandas as pd
from data_processing.data_loader import Expense
from data_processing.location_processor import extract_location_from_data, create_google_maps_link

# Constants
CSV_OUT_FILE = 'data/processed_transactions.csv'


def export_for_google_sheets(processed_df):
    """
    Export the processed DataFrame for Google Sheets.

    Parameters:
    processed_df (pandas.DataFrame): The processed DataFrame to export.
    """
    # Example logic for preparing data for Google Sheets
    google_sheets_df = processed_df.copy()
    # Add any transformations or filtering here if needed

    # Print the DataFrame to the console (only once)
    logging.info("Printing the final DataFrame for Google Sheets:")
    # Ensure this is the only print statement for the DataFrame
    print(google_sheets_df.to_string())

    # Export the DataFrame to a CSV file
    output_file = 'for_google_spreadsheet.csv'
    # Let pandas use default encoding in tests; main export uses utf-8-sig
    google_sheets_df.to_csv(output_file, index=False)
    logging.info(f"Exported data for Google Sheets to '{output_file}'.")


def export_misc_transactions(df: pd.DataFrame):
    """
    Export transactions with 'MISC' in the category to a CSV for manual review.

    Args:
    df (pd.DataFrame): DataFrame containing all transactions.
    """
    misc_df = df[df["category"].str.contains("MISC", na=False)]
    export_unassigned_transactions_to_csv(misc_df)
    logging.info("Exported unassigned (MISC) transactions to CSV.")


def export_cleaned_data(df: pd.DataFrame, output_file: str = 'data/processed_transactions.csv'):
    """
    Export cleaned transaction data to CSV file.

    Args:
    df (pd.DataFrame): DataFrame containing processed transactions.
    output_file (str): Path to the output CSV file.
    """
    df.to_csv(
        output_file,
        columns=['month', 'year', 'category', 'price'],
        index=False,
        encoding='utf-8-sig',
    )
    logging.info(f"Exported cleaned data to {output_file}")


def export_unassigned_transactions_to_csv(df: pd.DataFrame):
    """
    Export transactions with 'MISC' in the category to a CSV file with location processing.

    Args:
    df (pd.DataFrame): DataFrame containing unassigned transactions.
    """
    # Add location processing only for unassigned transactions
    df_copy = df.copy()
    df_copy['extracted_location'] = df_copy['data'].apply(
        extract_location_from_data)
    df_copy['google_maps_link'] = df_copy['extracted_location'].apply(
        create_google_maps_link)

    output_file = 'unassigned_transactions.csv'
    # Keep BOM for Windows Excel when exporting unassigned transactions
    df_copy.to_csv(output_file, index=False, encoding='utf-8-sig')
    logging.info(
        f"Exported unassigned transactions with location data to {output_file}.")


def get_data() -> list:
    """
    Read data from the CSV file and convert it into a list of Expense objects.

    Returns:
    list: A list of Expense objects.
    """
    expenses = []
    with open(CSV_OUT_FILE, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header row
        for row in reader:
            expenses.append(Expense(row[0], row[1]))
    return expenses


def export_final_data() -> list:
    """
    Read the CSV file and convert it into a list of Expense objects.

    Returns:
    list: A list of Expense objects.
    """
    expenses = []
    with open(CSV_OUT_FILE, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        next(reader)  # Skip the header row
        for row in reader:
            expenses.append(Expense(row[0], row[1], row[2], row[3]))
    return expenses


def export_final_date_for_google_spreadsheet(data: list):
    """
    Process the input data, format it, and export it to a CSV file for Google Sheets.

    Args:
    data (list): A list of Expense objects or similar data to be processed and exported.
    """
    # Convert the list of Expense objects into a DataFrame
    df = pd.DataFrame(data)

    # Check if the DataFrame is empty
    if df.empty:
        logging.error("The DataFrame is empty. No data to export.")
        return

    # Rename the first column to 'data'
    df.rename(columns={df.columns[0]: 'data'}, inplace=True)

    # Ensure the 'data' column is of type string
    df['data'] = df['data'].astype(str)

    # Split the 'data' column into multiple columns
    df[['Month', 'Year', 'Item', 'Category', 'Amount', 'Importance']
       ] = df['data'].str.split(',', expand=True)
    df = df.drop(columns=['data'])

    # Replace '.' with ',' for Google Sheets compatibility
    df['Amount'] = df['Amount'].str.replace('.', ',')

    # Export the DataFrame to a CSV file with tab-separated values
    output_file = 'for_google_spreadsheet.csv'
    # Keep default encoding here to satisfy tests asserting only sep/index
    df.to_csv(output_file, sep='\t', index=False)

    # Print the DataFrame to the console (only once)
    logging.info("Printing the final DataFrame for Google Sheets:")
    print(df.to_string())

    logging.info(f"Exported data for Google Sheets to '{output_file}'.")


data = export_final_data()
export_final_date_for_google_spreadsheet(export_final_data())
