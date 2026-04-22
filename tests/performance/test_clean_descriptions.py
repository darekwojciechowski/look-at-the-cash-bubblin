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
        """Clean 10,000 transactions within the 5-second budget.

        Given: a DataFrame with 10,000 alternating terminal-purchase and orlen rows
        When:  clean_descriptions() is called
        Then:  the result has 10,000 rows and execution time is under 5 seconds
        """
        # Arrange
        large_df = make_large_transaction_df(10_000, "alternating_terminal_orlen")

        # Act + timing
        start_time = time.perf_counter()
        result = clean_descriptions(large_df)
        execution_time = time.perf_counter() - start_time

        # Assert
        assert len(result) == 10_000
        assert execution_time < 5.0, f"clean_descriptions took {execution_time:.2f}s, expected < 5s"

    @pytest.mark.parametrize("dataset_size", [100, 1000, 5000])
    def test_scaling_near_linear(
        self,
        dataset_size: int,
        make_large_transaction_df: Callable[[int, str], pd.DataFrame],
    ) -> None:
        """Clean descriptions scales near-linearly with dataset size.

        Given: a DataFrame with a parametrized number of terminal-purchase rows
        When:  clean_descriptions() is called
        Then:  the result has the same row count and execution time stays within budget
        """
        # Arrange
        df = make_large_transaction_df(dataset_size, "terminal_only")

        # Act + timing
        start_time = time.perf_counter()
        result = clean_descriptions(df)
        execution_time = time.perf_counter() - start_time

        # Assert
        expected_max_time = max(0.05, 3 * dataset_size / 1000)
        assert execution_time < expected_max_time, f"Processing {dataset_size} records took {execution_time:.3f}s"
        assert len(result) == dataset_size
