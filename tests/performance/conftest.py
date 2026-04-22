"""Shared fixtures for performance tests."""

from collections.abc import Callable

import pandas as pd
import pytest


@pytest.fixture
def make_large_transaction_df() -> Callable[[int, str], pd.DataFrame]:
    """Factory fixture for building large transaction DataFrames.

    Supported flavours:
    - ``"generic"``: f"transaction {i}" descriptions
    - ``"alternating_terminal_orlen"``: alternating terminal-purchase and orlen rows
    - ``"terminal_only"``: f"purchase in terminal {i}" descriptions
    """

    def _factory(size: int, flavour: str = "generic") -> pd.DataFrame:
        if flavour == "generic":
            data = [f"transaction {i}" for i in range(size)]
            price = [f"-{i % 100 + 10}.0" for i in range(size)]
        elif flavour == "alternating_terminal_orlen":
            data = [
                (f"purchase in terminal - mobile code {i}" if i % 2 == 0 else f"orlen station {i}") for i in range(size)
            ]
            price = [f"-{i % 100 + 10}.50" for i in range(size)]
        elif flavour == "terminal_only":
            data = [f"purchase in terminal {i}" for i in range(size)]
            price = ["-10.0"] * size
        else:
            raise ValueError(f"Unknown flavour: {flavour!r}")

        return pd.DataFrame({
            "data": data,
            "price": price,
            "month": [i % 12 + 1 for i in range(size)],
            "year": [2023] * size,
        })

    return _factory
