"""Performance tests for process_dataframe()."""

import time
from collections.abc import Callable

import pandas as pd
import pytest

from data_processing.data_core import process_dataframe


@pytest.mark.performance
@pytest.mark.slow
class TestProcessDataframePerformance:
    """Latency benchmarks for process_dataframe()."""

    def test_latency_10k_rows(
        self,
        make_large_transaction_df: Callable[[int, str], pd.DataFrame],
        empty_mappings: None,
    ) -> None:
        """Process 10,000 transactions within the 10-second budget.

        Given: a DataFrame with 10,000 rows and an empty mappings patch
        When:  process_dataframe() is called
        Then:  the result has 10,000 rows and execution time is under 10 seconds
        """
        # Arrange
        large_df = make_large_transaction_df(10_000, "generic")

        # Act + timing
        start_time = time.perf_counter()
        result = process_dataframe(large_df)
        execution_time = time.perf_counter() - start_time

        # Assert
        assert len(result) == 10_000
        assert execution_time < 10.0, f"process_dataframe took {execution_time:.2f}s, expected < 10s"
