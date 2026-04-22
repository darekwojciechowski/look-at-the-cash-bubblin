"""Performance tests for raw DataFrame primitive operations."""

import time
from collections.abc import Callable

import pandas as pd
import pytest


@pytest.mark.performance
@pytest.mark.slow
class TestDataframePrimitives:
    """Benchmarks for column access and row filtering on a 10k-row DataFrame."""

    def test_column_access_100x_under_100ms(
        self, make_large_transaction_df: Callable[[int, str], pd.DataFrame]
    ) -> None:
        """Column access repeated 100 times completes under 100 ms.

        Given: a DataFrame with 10,000 rows
        When:  the "data" column is accessed 100 times
        Then:  total execution time is under 0.1 seconds
        """
        # Arrange
        df = make_large_transaction_df(10_000, "generic")

        # Act + timing
        start_time = time.perf_counter()
        for _ in range(100):
            _ = df["data"]
        column_access_time = time.perf_counter() - start_time

        # Assert
        assert column_access_time < 0.1, f"Column access too slow: {column_access_time:.3f}s"

    def test_row_filtering_100x_under_1s(self, make_large_transaction_df: Callable[[int, str], pd.DataFrame]) -> None:
        """Row filtering repeated 100 times completes under 1 second.

        Given: a DataFrame with 10,000 rows
        When:  rows where month == 1 are filtered 100 times
        Then:  total execution time is under 1.0 second
        """
        # Arrange
        df = make_large_transaction_df(10_000, "generic")

        # Act + timing
        start_time = time.perf_counter()
        for _ in range(100):
            _ = df[df["month"] == 1]
        filtering_time = time.perf_counter() - start_time

        # Assert
        assert filtering_time < 1.0, f"Filtering too slow: {filtering_time:.3f}s"
