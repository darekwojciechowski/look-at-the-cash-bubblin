"""Performance tests for read_transaction_csv()."""

import time
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_imports import read_transaction_csv


@pytest.mark.performance
@pytest.mark.slow
class TestCsvReadingPerformance:
    """I/O latency benchmarks for read_transaction_csv()."""

    def test_read_csv_scaling_between_5k_and_50k(
        self,
        make_large_transaction_df: Callable[[int, str], pd.DataFrame],
        test_data_dir: Path,
    ) -> None:
        """CSV read cost scales reasonably between 5k and 50k rows.

        Given: real 5,000-row and 50,000-row CSV files written to disk
        When:  read_transaction_csv() is called for each file
        Then:  row counts and schema are preserved and per-row time stays bounded
        """
        # Arrange
        small_csv = test_data_dir / "small_test.csv"
        large_csv = test_data_dir / "large_test.csv"
        small_df = make_large_transaction_df(5_000, "generic")
        large_df = make_large_transaction_df(50_000, "generic")
        small_df.to_csv(small_csv, index=False)
        large_df.to_csv(large_csv, index=False)

        # Act + timing (small)
        small_start = time.perf_counter()
        small_result = read_transaction_csv(str(small_csv), "utf-8")
        small_time = time.perf_counter() - small_start

        # Act + timing (large)
        start_time = time.perf_counter()
        large_result = read_transaction_csv(str(large_csv), "utf-8")
        large_time = time.perf_counter() - start_time

        # Assert
        assert len(small_result) == 5_000
        assert len(large_result) == 50_000
        assert list(small_result.columns) == list(large_result.columns)
        assert large_time < 45.0, f"Reading 50k rows exceeded 45s guard ({large_time:.2f}s)"

        small_per_row = small_time / 5_000
        large_per_row = large_time / 50_000
        assert large_per_row <= small_per_row * 10
