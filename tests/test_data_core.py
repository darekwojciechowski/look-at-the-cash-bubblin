"""
Tests for data_processing.data_core module.
Comprehensive testing of data cleaning and processing functionality.
"""


import pytest
import pandas as pd
import numpy as np
from pytest_mock import MockerFixture
from data_processing.data_core import clean_date, process_dataframe


@pytest.fixture
def raw_transaction_data() -> pd.DataFrame:
    """Fixture with realistic raw transaction descriptions."""
    return pd.DataFrame({
        "data": [
            "purchase in terminal - mobile code",
            "web payment - mobile code",
            "orlen",
            "starbucks",
            "piotrkowska 157a"
        ],
        "price": ["-50.0", "-20.0", "-100.0", "-15.0", "200.0"],
        "month": [1, 1, 1, 1, 1],
        "year": [2023, 2023, 2023, 2023, 2023]
    })


@pytest.fixture
def expected_cleaned_data() -> pd.DataFrame:
    """Expected output after cleaning transaction descriptions."""
    return pd.DataFrame({
        "data": [
            "terminal purchase",
            "web payment",
            "Orlen gas station",
            "Starbucks coffee shop",
            "Biedronka - Piotrkowska 157a"
        ],
        "price": ["-50.0", "-20.0", "-100.0", "-15.0", "200.0"],
        "month": [1, 1, 1, 1, 1],
        "year": [2023, 2023, 2023, 2023, 2023]
    })


@pytest.fixture
def mappings_mock() -> dict[str, str]:
    """Fixture providing mock category mappings."""
    return {
        "terminal purchase": "SHOPPING",
        "web payment": "ONLINE_PAYMENT",
        "Orlen gas station": "FUEL",
        "Starbucks coffee shop": "COFFEE",
        "Biedronka - Piotrkowska 157a": "GROCERIES"
    }


@pytest.mark.unit
class TestCleanDate:
    """Test suite for transaction description cleaning."""

    def test_clean_date_all_replacements(
        self,
        raw_transaction_data: pd.DataFrame,
        expected_cleaned_data: pd.DataFrame
    ) -> None:
        """Verify all replacement patterns work correctly."""
        result = clean_date(raw_transaction_data)

        pd.testing.assert_frame_equal(
            result,
            expected_cleaned_data,
            check_dtype=False
        )

    @pytest.mark.parametrize("input_text,expected_output", [
        ("purchase in terminal - mobile code", "terminal purchase"),
        ("web payment - mobile code", "web payment"),
        ("orlen", "Orlen gas station"),
        ("starbucks", "Starbucks coffee shop"),
        ("piotrkowska 157a", "Biedronka - Piotrkowska 157a"),
    ])
    def test_clean_date_individual_replacements(
        self,
        input_text: str,
        expected_output: str
    ) -> None:
        """Test individual replacement patterns."""
        df = pd.DataFrame({
            "data": [input_text],
            "price": ["-10.0"],
            "month": [1],
            "year": [2023]
        })

        result = clean_date(df)
        assert result["data"].iloc[0] == expected_output

    def test_clean_date_preserves_other_columns(
        self,
        raw_transaction_data: pd.DataFrame
    ) -> None:
        """Ensure clean_date doesn't modify non-data columns."""
        result = clean_date(raw_transaction_data)

        pd.testing.assert_series_equal(
            result["price"],
            raw_transaction_data["price"],
            check_dtype=False
        )
        pd.testing.assert_series_equal(
            result["month"],
            raw_transaction_data["month"],
            check_dtype=False
        )
        pd.testing.assert_series_equal(
            result["year"],
            raw_transaction_data["year"],
            check_dtype=False
        )

    def test_clean_date_with_empty_dataframe(self) -> None:
        """Test clean_date with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["data", "price", "month", "year"])
        result = clean_date(empty_df)

        assert result.empty
        assert list(result.columns) == ["data", "price", "month", "year"]


@pytest.mark.unit
class TestProcessDataframe:
    """Test suite for DataFrame processing and categorization."""

    def test_process_dataframe_complete_workflow(
        self,
        raw_transaction_data: pd.DataFrame,
        mappings_mock: dict[str, str],
        mocker: MockerFixture
    ) -> None:
        """Test complete processing workflow with mock mappings."""
        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        processed_df = process_dataframe(raw_transaction_data)

        # Verify 4 rows after filtering out positive price
        assert len(processed_df) == 4

        # Verify categories assigned correctly
        expected_categories = ["SHOPPING", "ONLINE_PAYMENT", "FUEL", "COFFEE"]
        assert processed_df["category"].tolist() == expected_categories

        # Verify column order
        expected_columns = ["month", "year", "price", "category", "data"]
        assert list(processed_df.columns) == expected_columns

    def test_process_dataframe_filters_positive_prices(
        self,
        raw_transaction_data: pd.DataFrame,
        mappings_mock: dict[str, str],
        mocker: MockerFixture
    ) -> None:
        """Verify positive price transactions are filtered out."""
        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        processed_df = process_dataframe(raw_transaction_data)

        # Verify prices are converted to absolute positive values
        assert all(float(price) > 0 for price in processed_df["price"])
        # Verify original positive price row was filtered out (4 rows remain)
        assert len(processed_df) == 4

    def test_process_dataframe_converts_price_to_absolute(
        self,
        mappings_mock: dict[str, str],
        mocker: MockerFixture
    ) -> None:
        """Test price conversion to absolute values."""
        df = pd.DataFrame({
            "data": ["terminal purchase"],
            "price": ["-50.0"],
            "month": [1],
            "year": [2023]
        })

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(df)

        assert float(result["price"].iloc[0]) == 50.0

    def test_process_dataframe_column_order(
        self,
        raw_transaction_data: pd.DataFrame,
        mappings_mock: dict[str, str],
        mocker: MockerFixture
    ) -> None:
        """Verify column order in processed DataFrame."""
        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(raw_transaction_data)

        expected_columns = ["month", "year", "price", "category", "data"]
        assert list(result.columns) == expected_columns

    def test_process_dataframe_with_empty_dataframe(
        self,
        mappings_mock: dict[str, str],
        mocker: MockerFixture
    ) -> None:
        """Test process_dataframe with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["data", "price", "month", "year"])

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(empty_df)

        assert result.empty
        expected_columns = ["month", "year", "price", "category", "data"]
        assert list(result.columns) == expected_columns

    def test_process_dataframe_with_invalid_columns(
        self,
        mocker: MockerFixture
    ) -> None:
        """Test process_dataframe when required columns are missing."""
        mock_logging_error = mocker.patch("logging.error")
        invalid_df = pd.DataFrame({
            "invalid_column": ["test"],
            "wrong_price": ["invalid_price"],
            "month": [1],
            "year": [2023]
        })

        with pytest.raises(KeyError):
            process_dataframe(invalid_df)

    def test_process_dataframe_handles_mixed_price_formats(
        self,
        mappings_mock: dict[str, str],
        mocker: MockerFixture
    ) -> None:
        """Test processing with various price formats."""
        df = pd.DataFrame({
            "data": ["terminal purchase", "web payment"],
            "price": ["-50", "-20.50"],
            "month": [1, 1],
            "year": [2023, 2023]
        })

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(df)

        assert len(result) == 2
        assert float(result["price"].iloc[0]) == 50.0
        assert float(result["price"].iloc[1]) == 20.50

    @pytest.mark.parametrize("price_value", [
        "-100.0",
        "-0.01",
        "-999.99",
    ])
    def test_process_dataframe_with_various_negative_prices(
        self,
        price_value: str,
        mappings_mock: dict[str, str],
        mocker: MockerFixture
    ) -> None:
        """Test processing with various negative price values."""
        df = pd.DataFrame({
            "data": ["terminal purchase"],
            "price": [price_value],
            "month": [1],
            "year": [2023]
        })

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(df)

        assert len(result) == 1
        assert float(result["price"].iloc[0]) == abs(float(price_value))
