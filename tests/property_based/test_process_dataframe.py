"""Property-based tests for data_processing.data_core.process_dataframe."""

import pandas as pd
import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from data_processing.data_core import process_dataframe
from tests.property_based.strategies import negative_price_strs


@pytest.mark.property
class TestProcessDataframe:
    """Property-based invariants for process_dataframe()."""

    @given(
        prices=st.lists(
            st.floats(min_value=-10000, max_value=-0.01, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=100,
        )
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_always_returns_dataframe(self, prices: list[float], empty_mappings: None) -> None:
        """Property: process_dataframe always returns a valid DataFrame.

        Given: a list of negative floats and an empty category mapping
        When:  process_dataframe() is called
        Then:  the result is a DataFrame with category and price columns, no more rows than input
        """
        # Arrange
        count = len(prices)
        df = pd.DataFrame({
            "data": [f"transaction {i}" for i in range(count)],
            "price": [str(p) for p in prices],
            "month": [1] * count,
            "year": [2023] * count,
        })

        # Act
        result = process_dataframe(df)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) <= len(df)
        assert "category" in result.columns
        assert "price" in result.columns

    @given(
        prices=st.lists(
            st.floats(min_value=-10000, max_value=-0.01, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=50,
        )
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_price_conversion_always_positive(self, prices: list[float], empty_mappings: None) -> None:
        """Property: All negative prices are converted to positive absolute values.

        Given: a list of negative floats and an empty category mapping
        When:  process_dataframe() is called
        Then:  every price in the result is a positive float
        """
        # Arrange
        df = pd.DataFrame({
            "data": [f"test {i}" for i in range(len(prices))],
            "price": [str(p) for p in prices],
            "month": [1] * len(prices),
            "year": [2023] * len(prices),
        })

        # Act
        result = process_dataframe(df)

        # Assert
        for price in result["price"]:
            assert float(price) > 0

    @given(count=st.integers(min_value=1, max_value=50))
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_column_order_consistency(self, count: int, empty_mappings: None) -> None:
        """Property: Output columns are always in the canonical order.

        Given: a DataFrame with a Hypothesis-generated row count and empty mapping
        When:  process_dataframe() is called
        Then:  columns are always [month, year, price, category, data]
        """
        # Arrange
        df = pd.DataFrame({
            "data": [f"test {i}" for i in range(count)],
            "price": ["-10.0"] * count,
            "month": [1] * count,
            "year": [2023] * count,
        })

        # Act
        result = process_dataframe(df)

        # Assert
        assert list(result.columns) == ["month", "year", "price", "category", "data"]

    @given(
        month=st.integers(min_value=1, max_value=12),
        year=st.integers(min_value=1900, max_value=2100),
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_date_fields_preserve_values(self, month: int, year: int, empty_mappings: None) -> None:
        """Property: Month and year values are preserved through processing.

        Given: Hypothesis-generated month and year integers and empty mapping
        When:  process_dataframe() is called on a single-row DataFrame
        Then:  the output row retains the original month and year values
        """
        # Arrange
        df = pd.DataFrame({"data": ["test"], "price": ["-10.0"], "month": [month], "year": [year]})

        # Act
        result = process_dataframe(df)

        # Assert — skip examples where the row was filtered out
        assume(len(result) > 0)
        assert result["month"].iloc[0] == month
        assert result["year"].iloc[0] == year

    @given(price_str=negative_price_strs())
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_price_format_handling(self, price_str: str, empty_mappings: None) -> None:
        """Property: Negative decimal price strings are converted to their absolute values.

        Given: a Hypothesis-generated negative decimal price string and empty mapping
        When:  process_dataframe() is called
        Then:  the result price equals the absolute value of the input within 0.01 tolerance
        """
        # Arrange
        df = pd.DataFrame({"data": ["test"], "price": [price_str], "month": [1], "year": [2023]})

        # Act
        result = process_dataframe(df)

        # Assert — skip examples where the row was filtered out
        assume(len(result) > 0)
        assert abs(float(result["price"].iloc[0]) - abs(float(price_str))) < 0.01
