import pytest
from unittest.mock import patch, MagicMock
from main import main


@patch("main.setup_logging")
@patch("main.read_transaction_csv")
@patch("main.process_dataframe")
@patch("main.export_misc_transactions")
@patch("main.pd.DataFrame.to_csv")
def test_main_workflow(mock_to_csv, mock_export_misc, mock_process_df, mock_read_csv, mock_setup_logging):
    """
    Tests the main function workflow to ensure:
    - Logging is set up correctly.
    - Transactions are read from the correct CSV file.
    - The DataFrame is processed as expected.
    - Miscellaneous transactions are exported correctly.
    - The processed DataFrame is exported to a CSV file with the correct structure.
    """
    # Mock the behavior of the imported functions
    mock_read_csv.return_value = MagicMock()  # Mocked DataFrame
    mock_processed_df = MagicMock()  # Mocked processed DataFrame
    mock_process_df.return_value = mock_processed_df

    # Add a to_csv method to the mocked processed DataFrame
    mock_processed_df.to_csv = mock_to_csv

    # Run the main function
    main()

    # Verify that setup_logging was called
    mock_setup_logging.assert_called_once()

    # Verify that read_transaction_csv was called with the correct arguments
    mock_read_csv.assert_called_once_with('data/demo_ipko.csv', 'iso_8859_1')

    # Verify that process_dataframe was called with the DataFrame returned by read_transaction_csv
    mock_process_df.assert_called_once_with(mock_read_csv.return_value)

    # Verify that export_misc_transactions was called with the processed DataFrame
    mock_export_misc.assert_called_once_with(mock_process_df.return_value)

    # Verify that the processed DataFrame was exported to CSV
    mock_to_csv.assert_called_once_with(
        'data/processed_transactions.csv',
        columns=['month', 'year', 'category', 'price'],
        index=False
    )
