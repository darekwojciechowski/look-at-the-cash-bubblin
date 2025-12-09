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
    Read the transaction CSV file into a DataFrame with smart encoding handling.

    Parameters:
    file_path (str): Path to the CSV file.
    encoding (str): Primary encoding to try (if sensible).

    Returns:
    pandas.DataFrame: The loaded DataFrame with properly decoded text.
    """
    # Prefer encodings that are commonly used for Polish text first.
    preferred_pl_encodings = ['utf-8', 'utf-8-sig', 'cp1250', 'iso-8859-2']
    # keep latin1 last as it rarely fails but can mojibake
    secondary_encodings = ['cp1252', 'iso-8859-1']

    # If caller passes latin-1/iso-8859-1, deprioritize it to avoid silent mojibake.
    enc_lower = (encoding or '').replace('_', '-').lower()
    is_latin1 = enc_lower in {'iso-8859-1', 'latin1', 'latin-1', 'iso_8859_1'}

    if encoding and not is_latin1:
        # Respect caller-provided encoding by trying it first
        encodings_to_try = [
            encoding] + [e for e in preferred_pl_encodings + secondary_encodings if e != encoding]
    else:
        # Use a safe default order for Polish data
        encodings_to_try = preferred_pl_encodings + secondary_encodings

    try:
        for enc in encodings_to_try:
            try:
                df = pd.read_csv(file_path, on_bad_lines='skip', encoding=enc)
                logging.info(
                    f"Successfully loaded CSV file: {file_path} with encoding: {enc}")
                return df
            except (UnicodeDecodeError, UnicodeError):
                logging.debug(f"Failed to read with encoding: {enc}")
                continue
            except FileNotFoundError as e:
                # Explicit log message expected by tests and users
                logging.error(
                    f"Failed to read CSV file: {file_path}. Error: {str(e)}")
                raise
            except Exception as e:
                # If it's clearly encoding-related, try next; otherwise, log and re-raise
                if 'codec' in str(e).lower() or 'encoding' in str(e).lower():
                    logging.warning(f"Encoding error with {enc}: {e}")
                    continue
                else:
                    logging.error(
                        f"Failed to read CSV file: {file_path}. Error: {str(e)}")
                    raise
    finally:
        # For visibility, log the attempted encodings if we end up failing completely
        logging.debug(f"Tried encodings in order: {encodings_to_try}")

    # If all encodings fail, raise an error
    raise ValueError(
        f"Could not read {file_path} with any of the tried encodings: {encodings_to_try}")
