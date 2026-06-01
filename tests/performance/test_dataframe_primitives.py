"""Performance tests for raw DataFrame primitive operations."""

import time
from collections.abc import Callable

import pandas as pd
import pytest


@pytest.mark.performance
@pytest.mark.slow
class TestDataframePrimitives:
    """Benchmarks for column access and row filtering on a 10k-row DataFrame."""

    def test_column_access_scales_with_iteration_count(
        self, make_large_transaction_df: Callable[[int, str], pd.DataFrame]
    ) -> None:
        """Column access cost scales within a bounded factor across loop counts.

        Given: a DataFrame with 10,000 rows
        When:  the "data" column is accessed in short and long loops
        Then:  returned data is stable and per-iteration time stays bounded
        """
        # Arrange
        df = make_large_transaction_df(10_000, "generic")

        # Act + timing
        def _time_column_access(iterations: int) -> tuple[float, pd.Series]:
            start = time.perf_counter()
            result = df["data"]
            for _ in range(iterations - 1):
                result = df["data"]
            return time.perf_counter() - start, result

        short_time, short_result = _time_column_access(20)
        long_time, long_result = _time_column_access(200)

        # Assert
        assert len(short_result) == len(df)
        assert short_result.equals(long_result)
        assert long_time < 10.0, f"Column access exceeded 10s guard ({long_time:.3f}s)"

        short_per_iteration = short_time / 20
        long_per_iteration = long_time / 200
        assert long_per_iteration <= short_per_iteration * 6

    def test_row_filtering_scales_with_iteration_count(
        self, make_large_transaction_df: Callable[[int, str], pd.DataFrame]
    ) -> None:
        """Row filtering cost scales within a bounded factor across loop counts.

        Given: a DataFrame with 10,000 rows
        When:  rows where month == 1 are filtered in short and long loops
        Then:  filtered row counts stay stable and per-iteration time remains bounded
        """
        # Arrange
        df = make_large_transaction_df(10_000, "generic")

        # Act + timing
        def _time_filter(iterations: int) -> tuple[float, pd.DataFrame]:
            start = time.perf_counter()
            result = df[df["month"] == 1]
            for _ in range(iterations - 1):
                result = df[df["month"] == 1]
            return time.perf_counter() - start, result

        short_time, short_filtered = _time_filter(20)
        long_time, long_filtered = _time_filter(200)

        # Assert
        assert len(short_filtered) == len(long_filtered)
        assert long_time < 15.0, f"Filtering exceeded 15s guard ({long_time:.3f}s)"

        short_per_iteration = short_time / 20
        long_per_iteration = long_time / 200
        assert long_per_iteration <= short_per_iteration * 8
