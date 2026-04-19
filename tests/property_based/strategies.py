"""Shared Hypothesis strategies for the property-based test suite."""

import pandas as pd
from hypothesis import strategies as st
from hypothesis.extra.pandas import column, data_frames, range_indexes


def raw_transaction_dfs(min_size: int = 1, max_size: int = 50) -> st.SearchStrategy[pd.DataFrame]:
    """DataFrames with the raw transaction schema [data, price, month, year].

    Args:
        min_size: Minimum number of rows (default 1 to avoid trivially empty frames).
        max_size: Maximum number of rows.

    Returns:
        Strategy producing DataFrames ready for clean_descriptions / process_dataframe.
    """
    return data_frames(
        index=range_indexes(min_size=min_size, max_size=max_size),
        columns=[
            column(
                "data",
                dtype=str,
                elements=st.text(
                    min_size=1,
                    max_size=100,
                    alphabet=st.characters(blacklist_categories=["Cs"]),
                ),
            ),
            column(
                "price",
                dtype=str,
                elements=st.from_regex(r"-\d+\.\d{2}", fullmatch=True),
            ),
            column("month", dtype=int, elements=st.integers(min_value=1, max_value=12)),
            column("year", dtype=int, elements=st.integers(min_value=2000, max_value=2030)),
        ],
    )


def negative_price_strs() -> st.SearchStrategy[str]:
    """Negative decimal price strings matching -NNN.NN format."""
    return st.from_regex(r"-\d+\.\d{2}", fullmatch=True)


def transaction_descriptions() -> st.SearchStrategy[str]:
    """Transaction description strings: known real-world samples plus arbitrary text."""
    _KNOWN: list[str] = [
        "orlen",
        "biedronka shopping",
        "starbucks",
        "unknown transaction",
        "mcd",
        "netflix",
        "terminal purchase",
    ]
    return st.one_of(
        st.sampled_from(_KNOWN),
        st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(blacklist_categories=["Cs"]),
        ),
    )
