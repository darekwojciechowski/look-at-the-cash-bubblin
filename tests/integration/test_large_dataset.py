"""Integration test for processing large (1000-row) datasets."""

from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_core import clean_descriptions, process_dataframe
from data_processing.data_imports import read_transaction_csv


@pytest.mark.integration
@pytest.mark.slow
class TestLargeDatasetProcessing:
    """Integration tests with larger datasets."""

    def test_processing_large_dataset(self, test_data_dir: Path, mocker: MockerFixture) -> None:
        """Test processing a larger dataset (1000+ transactions).

        Given: a CSV file with 1000 transaction rows saved to disk
        When:  read → clean → process is executed with a MISC-returning mock
        Then:  the processed DataFrame contains 1000 rows all categorised as MISC
        """
        # Arrange
        large_df = pd.DataFrame({
            "data": [f"transaction {i}" for i in range(1000)],
            "price": [f"-{i % 100 + 10}.0" for i in range(1000)],
            "month": [i % 12 + 1 for i in range(1000)],
            "year": [2023] * 1000,
        })

        # Save to file
        input_file = test_data_dir / "large_transactions.csv"
        large_df.to_csv(input_file, index=False)

        # Act
        df = read_transaction_csv(str(input_file), "utf-8")
        assert len(df) == 1000

        cleaned_df = clean_descriptions(df)
        assert len(cleaned_df) == 1000

        # Mock mappings — use a callable so .map() receives a function,
        # returning "MISC" for every description (matching real fallback behaviour).
        mocker.patch("data_processing.data_core.mappings", lambda _data: "MISC")

        processed_df = process_dataframe(cleaned_df)

        # Assert
        # All should be MISC since no descriptions match a real keyword
        assert len(processed_df) == 1000
        assert (processed_df["category"] == "MISC").all()
