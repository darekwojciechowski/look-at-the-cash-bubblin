"""Stateful property-based tests for the PKO transaction pipeline.

Uses Hypothesis RuleBasedStateMachine to verify that the pipeline correctly
handles any valid sequence of state transitions (EMPTY → LOADED → CLEANED →
PROCESSED → EMPTY) and that cross-state invariants are never violated.

This technique catches ordering bugs and emergent state corruption that
per-function unit tests miss because they only test one transition at a time.
"""

from enum import StrEnum

import pandas as pd
import pytest
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, precondition, rule

from data_processing.data_core import clean_descriptions, process_dataframe
from tests.property_based.strategies import transaction_descriptions

# ─────────────────────────────────────────────────────────────────────────────
# State enum
# ─────────────────────────────────────────────────────────────────────────────


class PipelineState(StrEnum):
    EMPTY = "EMPTY"
    LOADED = "LOADED"
    CLEANED = "CLEANED"
    PROCESSED = "PROCESSED"


# Column sets per pipeline stage — used to enforce strict structural invariants.
_RAW_COLUMNS: frozenset[str] = frozenset({"data", "price", "month", "year"})
_PROCESSED_COLUMNS: list[str] = ["month", "year", "price", "category", "data"]

_SAMPLE_PRICES: list[str] = ["-100.0", "-50.0", "-200.0", "-15.0", "-30.0"]

# ─────────────────────────────────────────────────────────────────────────────
# State machine
# ─────────────────────────────────────────────────────────────────────────────


@settings(max_examples=50, stateful_step_count=50, deadline=None)
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
        self._state: PipelineState = PipelineState.EMPTY
        self._pre_process_count: int = 0

    # ── Transitions ──────────────────────────────────────────────────────────

    @initialize()
    def start_empty(self) -> None:
        """Machine always begins in the EMPTY state."""
        self.buffer = pd.DataFrame()
        self._state = PipelineState.EMPTY

    @rule(
        description=transaction_descriptions(),
        price=st.sampled_from(_SAMPLE_PRICES),
        month=st.integers(min_value=1, max_value=12),
        year=st.integers(min_value=2020, max_value=2026),
    )
    def load_transactions(self, description: str, price: str, month: int, year: int) -> None:
        """Transition any → LOADED by creating a raw transaction DataFrame."""
        self.buffer = pd.DataFrame({
            "data": [description],
            "price": [price],
            "month": [month],
            "year": [year],
        })
        self._state = PipelineState.LOADED

    @precondition(lambda self: self._state == PipelineState.LOADED)
    @rule()
    def clean_pipeline(self) -> None:
        """Transition LOADED → CLEANED by normalising descriptions."""
        self.buffer = clean_descriptions(self.buffer.copy())
        self._state = PipelineState.CLEANED

    @precondition(lambda self: self._state in (PipelineState.LOADED, PipelineState.CLEANED))
    @rule()
    def process_pipeline(self) -> None:
        """Transition LOADED/CLEANED → PROCESSED by categorising and filtering."""
        self._pre_process_count = len(self.buffer)
        self.buffer = process_dataframe(self.buffer.copy())
        self._state = PipelineState.PROCESSED

    @rule()
    def reset(self) -> None:
        """Transition any state → EMPTY."""
        self.buffer = pd.DataFrame()
        self._state = PipelineState.EMPTY

    # ── Invariants ───────────────────────────────────────────────────────────

    @invariant()
    def buffer_is_always_a_dataframe(self) -> None:
        """buffer must always be a pandas DataFrame regardless of state."""
        assert isinstance(self.buffer, pd.DataFrame)

    @invariant()
    def column_schema_matches_pipeline_state(self) -> None:
        """Column schema must match the expected structure for each pipeline state.

        PROCESSED state requires exactly [month, year, price, category, data].
        LOADED/CLEANED state columns must be a subset of the raw schema.
        EMPTY state imposes no column constraint.
        """
        if self._state == PipelineState.PROCESSED:
            assert list(self.buffer.columns) == _PROCESSED_COLUMNS, (
                f"Expected {_PROCESSED_COLUMNS}, got {list(self.buffer.columns)}"
            )
        elif self._state in (PipelineState.LOADED, PipelineState.CLEANED):
            assert set(self.buffer.columns).issubset(_RAW_COLUMNS), (
                f"Unexpected columns in {self._state}: {set(self.buffer.columns) - _RAW_COLUMNS}"
            )

    @invariant()
    def processed_prices_are_non_negative_absolute_values(self) -> None:
        """After PROCESSED state, all prices must be non-negative absolute values.

        process_dataframe() strips income (positive input prices) and converts
        expenses to absolute values; the result must never contain negatives.
        """
        if self._state != PipelineState.PROCESSED:
            return
        if "price" not in self.buffer.columns or len(self.buffer) == 0:
            return
        prices = self.buffer["price"].astype(float)
        assert (prices >= 0).all(), f"Negative prices after processing: {prices[prices < 0].tolist()}"

    @invariant()
    def row_count_does_not_increase_after_processing(self) -> None:
        """Processing must never add rows — filtering can only reduce or preserve count."""
        if self._state == PipelineState.PROCESSED:
            assert len(self.buffer) <= self._pre_process_count, (
                f"Row count grew from {self._pre_process_count} to {len(self.buffer)}"
            )


# ─────────────────────────────────────────────────────────────────────────────
# Pytest entry point
# ─────────────────────────────────────────────────────────────────────────────

TestPipelineStateMachine = pytest.mark.property(TransactionPipelineMachine.TestCase)
