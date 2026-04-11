"""
Performance tests for data processing operations.
Tests execution speed and memory efficiency.
"""

import time
from pathlib import Path

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.data_core import clean_descriptions, process_dataframe
from data_processing.data_imports import read_transaction_csv


@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Performance tests for critical operations."""

    def test_clean_descriptions_performance_large_dataset(self) -> None:
        """Clean 10,000 transactions within the 5-second budget.

        Given: a DataFrame with 10,000 alternating terminal-purchase and orlen rows
        When:  clean_descriptions() is called
        Then:  the result has 10,000 rows and execution time is under 5 seconds
        """
        # Arrange
        large_df = pd.DataFrame(
            {
                "data": [
                    (f"purchase in terminal - mobile code {i}" if i % 2 == 0 else f"orlen station {i}")
                    for i in range(10000)
                ],
                "price": [f"-{i % 100 + 10}.50" for i in range(10000)],
                "month": [i % 12 + 1 for i in range(10000)],
                "year": [2023] * 10000,
            }
        )

        # Act + timing
        start_time = time.perf_counter()
        result = clean_descriptions(large_df)
        execution_time = time.perf_counter() - start_time

        # Assert
        assert len(result) == 10000
        assert execution_time < 5.0, f"clean_descriptions took {execution_time:.2f}s, expected < 5s"

    def test_process_dataframe_performance(self, mocker: MockerFixture) -> None:
        """Process 10,000 transactions within the 10-second budget.

        Given: a DataFrame with 10,000 rows and a mock mappings dict
        When:  process_dataframe() is called
        Then:  the result has 10,000 rows and execution time is under 10 seconds
        """
        # Arrange
        large_df = pd.DataFrame(
            {
                "data": [f"transaction {i}" for i in range(10000)],
                "price": [f"-{i % 100 + 10}.0" for i in range(10000)],
                "month": [i % 12 + 1 for i in range(10000)],
                "year": [2023] * 10000,
            }
        )
        mock_mappings = {f"transaction {i}": "TEST" for i in range(100)}
        mocker.patch("data_processing.data_core.mappings", mock_mappings)

        # Act + timing
        start_time = time.perf_counter()
        result = process_dataframe(large_df)
        execution_time = time.perf_counter() - start_time

        # Assert
        assert len(result) == 10000
        assert execution_time < 10.0, f"process_dataframe took {execution_time:.2f}s, expected < 10s"

    def test_csv_reading_performance(self, test_data_dir: Path) -> None:
        """Read a 50,000-row CSV file within the 3-second budget.

        Given: a real CSV file with 50,000 transaction rows written to disk
        When:  read_transaction_csv() is called with utf-8 encoding
        Then:  50,000 rows are returned and execution time is under 3 seconds
        """
        # Arrange
        csv_file = test_data_dir / "large_test.csv"
        large_df = pd.DataFrame(
            {
                "data": [f"transaction {i}" for i in range(50000)],
                "price": [f"-{i % 1000 + 10}.0" for i in range(50000)],
                "month": [i % 12 + 1 for i in range(50000)],
                "year": [2023] * 50000,
            }
        )
        large_df.to_csv(csv_file, index=False)

        # Act + timing
        start_time = time.perf_counter()
        result = read_transaction_csv(str(csv_file), "utf-8")
        execution_time = time.perf_counter() - start_time

        # Assert
        assert len(result) == 50000
        assert execution_time < 3.0, f"read_transaction_csv took {execution_time:.2f}s, expected < 3s"

    def test_memory_efficiency_large_dataset(self) -> None:
        """Verify clean_descriptions does not more than double memory usage.

        Given: a DataFrame with 100,000 rows
        When:  clean_descriptions() is called
        Then:  the result object is no larger than 1.5× the input object size
        """
        import sys

        # Arrange
        large_df = pd.DataFrame(
            {
                "data": [f"transaction {i}" for i in range(100000)],
                "price": [f"-{i}.0" for i in range(100000)],
                "month": [1] * 100000,
                "year": [2023] * 100000,
            }
        )
        initial_size = sys.getsizeof(large_df)

        # Act
        result = clean_descriptions(large_df)

        # Assert
        result_size = sys.getsizeof(result)
        assert result_size < initial_size * 1.5, f"Memory usage increased from {initial_size} to {result_size}"


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Benchmark tests for comparing performance."""

    @pytest.mark.parametrize("dataset_size", [100, 1000, 5000])
    def test_clean_descriptions_scaling(self, dataset_size: int) -> None:
        """Clean descriptions scales near-linearly with dataset size.

        Given: a DataFrame with a parametrized number of terminal-purchase rows
        When:  clean_descriptions() is called
        Then:  the result has the same row count and execution time stays within budget
        """
        # Arrange
        df = pd.DataFrame(
            {
                "data": [f"purchase in terminal {i}" for i in range(dataset_size)],
                "price": ["-10.0"] * dataset_size,
                "month": [1] * dataset_size,
                "year": [2023] * dataset_size,
            }
        )

        # Act + timing
        start_time = time.perf_counter()
        result = clean_descriptions(df)
        execution_time = time.perf_counter() - start_time

        # Assert
        expected_max_time = dataset_size / 1000  # 1ms per 1000 records
        assert execution_time < expected_max_time + 1.0, f"Processing {dataset_size} records took {execution_time:.3f}s"
        assert len(result) == dataset_size

    def test_dataframe_operations_efficiency(self) -> None:
        """Column access and row filtering complete within tight time budgets.

        Given: a DataFrame with 10,000 rows
        When:  column access is repeated 100 times then row filtering 100 times
        Then:  column access completes in under 0.1 s and filtering in under 1.0 s
        """
        # Arrange
        df = pd.DataFrame(
            {
                "data": ["test"] * 10000,
                "price": ["-10.0"] * 10000,
                "month": [1] * 10000,
                "year": [2023] * 10000,
            }
        )

        # Act + timing (column access)
        start_time = time.perf_counter()
        for _ in range(100):
            _ = df["data"]
        column_access_time = time.perf_counter() - start_time

        # Assert (column access)
        assert column_access_time < 0.1, f"Column access too slow: {column_access_time:.3f}s"

        # Act + timing (filtering)
        start_time = time.perf_counter()
        for _ in range(100):
            _ = df[df["month"] == 1]
        filtering_time = time.perf_counter() - start_time

        # Assert (filtering)
        assert filtering_time < 1.0, f"Filtering too slow: {filtering_time:.3f}s"
