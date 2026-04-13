"""Data contract tests for PKO IPKO processing pipeline.

Each test class validates the schema guarantee that one pipeline stage
promises to the next stage.  Treating inter-stage boundaries as typed
contracts catches schema drift early and documents the expected shape of
every intermediate artifact.

Markers: unit, contract
"""

import pandas as pd
import pytest

from data_processing.data_core import clean_descriptions, process_dataframe
from data_processing.data_imports import ipko_import
from data_processing.location_processor import extract_location_from_data

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_IPKO_RAW_COLUMNS = {0, 1, 2, 3, 4, 5, 6, 7, 8}
_IPKO_OUTPUT_COLUMNS = {"price", "data", "month", "year"}
_PROCESSED_COLUMNS = ["month", "year", "price", "category", "data"]


# ─────────────────────────────────────────────────────────────────────────────
# 1. ipko_import output contract
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.contract
class TestIpkoImportOutputContract:
    """ipko_import() must produce a DataFrame with the canonical pipeline schema."""

    def test_output_columns_are_exactly_required_set(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """ipko_import() produces exactly {price, data, month, year}.

        Given: a raw 9-column IPKO DataFrame
        When:  ipko_import() is called
        Then:  the result has exactly the four canonical columns and no others
        """
        # Arrange — via sample_ipko_dataframe fixture
        # Act
        result = ipko_import(sample_ipko_dataframe)

        # Assert
        assert set(result.columns) == _IPKO_OUTPUT_COLUMNS

    def test_month_values_are_in_valid_calendar_range(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """month column values must be integers in [1, 12].

        Given: a raw IPKO DataFrame with date strings in YYYY-MM-DD format
        When:  ipko_import() is called
        Then:  every month value is between 1 and 12 inclusive
        """
        result = ipko_import(sample_ipko_dataframe)

        assert result["month"].between(1, 12).all()

    def test_data_column_contains_only_lowercase_text(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """The concatenated 'data' column must be lowercase after import.

        Given: a raw IPKO DataFrame
        When:  ipko_import() is called
        Then:  every value in the data column equals its own .lower() form
        """
        result = ipko_import(sample_ipko_dataframe)

        assert result["data"].str.lower().eq(result["data"]).all()

    def test_no_raw_integer_columns_remain(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """All nine integer-indexed raw columns must be dropped.

        Given: a raw IPKO DataFrame whose columns are integers 0–8
        When:  ipko_import() is called
        Then:  no integer-typed column names remain in the output
        """
        result = ipko_import(sample_ipko_dataframe)

        assert not any(isinstance(c, int) for c in result.columns)

    def test_year_extracted_matches_source_dates(self, sample_ipko_dataframe: pd.DataFrame) -> None:
        """Year must be parsed from the transaction_date column.

        Given: a raw IPKO DataFrame whose dates are in 2023
        When:  ipko_import() is called
        Then:  every year value equals 2023
        """
        result = ipko_import(sample_ipko_dataframe)

        assert (result["year"] == 2023).all()


# ─────────────────────────────────────────────────────────────────────────────
# 2. process_dataframe output contract
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.contract
class TestProcessDataframeOutputContract:
    """process_dataframe() must produce a clean, categorized DataFrame ready for export."""

    def test_output_column_order_matches_export_schema(self, sample_raw_dataframe: pd.DataFrame) -> None:
        """Output columns must match the canonical export order.

        Given: a raw transaction DataFrame with data/price/month/year columns
        When:  process_dataframe() is called
        Then:  output columns are exactly [month, year, price, category, data]
        """
        result = process_dataframe(sample_raw_dataframe)

        assert list(result.columns) == _PROCESSED_COLUMNS

    def test_category_column_has_no_null_values(self, sample_raw_dataframe: pd.DataFrame) -> None:
        """Every row in the output must have a non-null category.

        Given: a raw transaction DataFrame
        When:  process_dataframe() is called
        Then:  the category column contains no NaN or None values
        """
        result = process_dataframe(sample_raw_dataframe)

        assert result["category"].notna().all()

    def test_no_positive_original_prices_in_output(self) -> None:
        """Income rows (positive price) must be filtered out.

        Given: a DataFrame containing one negative and one positive price
        When:  process_dataframe() is called
        Then:  the positive-price row is absent from the result
        """
        # Arrange — mixed-sign prices
        df = pd.DataFrame(
            {
                "data": ["orlen", "salary income"],
                "price": ["-100.0", "3000.0"],
                "month": [1, 1],
                "year": [2023, 2023],
            }
        )

        # Act
        result = process_dataframe(df)

        # Assert — only expense row survives
        assert len(result) == 1
        assert float(result["price"].iloc[0]) > 0  # stored as absolute value

    def test_price_column_dtype_is_object_string(self, sample_raw_dataframe: pd.DataFrame) -> None:
        """Price must be stored as a string dtype after processing.

        Given: a raw transaction DataFrame with string prices
        When:  process_dataframe() is called
        Then:  the price column has a string dtype (object or StringDtype)
        """
        result = process_dataframe(sample_raw_dataframe)

        assert pd.api.types.is_string_dtype(result["price"])

    def test_row_count_does_not_exceed_input(self, sample_raw_dataframe: pd.DataFrame) -> None:
        """Processing can only remove rows, never add them.

        Given: a raw transaction DataFrame
        When:  process_dataframe() is called
        Then:  the output has fewer or equal rows than the input
        """
        result = process_dataframe(sample_raw_dataframe)

        assert len(result) <= len(sample_raw_dataframe)


# ─────────────────────────────────────────────────────────────────────────────
# 3. clean_descriptions output contract
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.contract
class TestCleanDescriptionsContract:
    """clean_descriptions() must honour the OCP and preserve row count and dtype."""

    def test_ocp_custom_replacements_are_applied(self) -> None:
        """Passing a custom replacements dict replaces the default IPKO mapping.

        Given: a DataFrame with 'data' containing 'foo bar' and a custom {'foo': 'baz'}
        When:  clean_descriptions() is called with that custom dict
        Then:  'foo' is replaced by 'baz' without modifying the remaining text
        """
        # Arrange
        df = pd.DataFrame(
            {
                "data": ["foo bar"],
                "price": ["-50.0"],
                "month": [1],
                "year": [2023],
            }
        )

        # Act
        result = clean_descriptions(df.copy(), replacements={"foo": "baz"})

        # Assert
        assert result["data"].iloc[0] == "baz bar"

    def test_data_column_dtype_is_preserved(self, sample_raw_dataframe: pd.DataFrame) -> None:
        """The data column dtype must remain a string dtype after cleaning.

        Given: a raw transaction DataFrame whose data column is a string dtype
        When:  clean_descriptions() is called
        Then:  the data column dtype is still a string dtype (object or StringDtype)
        """
        result = clean_descriptions(sample_raw_dataframe.copy())

        assert pd.api.types.is_string_dtype(result["data"])

    def test_row_count_is_unchanged(self, sample_raw_dataframe: pd.DataFrame) -> None:
        """Cleaning must not add or remove rows.

        Given: a raw transaction DataFrame with N rows
        When:  clean_descriptions() is called
        Then:  the output has the same N rows
        """
        original_len = len(sample_raw_dataframe)

        result = clean_descriptions(sample_raw_dataframe.copy())

        assert len(result) == original_len


# ─────────────────────────────────────────────────────────────────────────────
# 4. extract_location_from_data output contract
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
@pytest.mark.contract
class TestLocationExtractorOutputContract:
    """extract_location_from_data() must always return str and never raise."""

    @pytest.mark.parametrize(
        "transaction_text",
        [
            "some generic transaction",
            "lokalizacja: adres: ul. Testowa 1 miasto: Warszawa kraj: Polska",
            "PAYMENT - ul. Kościuszki 10, Łódź",
            "abc",
        ],
    )
    def test_always_returns_str_for_normal_input(self, transaction_text: str) -> None:
        """Return type must be str for any non-null input.

        Given: a non-null transaction text string (parametrized)
        When:  extract_location_from_data() is called
        Then:  the return value is an instance of str
        """
        result = extract_location_from_data(transaction_text)

        assert isinstance(result, str)

    def test_does_not_raise_on_float_nan(self) -> None:
        """Must not raise TypeError when passed float NaN.

        Given: float('nan') as input (the value pandas assigns to missing floats)
        When:  extract_location_from_data() is called
        Then:  no exception is raised
        """
        extract_location_from_data(float("nan"))  # must not raise

    def test_returns_empty_string_for_none(self) -> None:
        """None input must yield an empty string.

        Given: None as input
        When:  extract_location_from_data() is called
        Then:  an empty string is returned
        """
        result = extract_location_from_data(None)

        assert result == ""

    def test_returns_str_for_float_nan(self) -> None:
        """float NaN input must yield a str (not raise, not return None).

        Given: float('nan') as input
        When:  extract_location_from_data() is called
        Then:  the return value is an instance of str
        """
        result = extract_location_from_data(float("nan"))

        assert isinstance(result, str)
