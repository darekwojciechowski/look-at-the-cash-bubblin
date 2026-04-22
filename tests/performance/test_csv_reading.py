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

    def test_read_50k_row_csv_under_3s(
        self,
        make_large_transaction_df: Callable[[int, str], pd.DataFrame],
        test_data_dir: Path,
    ) -> None:
        """Read a 50,000-row CSV file within the 3-second budget.

        Given: a real CSV file with 50,000 transaction rows written to disk
        When:  read_transaction_csv() is called with utf-8 encoding
        Then:  50,000 rows are returned and execution time is under 3 seconds
        """
        # Arrange
        csv_file = test_data_dir / "large_test.csv"
        large_df = make_large_transaction_df(50_000, "generic")
        large_df.to_csv(csv_file, index=False)

        # Act + timing
        start_time = time.perf_counter()
        result = read_transaction_csv(str(csv_file), "utf-8")
        execution_time = time.perf_counter() - start_time

        # Assert
        assert len(result) == 50_000
        assert execution_time < 3.0, f"read_transaction_csv took {execution_time:.2f}s, expected < 3s"
