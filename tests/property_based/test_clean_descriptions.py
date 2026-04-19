"""Property-based tests for data_processing.data_core.clean_descriptions."""

import pandas as pd
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.extra.pandas import column, data_frames, range_indexes

from data_processing.data_core import clean_descriptions
from tests.property_based.strategies import raw_transaction_dfs


@pytest.mark.property
class TestCleanDescriptions:
    """Property-based invariants for clean_descriptions()."""

    @given(data=raw_transaction_dfs())
    @settings(max_examples=20, deadline=None)
    def test_preserves_row_count(self, data: pd.DataFrame) -> None:
        """Property: clean_descriptions preserves the number of rows.

        Given: a Hypothesis-generated DataFrame with the raw transaction schema
        When:  clean_descriptions() is called
        Then:  the result has the same number of rows and columns as the input
        """
        # Act
        result = clean_descriptions(data)

        # Assert
        assert len(result) == len(data)
        assert list(result.columns) == list(data.columns)

    @given(
        df=data_frames(
            index=range_indexes(min_size=0, max_size=100),
            columns=[
                column("data", dtype=str),
                column("price", dtype=str),
                column("month", dtype=int),
                column("year", dtype=int),
            ],
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_idempotent(self, df: pd.DataFrame) -> None:
        """Property: Applying clean_descriptions twice gives the same result.

        Given: a Hypothesis-generated DataFrame with at least one row
        When:  clean_descriptions() is applied twice in succession
        Then:  both results are identical (idempotent)
        """
        # Arrange — skip trivially empty frames; they carry no signal
        assume(len(df) > 0)

        # Act
        first_clean = clean_descriptions(df)
        second_clean = clean_descriptions(first_clean)

        # Assert
        pd.testing.assert_frame_equal(first_clean, second_clean)

    @given(
        text=st.text(
            min_size=1,
            max_size=200,
            alphabet=st.characters(blacklist_categories=["Cs"]),
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_handles_arbitrary_strings(self, text: str) -> None:
        """Property: clean_descriptions handles any valid string without crashing.

        Given: an arbitrary non-surrogate string
        When:  clean_descriptions() is called
        Then:  it does not raise and the data cell remains a string
        """
        # Arrange
        df = pd.DataFrame({"data": [text], "price": ["-10.0"], "month": [1], "year": [2023]})

        # Act
        result = clean_descriptions(df)

        # Assert
        assert len(result) == 1
        assert isinstance(result["data"].iloc[0], str)
