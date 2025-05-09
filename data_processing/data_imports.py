import logging
import pandas as pd


def ipko_import(df):
    """
    Process the DataFrame for IPKO transactions (standard format).

    Parameters:
    df (pandas.DataFrame): The input DataFrame containing transaction data.

    Returns:
    pandas.DataFrame: The processed DataFrame with cleaned and transformed data.
    """
    # Rename columns for consistency
    df.rename(columns={
        df.columns[0]: 'transaction_date',
        df.columns[1]: 'currency_data',
        df.columns[2]: 'transaction_type',
        df.columns[3]: 'price',
        df.columns[4]: 'currency',
        df.columns[5]: 'transaction_description',
        df.columns[6]: 'unnamed_6',
        df.columns[7]: 'data',
        df.columns[8]: 'unnamed_8'
    }, inplace=True)

    # Convert 'transaction_date' to datetime format
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Extract month and year from 'transaction_date'
    df['month'] = df['transaction_date'].dt.month
    df['year'] = df['transaction_date'].dt.year

    # Convert specified columns to lowercase safely
    columns_to_lower = ['data', 'transaction_type',
                        'transaction_description', 'unnamed_6', 'unnamed_8']
    for col in columns_to_lower:
        df[col] = df[col].astype(str).str.lower()

    # Combine multiple columns into a single 'data' column
    df['data'] = df[['transaction_type', 'transaction_description',
                     'unnamed_6', 'unnamed_8', 'data']].apply('//'.join, axis=1)

    # Drop unnecessary columns
    columns_to_drop = ['transaction_date', 'currency_data', 'currency',
                       'transaction_type', 'unnamed_6', 'unnamed_8', 'transaction_description']
    df.drop(columns=columns_to_drop, inplace=True)

    return df


def read_transaction_csv(file_path, encoding):
    """
    Read the transaction CSV file into a DataFrame.

    Parameters:
    file_path (str): Path to the CSV file.
    encoding (str): Encoding of the CSV file.

    Returns:
    pandas.DataFrame: The loaded DataFrame.
    """
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip', encoding=encoding)
        logging.info(f"Successfully loaded CSV file: {file_path}")
        return df
    except Exception as e:
        logging.error(f"Failed to read CSV file: {file_path}. Error: {e}")
        raise
