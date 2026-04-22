"""Memory footprint tests for clean_descriptions()."""

from collections.abc import Callable

import pandas as pd
import pytest

from data_processing.data_core import clean_descriptions


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryFootprint:
    """Memory benchmarks for clean_descriptions()."""

    def test_clean_descriptions_does_not_inflate_memory(
        self, make_large_transaction_df: Callable[[int, str], pd.DataFrame]
    ) -> None:
        """Verify clean_descriptions does not more than 1.5× the input memory.

        Given: a DataFrame with 100,000 rows
        When:  clean_descriptions() is called
        Then:  the result uses no more than 1.5× the initial memory (by pandas deep measure)
        """
        # Arrange
        large_df = make_large_transaction_df(100_000, "generic")
        initial_size = large_df.memory_usage(deep=True).sum()

        # Act
        result = clean_descriptions(large_df)

        # Assert
        result_size = result.memory_usage(deep=True).sum()
        assert result_size < initial_size * 1.5, f"Memory usage increased from {initial_size} to {result_size}"
