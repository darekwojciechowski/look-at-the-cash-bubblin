"""
Performance tests for data processing operations.
Tests execution speed and memory efficiency.
"""

import pytest
import pandas as pd
import time
from pathlib import Path
from pytest_mock import MockerFixture

from data_processing.data_core import clean_date, process_dataframe
from data_processing.data_imports import read_transaction_csv


@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Performance tests for critical operations."""

    def test_clean_date_performance_large_dataset(self) -> None:
        """Test clean_date performance with 10,000 transactions."""
        # Create large dataset
        large_df = pd.DataFrame({
            "data": [
                f"purchase in terminal - mobile code {i}" if i % 2 == 0
                else f"orlen station {i}"
                for i in range(10000)
            ],
            "price": [f"-{i % 100 + 10}.50" for i in range(10000)],
            "month": [i % 12 + 1 for i in range(10000)],
            "year": [2023] * 10000
        })

        # Measure performance
        start_time = time.perf_counter()
        result = clean_date(large_df)
        execution_time = time.perf_counter() - start_time

        # Assertions
        assert len(result) == 10000
        assert execution_time < 5.0, f"clean_date took {execution_time:.2f}s, expected < 5s"

    def test_process_dataframe_performance(self, mocker: MockerFixture) -> None:
        """Test process_dataframe performance with 10,000 transactions."""
        # Create large dataset
        large_df = pd.DataFrame({
            "data": [f"transaction {i}" for i in range(10000)],
            "price": [f"-{i % 100 + 10}.0" for i in range(10000)],
            "month": [i % 12 + 1 for i in range(10000)],
            "year": [2023] * 10000
        })

        # Mock mappings for consistent testing
        mock_mappings = {f"transaction {i}": "TEST" for i in range(100)}
        mocker.patch("data_processing.data_core.mappings", mock_mappings)

        # Measure performance
        start_time = time.perf_counter()
        result = process_dataframe(large_df)
        execution_time = time.perf_counter() - start_time

        # Assertions
        assert len(result) == 10000
        assert execution_time < 10.0, f"process_dataframe took {execution_time:.2f}s, expected < 10s"

    def test_csv_reading_performance(self, test_data_dir: Path) -> None:
        """Test CSV reading performance with large file."""
        # Create large CSV file
        csv_file = test_data_dir / "large_test.csv"
        large_df = pd.DataFrame({
            "data": [f"transaction {i}" for i in range(50000)],
            "price": [f"-{i % 1000 + 10}.0" for i in range(50000)],
            "month": [i % 12 + 1 for i in range(50000)],
            "year": [2023] * 50000
        })
        large_df.to_csv(csv_file, index=False)

        # Measure performance
        start_time = time.perf_counter()
        result = read_transaction_csv(str(csv_file), 'utf-8')
        execution_time = time.perf_counter() - start_time

        # Assertions
        assert len(result) == 50000
        assert execution_time < 3.0, f"read_transaction_csv took {execution_time:.2f}s, expected < 3s"

    def test_memory_efficiency_large_dataset(self) -> None:
        """Test that processing doesn't create excessive memory copies."""
        import sys

        # Create large dataset
        large_df = pd.DataFrame({
            "data": [f"transaction {i}" for i in range(100000)],
            "price": [f"-{i}.0" for i in range(100000)],
            "month": [1] * 100000,
            "year": [2023] * 100000
        })

        initial_size = sys.getsizeof(large_df)

        # Process data
        result = clean_date(large_df)

        result_size = sys.getsizeof(result)

        # Memory should not grow excessively (allow 50% overhead)
        assert result_size < initial_size * 1.5, \
            f"Memory usage increased from {initial_size} to {result_size}"


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Benchmark tests for comparing performance."""

    @pytest.mark.parametrize("dataset_size", [100, 1000, 5000])
    def test_clean_date_scaling(self, dataset_size: int) -> None:
        """Test how clean_date scales with dataset size."""
        df = pd.DataFrame({
            "data": [f"purchase in terminal {i}" for i in range(dataset_size)],
            "price": ["-10.0"] * dataset_size,
            "month": [1] * dataset_size,
            "year": [2023] * dataset_size
        })

        start_time = time.perf_counter()
        result = clean_date(df)
        execution_time = time.perf_counter() - start_time

        # Performance should scale roughly linearly
        expected_max_time = dataset_size / 1000  # 1ms per 1000 records
        assert execution_time < expected_max_time + 1.0, \
            f"Processing {dataset_size} records took {execution_time:.3f}s"

        assert len(result) == dataset_size

    def test_dataframe_operations_efficiency(self) -> None:
        """Test efficiency of DataFrame operations."""
        df = pd.DataFrame({
            "data": ["test"] * 10000,
            "price": ["-10.0"] * 10000,
            "month": [1] * 10000,
            "year": [2023] * 10000
        })

        # Test column access performance
        start_time = time.perf_counter()
        for _ in range(100):
            _ = df["data"]
        column_access_time = time.perf_counter() - start_time

        assert column_access_time < 0.1, \
            f"Column access too slow: {column_access_time:.3f}s"

        # Test filtering performance
        start_time = time.perf_counter()
        for _ in range(100):
            _ = df[df["month"] == 1]
        filtering_time = time.perf_counter() - start_time

        assert filtering_time < 1.0, \
            f"Filtering too slow: {filtering_time:.3f}s"
