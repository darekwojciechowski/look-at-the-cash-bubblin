"""Integration test for main() entry-point with real CSV file I/O."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from main import main


@pytest.mark.integration
class TestMainWorkflowIntegration:
    """Integration tests for main() with real file I/O."""

    def test_main_workflow_with_real_csv(self, tmp_path: Path, mocker: MockerFixture) -> None:
        """End-to-end test: main() reads a real IPKO CSV file without mocking I/O.

        Given: a real cp1250-encoded IPKO CSV file with two transactions
        When:  main() is called with the file path patched and exports mocked
        Then:  both export functions are called and the processed DataFrame is non-empty with a category column
        """
        # Arrange
        csv_file = tmp_path / "demo_ipko.csv"
        # IPKO export format: 9 unnamed columns, no header
        csv_file.write_text(
            "2024-01-15,PLN,purchase,-50.0,PLN,orlen fuel station,,orlen,,\n"
            "2024-01-16,PLN,purchase,-15.0,PLN,starbucks coffee,,starbucks,,\n",
            encoding="cp1250",
        )

        mocker.patch("main.CSV_INPUT_FILE", csv_file)
        mock_export_misc = mocker.patch("main.export_misc_transactions")
        mock_export_cleaned = mocker.patch("main.export_cleaned_data")

        # Act
        main()

        # Assert
        mock_export_misc.assert_called_once()
        mock_export_cleaned.assert_called_once()
        processed_df = mock_export_cleaned.call_args[0][0]
        assert not processed_df.empty
        assert "category" in processed_df.columns
