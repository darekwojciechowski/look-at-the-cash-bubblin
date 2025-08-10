import pytest
from unittest.mock import patch, MagicMock
from main import main


@patch("main.setup_logging")
@patch("main.read_transaction_csv")
@patch("main.ipko_import")
@patch("main.process_dataframe")
@patch("main.export_misc_transactions")
@patch("main.pd.DataFrame.to_csv")
def test_main_workflow(mock_to_csv, mock_export_misc, mock_process_df, mock_ipko_import, mock_read_csv, mock_setup_logging):
    """
    Tests the main function workflow to ensure:
    - Logging is set up correctly.
    - Transactions are read from the correct CSV file.
    - The DataFrame is processed as expected.
    - Miscellaneous transactions are exported correctly.
    - The processed DataFrame is exported to a CSV file with the correct structure.
    """
    # Create proper DataFrame mocks instead of MagicMock
    import pandas as pd

    raw_df = pd.DataFrame({
        "data": ["test1", "test2"],
        "price": [100, 200],
        "month": [1, 1],
        "year": [2023, 2023]
    })

    processed_df = pd.DataFrame({
        "month": [1, 1],
        "year": [2023, 2023],
        "price": [100, 200],
        "category": ["Food", "Transport"],
        "data": ["test1", "test2"]
    })

    # Mock the behavior of the imported functions
    mock_read_csv.return_value = raw_df
    # ipko_import returns the same format we need
    mock_ipko_import.return_value = raw_df
    mock_process_df.return_value = processed_df

    # Run the main function
    main()

    # Verify that setup_logging was called
    mock_setup_logging.assert_called_once()

    # Verify that read_transaction_csv was called with the correct arguments
    mock_read_csv.assert_called_once_with('data/demo_ipko.csv', 'cp1250')

    # Verify that ipko_import was called with the DataFrame returned by read_transaction_csv
    mock_ipko_import.assert_called_once_with(raw_df)

    # Verify that process_dataframe was called with the DataFrame returned by ipko_import
    mock_process_df.assert_called_once_with(raw_df)

    # Verify that export_misc_transactions was called with the processed DataFrame
    mock_export_misc.assert_called_once_with(processed_df)

    # Verify that the processed DataFrame was exported to CSV
    mock_to_csv.assert_called_once_with(
        'data/processed_transactions.csv',
        columns=['month', 'year', 'category', 'price'],
        index=False,
        encoding='utf-8-sig'
    )
