"""Performance tests for clean_descriptions()."""

import time
from collections.abc import Callable

import pandas as pd
import pytest

from data_processing.data_core import clean_descriptions


@pytest.mark.performance
@pytest.mark.slow
class TestCleanDescriptionsPerformance:
    """Latency and scaling benchmarks for clean_descriptions()."""

    def test_latency_10k_rows(self, make_large_transaction_df: Callable[[int, str], pd.DataFrame]) -> None:
        """Clean 10,000 transactions while preserving row count and key replacements.

        Given: a DataFrame with 10,000 alternating terminal-purchase and orlen rows
        When:  clean_descriptions() is called
        Then:  the result has 10,000 rows, contains normalized keywords,
               and completes within a generous guard time
        """
        # Arrange
        large_df = make_large_transaction_df(10_000, "alternating_terminal_orlen")

        # Act + timing
        start_time = time.perf_counter()
        result = clean_descriptions(large_df)
        execution_time = time.perf_counter() - start_time

        # Assert
        assert len(result) == 10_000
        assert result["data"].str.contains("terminal purchase", regex=False).any()
        assert result["data"].str.contains("Orlen gas station", regex=False).any()
        assert execution_time < 30.0, f"clean_descriptions took {execution_time:.2f}s, expected < 30s guard"

    def test_scaling_near_linear(
        self,
        make_large_transaction_df: Callable[[int, str], pd.DataFrame],
    ) -> None:
        """Per-row runtime stays within a bounded factor as dataset size grows.

        Given: terminal-only datasets of increasing size
        When:  clean_descriptions() runs for each dataset
        Then:  row counts are preserved and per-row cost does not regress sharply
        """
        # Arrange
        sizes = [500, 2500, 5000]
        per_row_times: dict[int, float] = {}

        # Act + Assert per size
        for size in sizes:
            df = make_large_transaction_df(size, "terminal_only")
            start_time = time.perf_counter()
            result = clean_descriptions(df)
            execution_time = time.perf_counter() - start_time

            assert len(result) == size
            assert result["data"].str.contains("purchase in terminal", regex=False).all()
            assert execution_time < 20.0, f"Processing {size} records exceeded 20s guard"
            per_row_times[size] = execution_time / size

        # Relative scaling guard: larger batches should not be dramatically
        # slower per row than smaller ones on the same host.
        assert per_row_times[5000] <= per_row_times[500] * 10
