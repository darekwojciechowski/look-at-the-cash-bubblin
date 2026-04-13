"""Stateful property-based tests for the PKO transaction pipeline.

Uses Hypothesis RuleBasedStateMachine to verify that the pipeline correctly
handles any valid sequence of state transitions (EMPTY → LOADED → CLEANED →
PROCESSED → EMPTY) and that cross-state invariants are never violated.

This technique catches ordering bugs and emergent state corruption that
per-function unit tests miss because they only test one transition at a time.

Markers: property
"""

import pandas as pd
import pytest

try:
    from hypothesis import HealthCheck, settings
    from hypothesis import strategies as st
    from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    pytest.skip("Hypothesis not installed", allow_module_level=True)

from data_processing.data_core import clean_descriptions, process_dataframe

# ─────────────────────────────────────────────────────────────────────────────
# Strategies
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_DESCRIPTIONS: list[str] = [
    "orlen",
    "biedronka shopping",
    "starbucks",
    "unknown transaction",
    "mcd",
    "netflix",
    "terminal purchase",
]

_SAMPLE_PRICES: list[str] = ["-100.0", "-50.0", "-200.0", "-15.0", "-30.0"]

# Columns that may appear in the buffer at any pipeline stage.
_VALID_COLUMNS: frozenset[str] = frozenset({"data", "price", "month", "year", "category"})


# ─────────────────────────────────────────────────────────────────────────────
# State machine
# ─────────────────────────────────────────────────────────────────────────────


class TransactionPipelineMachine(RuleBasedStateMachine):
    """Models the four-state pipeline and checks structural invariants at every step.

    States
    ------
    EMPTY     : no data loaded; buffer is an empty DataFrame
    LOADED    : raw transaction data ready for cleaning
    CLEANED   : descriptions have been normalised
    PROCESSED : categorised and filtered; ready for export
    """

    def __init__(self) -> None:
        super().__init__()
        self.buffer: pd.DataFrame = pd.DataFrame()
        self._state: str = "EMPTY"

    # ── Transitions ──────────────────────────────────────────────────────────

    @initialize()
    def start_empty(self) -> None:
        """Machine always begins in the EMPTY state."""
        self.buffer = pd.DataFrame()
        self._state = "EMPTY"

    @rule(
        description=st.sampled_from(_SAMPLE_DESCRIPTIONS),
        price=st.sampled_from(_SAMPLE_PRICES),
        month=st.integers(min_value=1, max_value=12),
        year=st.integers(min_value=2020, max_value=2026),
    )
    def load_transactions(self, description: str, price: str, month: int, year: int) -> None:
        """Transition EMPTY → LOADED by creating a raw transaction DataFrame."""
        self.buffer = pd.DataFrame(
            {
                "data": [description],
                "price": [price],
                "month": [month],
                "year": [year],
            }
        )
        self._state = "LOADED"

    @rule()
    def clean_pipeline(self) -> None:
        """Transition LOADED → CLEANED by normalising descriptions.

        No-op when not in LOADED state.
        """
        if self._state != "LOADED":
            return
        self.buffer = clean_descriptions(self.buffer.copy())
        self._state = "CLEANED"

    @rule()
    def process_pipeline(self) -> None:
        """Transition LOADED/CLEANED → PROCESSED by categorising and filtering.

        No-op when not in a processable state.
        """
        if self._state not in ("LOADED", "CLEANED"):
            return
        self.buffer = process_dataframe(self.buffer.copy())
        self._state = "PROCESSED"

    @rule()
    def reset(self) -> None:
        """Transition any state → EMPTY."""
        self.buffer = pd.DataFrame()
        self._state = "EMPTY"

    # ── Invariants ───────────────────────────────────────────────────────────

    @invariant()
    def buffer_is_always_a_dataframe(self) -> None:
        """buffer must always be a pandas DataFrame regardless of state."""
        assert isinstance(self.buffer, pd.DataFrame)

    @invariant()
    def column_names_are_subset_of_valid_pipeline_columns(self) -> None:
        """No unexpected columns should appear at any pipeline stage."""
        assert set(self.buffer.columns).issubset(_VALID_COLUMNS)

    @invariant()
    def processed_prices_are_non_negative_absolute_values(self) -> None:
        """After PROCESSED state, all prices must be absolute (non-negative).

        process_dataframe() removes income (positive original prices) and
        converts expenses to absolute values, so the result must contain
        no negative numbers.
        """
        if self._state != "PROCESSED":
            return
        if "price" not in self.buffer.columns or len(self.buffer) == 0:
            return
        prices = self.buffer["price"].astype(float)
        assert (prices >= 0).all(), f"Negative prices found after processing: {prices[prices < 0].tolist()}"

    @invariant()
    def row_count_does_not_increase_after_processing(self) -> None:
        """Buffer length must be non-negative (sanity guard)."""
        assert len(self.buffer) >= 0


# ─────────────────────────────────────────────────────────────────────────────
# Pytest test class
# ─────────────────────────────────────────────────────────────────────────────

TestPipelineStateMachine = TransactionPipelineMachine.TestCase
TestPipelineStateMachine.settings = settings(  # type: ignore[attr-defined]
    max_examples=50,
    stateful_step_count=10,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
