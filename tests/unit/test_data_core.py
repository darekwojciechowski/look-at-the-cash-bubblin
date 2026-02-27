"""
Tests for data_processing.data_core module.
Comprehensive testing of data cleaning and processing functionality.
"""

from collections.abc import Callable

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_core import clean_descriptions, process_dataframe


@pytest.mark.unit
class TestCleanDescriptions:
    """Test suite for transaction description cleaning."""

    def test_clean_descriptions_all_replacements(
        self, sample_raw_dataframe: pd.DataFrame, expected_cleaned_data: pd.DataFrame
    ) -> None:
        """Verify all replacement patterns work correctly."""
        result = clean_descriptions(sample_raw_dataframe)

        pd.testing.assert_frame_equal(result, expected_cleaned_data, check_dtype=False)

    @pytest.mark.parametrize(
        "input_text,expected_output",
        [
            ("purchase in terminal - mobile code", "terminal purchase"),
            ("web payment - mobile code", "web payment"),
            ("orlen", "Orlen gas station"),
            ("starbucks", "Starbucks coffee shop"),
            ("piotrkowska 157a", "Biedronka - Piotrkowska 157a"),
        ],
    )
    def test_clean_descriptions_individual_replacements(self, input_text: str, expected_output: str) -> None:
        """Test individual replacement patterns."""
        df = pd.DataFrame({"data": [input_text], "price": ["-10.0"], "month": [1], "year": [2023]})

        result = clean_descriptions(df)
        assert result["data"].iloc[0] == expected_output

    def test_clean_descriptions_preserves_other_columns(self, sample_raw_dataframe: pd.DataFrame) -> None:
        """Ensure clean_descriptions doesn't modify non-data columns."""
        result = clean_descriptions(sample_raw_dataframe)

        pd.testing.assert_series_equal(result["price"], sample_raw_dataframe["price"], check_dtype=False)
        pd.testing.assert_series_equal(result["month"], sample_raw_dataframe["month"], check_dtype=False)
        pd.testing.assert_series_equal(result["year"], sample_raw_dataframe["year"], check_dtype=False)

    def test_clean_descriptions_with_empty_dataframe(self) -> None:
        """Test clean_descriptions with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["data", "price", "month", "year"])
        result = clean_descriptions(empty_df)

        assert result.empty
        assert list(result.columns) == ["data", "price", "month", "year"]

    def test_clean_descriptions_with_custom_replacements(self) -> None:
        """Test that a custom replacements dict is honoured (OCP injection point).

        clean_descriptions accepts an optional ``replacements`` parameter so
        callers can support other bank formats without touching the function
        body.  This test verifies that the injected dict is applied instead of
        the default IPKO replacement map.
        """
        # Arrange — custom bank format with different description conventions
        custom_replacements = {
            "pkt zakup": "card purchase",
            "przel wychodzacy": "outgoing transfer",
        }
        df = pd.DataFrame(
            {
                "data": ["pkt zakup sklep", "przel wychodzacy firma", "orlen"],
                "price": ["-30.0", "-200.0", "-100.0"],
                "month": [1, 1, 1],
                "year": [2023, 2023, 2023],
            }
        )

        # Act
        result = clean_descriptions(df, replacements=custom_replacements)

        # Assert — custom replacements applied, default IPKO map NOT applied
        assert result["data"].iloc[0] == "card purchase sklep"
        assert result["data"].iloc[1] == "outgoing transfer firma"
        # "orlen" stays unchanged — it's not in the custom dict
        assert result["data"].iloc[2] == "orlen"

    @pytest.mark.parametrize(
        "replacements,input_text,expected",
        [
            ({"hello": "hi"}, "hello world", "hi world"),
            ({"foo": "bar", "baz": "qux"}, "foo and baz", "bar and qux"),
            ({}, "unchanged text", "unchanged text"),
        ],
    )
    def test_clean_descriptions_custom_replacements_parametrized(
        self, replacements: dict[str, str], input_text: str, expected: str
    ) -> None:
        """Parametrized checks that custom replacement dicts are applied correctly."""
        df = pd.DataFrame({"data": [input_text], "price": ["-10.0"], "month": [1], "year": [2023]})
        result = clean_descriptions(df, replacements=replacements)
        assert result["data"].iloc[0] == expected


@pytest.mark.unit
class TestProcessDataframe:
    """Test suite for DataFrame processing and categorization."""

    def test_process_dataframe_complete_workflow(
        self,
        sample_raw_dataframe: pd.DataFrame,
        mappings_mock: Callable[[str], str],
        mocker: MockerFixture,
    ) -> None:
        """Test complete processing workflow with mock mappings."""
        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        processed_df = process_dataframe(sample_raw_dataframe)

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
        sample_raw_dataframe: pd.DataFrame,
        mappings_mock: Callable[[str], str],
        mocker: MockerFixture,
    ) -> None:
        """Verify positive price transactions are filtered out."""
        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        processed_df = process_dataframe(sample_raw_dataframe)

        # Verify prices are converted to absolute positive values
        assert all(float(price) > 0 for price in processed_df["price"])
        # Verify original positive price row was filtered out (4 rows remain)
        assert len(processed_df) == 4

    def test_process_dataframe_converts_price_to_absolute(
        self, mappings_mock: Callable[[str], str], mocker: MockerFixture
    ) -> None:
        """Test price conversion to absolute values."""
        df = pd.DataFrame(
            {
                "data": ["terminal purchase"],
                "price": ["-50.0"],
                "month": [1],
                "year": [2023],
            }
        )

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(df)

        assert float(result["price"].iloc[0]) == 50.0

    def test_process_dataframe_column_order(
        self,
        sample_raw_dataframe: pd.DataFrame,
        mappings_mock: Callable[[str], str],
        mocker: MockerFixture,
    ) -> None:
        """Verify column order in processed DataFrame."""
        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(sample_raw_dataframe)

        expected_columns = ["month", "year", "price", "category", "data"]
        assert list(result.columns) == expected_columns

    def test_process_dataframe_with_empty_dataframe(self, mappings_mock: Callable[[str], str], mocker: MockerFixture) -> None:
        """Test process_dataframe with empty DataFrame."""
        empty_df = pd.DataFrame(columns=["data", "price", "month", "year"])

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(empty_df)

        assert result.empty
        expected_columns = ["month", "year", "price", "category", "data"]
        assert list(result.columns) == expected_columns

    def test_process_dataframe_removes_refund_entries(self, mocker: MockerFixture) -> None:
        """Verify rows matched as REMOVE_ENTRY (zwrot/refund) are excluded from output."""
        df = pd.DataFrame(
            {
                "data": ["zwrot za zamowienie", "regular purchase", "refund processed"],
                "price": ["-30.0", "-50.0", "-20.0"],
                "month": [1, 1, 1],
                "year": [2023, 2023, 2023],
            }
        )
        result = process_dataframe(df)

        # Only the regular purchase should remain
        assert len(result) == 1
        assert result["data"].iloc[0] == "regular purchase"
        assert "REMOVE_ENTRY" not in result["category"].values

    def test_process_dataframe_with_invalid_columns(self, mocker: MockerFixture) -> None:
        """Test process_dataframe when required columns are missing."""
        mocker.patch("logging.error")
        invalid_df = pd.DataFrame(
            {
                "invalid_column": ["test"],
                "wrong_price": ["invalid_price"],
                "month": [1],
                "year": [2023],
            }
        )

        with pytest.raises(KeyError):
            process_dataframe(invalid_df)

    def test_process_dataframe_handles_mixed_price_formats(
        self, mappings_mock: Callable[[str], str], mocker: MockerFixture
    ) -> None:
        """Test processing with various price formats."""
        df = pd.DataFrame(
            {
                "data": ["terminal purchase", "web payment"],
                "price": ["-50", "-20.50"],
                "month": [1, 1],
                "year": [2023, 2023],
            }
        )

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(df)

        assert len(result) == 2
        assert float(result["price"].iloc[0]) == 50.0
        assert float(result["price"].iloc[1]) == 20.50

    @pytest.mark.parametrize(
        "price_value",
        [
            "-100.0",
            "-0.01",
            "-999.99",
        ],
    )
    def test_process_dataframe_with_various_negative_prices(
        self, price_value: str, mappings_mock: Callable[[str], str], mocker: MockerFixture
    ) -> None:
        """Test processing with various negative price values."""
        df = pd.DataFrame(
            {
                "data": ["terminal purchase"],
                "price": [price_value],
                "month": [1],
                "year": [2023],
            }
        )

        mocker.patch("data_processing.data_core.mappings", mappings_mock)
        result = process_dataframe(df)

        assert len(result) == 1
        assert float(result["price"].iloc[0]) == abs(float(price_value))
