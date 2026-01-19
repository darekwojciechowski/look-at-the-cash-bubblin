"""
Property-based tests using Hypothesis.
Generates random test cases to find edge cases.
"""

import pytest

try:
    from hypothesis import HealthCheck, given, settings
    from hypothesis import strategies as st
    from hypothesis.extra.pandas import column, data_frames, range_indexes

    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    pytest.skip("Hypothesis not installed", allow_module_level=True)

from unittest.mock import patch

import pandas as pd

from data_processing.data_core import clean_date, process_dataframe


@pytest.mark.property
@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not installed")
class TestPropertyBasedDataCore:
    """Property-based tests for data_core module."""

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
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.filter_too_much,
        ],
    )
    def test_process_dataframe_always_returns_dataframe(self, prices: list[float]) -> None:
        """Property: process_dataframe always returns a valid DataFrame."""
        transaction_count = len(prices)

        df = pd.DataFrame(
            {
                "data": [f"transaction {i}" for i in range(transaction_count)],
                "price": [str(p) for p in prices],
                "month": [1] * transaction_count,
                "year": [2023] * transaction_count,
            }
        )

        with patch("data_processing.data_core.mappings", {}):
            result = process_dataframe(df)

        # Properties that should always hold
        assert isinstance(result, pd.DataFrame)
        assert len(result) <= len(df)  # Can be filtered
        assert "category" in result.columns
        assert "price" in result.columns

    @given(
        data=data_frames(
            index=range_indexes(min_size=1, max_size=50),
            columns=[
                column("data", dtype=str, elements=st.text(min_size=1, max_size=100)),
                column(
                    "price",
                    dtype=str,
                    elements=st.from_regex(r"-?\d+\.?\d*", fullmatch=True),
                ),
                column("month", dtype=int, elements=st.integers(min_value=1, max_value=12)),
                column(
                    "year",
                    dtype=int,
                    elements=st.integers(min_value=2000, max_value=2030),
                ),
            ],
        )
    )
    @settings(max_examples=20, deadline=None)
    def test_clean_date_preserves_row_count(self, data: pd.DataFrame) -> None:
        """Property: clean_date preserves the number of rows."""
        result = clean_date(data)

        assert len(result) == len(data)
        assert list(result.columns) == list(data.columns)

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
    def test_price_conversion_always_positive(self, prices: list[float]) -> None:
        """Property: All negative prices are converted to positive."""
        df = pd.DataFrame(
            {
                "data": [f"test {i}" for i in range(len(prices))],
                "price": [str(p) for p in prices],
                "month": [1] * len(prices),
                "year": [2023] * len(prices),
            }
        )

        with patch("data_processing.data_core.mappings", {}):
            result = process_dataframe(df)

        # All prices should be positive
        for price in result["price"]:
            assert float(price) > 0

    @given(
        text=st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=["Cs"]),
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_clean_date_handles_arbitrary_strings(self, text: str) -> None:
        """Property: clean_date handles any valid string input."""
        df = pd.DataFrame({"data": [text], "price": ["-10.0"], "month": [1], "year": [2023]})

        # Should not crash
        result = clean_date(df)
        assert len(result) == 1
        assert isinstance(result["data"].iloc[0], str)


@pytest.mark.property
@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not installed")
class TestPropertyBasedInvariants:
    """Tests for invariants that should always hold."""

    @given(
        df=data_frames(
            index=range_indexes(min_size=0, max_size=100),
            columns=[
                column("data", dtype=str),
                column("price", dtype=str),
                column("month", dtype=int),
                column("year", dtype=int),
            ],
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_clean_date_idempotent(self, df: pd.DataFrame) -> None:
        """Property: Applying clean_date twice gives same result."""
        # Handle empty dataframe
        if len(df) == 0:
            return

        first_clean = clean_date(df)
        second_clean = clean_date(first_clean)

        pd.testing.assert_frame_equal(first_clean, second_clean)

    @given(count=st.integers(min_value=1, max_value=50))
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_column_order_consistency(self, count: int) -> None:
        """Property: Output columns are always in consistent order."""
        df = pd.DataFrame(
            {
                "data": [f"test {i}" for i in range(count)],
                "price": ["-10.0"] * count,
                "month": [1] * count,
                "year": [2023] * count,
            }
        )

        with patch("data_processing.data_core.mappings", {}):
            result = process_dataframe(df)

        expected_columns = ["month", "year", "price", "category", "data"]
        assert list(result.columns) == expected_columns


@pytest.mark.property
@pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not installed")
class TestPropertyBasedEdgeCases:
    """Property-based tests for edge cases."""

    @given(
        month=st.integers(min_value=1, max_value=12),
        year=st.integers(min_value=1900, max_value=2100),
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_date_fields_preserve_values(self, month: int, year: int) -> None:
        """Property: Month and year values are preserved through processing."""
        df = pd.DataFrame({"data": ["test"], "price": ["-10.0"], "month": [month], "year": [year]})

        with patch("data_processing.data_core.mappings", {}):
            result = process_dataframe(df)

        if len(result) > 0:
            assert result["month"].iloc[0] == month
            assert result["year"].iloc[0] == year

    @given(price_str=st.from_regex(r"-\d+\.\d{2}", fullmatch=True))
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_price_format_handling(self, price_str: str) -> None:
        """Property: Various price formats are handled correctly."""
        df = pd.DataFrame({"data": ["test"], "price": [price_str], "month": [1], "year": [2023]})

        with patch("data_processing.data_core.mappings", {}):
            result = process_dataframe(df)

        if len(result) > 0:
            result_price = float(result["price"].iloc[0])
            original_price = abs(float(price_str))
            assert abs(result_price - original_price) < 0.01
