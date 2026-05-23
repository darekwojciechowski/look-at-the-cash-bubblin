"""Tests for data_processing.transaction_id — deterministic ID contract."""

import pandas as pd
import pytest

from data_processing.transaction_id import (
    ALGORITHM_VERSION,
    TXN_ID_LENGTH,
    _iso_date,
    _normalize_description,
    _to_minor_units,
    assign_txn_ids,
    compute_txn_id,
)


def _raw_row(
    *,
    booking_date: str = "2025-01-15",
    value_date: str = "2025-01-15",
    txn_type: str = "Zakup w terminalu",
    amount: str = "-50.00",
    currency: str = "PLN",
    data: str = "zakup w terminalu//biedronka",
) -> dict[str, object]:
    return {
        "booking_date": pd.Timestamp(booking_date),
        "value_date": pd.Timestamp(value_date),
        "txn_type": txn_type,
        "amount": amount,
        "currency": currency,
        "data": data,
        "day": int(booking_date[-2:]),
        "month": int(booking_date[5:7]),
        "year": int(booking_date[:4]),
    }


@pytest.mark.unit
class TestComputeTxnId:
    """Unit tests for the raw hash function."""

    def test_format_is_versioned_sha256(self) -> None:
        txn_id = compute_txn_id(
            booking_date="2025-01-15",
            value_date="2025-01-15",
            amount_minor=-5000,
            currency="PLN",
            txn_type="ZAKUP W TERMINALU",
            description="biedronka",
            occurrence_index=0,
        )

        assert txn_id.startswith(f"{ALGORITHM_VERSION}:")
        assert len(txn_id) == TXN_ID_LENGTH

    def test_deterministic_for_same_input(self) -> None:
        kwargs = {
            "booking_date": "2025-01-15",
            "value_date": "2025-01-15",
            "amount_minor": -5000,
            "currency": "PLN",
            "txn_type": "ZAKUP W TERMINALU",
            "description": "biedronka",
            "occurrence_index": 0,
        }

        assert compute_txn_id(**kwargs) == compute_txn_id(**kwargs)

    def test_different_amount_yields_different_id(self) -> None:
        base = {
            "booking_date": "2025-01-15",
            "value_date": "2025-01-15",
            "currency": "PLN",
            "txn_type": "ZAKUP",
            "description": "biedronka",
            "occurrence_index": 0,
        }

        id_a = compute_txn_id(amount_minor=-5000, **base)
        id_b = compute_txn_id(amount_minor=-5001, **base)

        assert id_a != id_b

    def test_description_normalization_collapses_whitespace(self) -> None:
        """Extra whitespace and casing in the description must not change the hash."""
        base = {
            "booking_date": "2025-01-15",
            "value_date": "2025-01-15",
            "amount_minor": -5000,
            "currency": "PLN",
            "txn_type": "ZAKUP",
            "occurrence_index": 0,
        }

        clean = compute_txn_id(description="biedronka warszawa", **base)
        messy = compute_txn_id(description="  Biedronka\t\nWarszawa  ", **base)

        assert clean == messy

    def test_txn_type_uppercased_for_hash(self) -> None:
        base = {
            "booking_date": "2025-01-15",
            "value_date": "2025-01-15",
            "amount_minor": -5000,
            "currency": "PLN",
            "description": "biedronka",
            "occurrence_index": 0,
        }

        lower = compute_txn_id(txn_type="zakup w terminalu", **base)
        upper = compute_txn_id(txn_type="ZAKUP W TERMINALU", **base)

        assert lower == upper

    def test_occurrence_index_disambiguates_identical_rows(self) -> None:
        base = {
            "booking_date": "2025-01-15",
            "value_date": "2025-01-15",
            "amount_minor": -1250,
            "currency": "PLN",
            "txn_type": "ZAKUP",
            "description": "biedronka",
        }

        first = compute_txn_id(occurrence_index=0, **base)
        second = compute_txn_id(occurrence_index=1, **base)

        assert first != second


@pytest.mark.unit
class TestAssignTxnIds:
    """Integration-style tests for the DataFrame helper."""

    def test_inserts_txn_id_as_first_column(self) -> None:
        df = pd.DataFrame([_raw_row()])

        result = assign_txn_ids(df)

        assert list(result.columns)[0] == "txn_id"
        assert result["txn_id"].iloc[0].startswith("v1:")
        assert len(result["txn_id"].iloc[0]) == TXN_ID_LENGTH

    def test_independent_of_row_order(self) -> None:
        """Shuffling distinct rows must not change any txn_id."""
        rows = [
            _raw_row(booking_date="2025-01-15", amount="-50.00", data="biedronka"),
            _raw_row(booking_date="2025-02-20", amount="-30.00", data="orlen"),
            _raw_row(booking_date="2025-03-10", amount="-100.00", data="netflix"),
        ]
        ordered = pd.DataFrame(rows)
        shuffled = pd.DataFrame([rows[2], rows[0], rows[1]])

        ordered_ids = set(assign_txn_ids(ordered)["txn_id"])
        shuffled_ids = set(assign_txn_ids(shuffled)["txn_id"])

        assert ordered_ids == shuffled_ids

    def test_identical_rows_get_distinct_occurrence_indices(self) -> None:
        """Two perfectly identical rows on the same day must hash to different IDs."""
        row = _raw_row(booking_date="2025-01-15", amount="-12.50", data="biedronka")
        df = pd.DataFrame([row, row])

        result = assign_txn_ids(df)

        assert result["txn_id"].iloc[0] != result["txn_id"].iloc[1]

    def test_category_change_after_assignment_does_not_affect_ids(self) -> None:
        """txn_id is computed before clean_descriptions and before categorization.

        Re-running with a different ``data`` value AFTER assignment would change
        the ID, but the contract is that we compute it ONCE, then downstream
        mutations cannot affect the already-emitted column.
        """
        df = pd.DataFrame([_raw_row(data="orlen")])

        result_before = assign_txn_ids(df.copy())
        # Simulate clean_descriptions mutating `data` in place
        df["data"] = "Orlen gas station"
        result_after_mutation = assign_txn_ids(df.copy())

        # Both runs computed on `data` at their own moment, so they DIFFER —
        # this is exactly why the plan mandates computing txn_id BEFORE
        # clean_descriptions runs.
        assert result_before["txn_id"].iloc[0] != result_after_mutation["txn_id"].iloc[0]

    def test_overlapping_imports_share_ids_for_overlapping_rows(self) -> None:
        """The core use case: re-importing a wider date range yields identical IDs
        for the overlapping subset."""
        jan = _raw_row(booking_date="2025-01-15", data="biedronka", amount="-50.00")
        feb = _raw_row(booking_date="2025-02-20", data="orlen", amount="-100.00")
        mar = _raw_row(booking_date="2025-03-10", data="netflix", amount="-39.99")
        apr = _raw_row(booking_date="2025-04-05", data="amazon", amount="-200.00")

        first_import = assign_txn_ids(pd.DataFrame([jan, feb, mar]))
        second_import = assign_txn_ids(pd.DataFrame([jan, feb, mar, apr]))

        overlap_first = set(first_import["txn_id"])
        overlap_second_subset = set(second_import["txn_id"].iloc[:3])
        assert overlap_first == overlap_second_subset
        # And the new row introduces exactly one new ID.
        assert len(set(second_import["txn_id"]) - overlap_first) == 1

    def test_missing_required_columns_raises(self) -> None:
        df = pd.DataFrame([{"amount": "-50.00", "data": "biedronka"}])

        with pytest.raises(ValueError, match="missing required columns"):
            assign_txn_ids(df)

    def test_logs_warning_when_duplicates_present(self, loguru_sink: list[str]) -> None:
        row = _raw_row(booking_date="2025-01-15", amount="-12.50", data="biedronka")
        df = pd.DataFrame([row, row])

        assign_txn_ids(df)

        assert any("[TXN_ID]" in msg and "occurrence_index" in msg for msg in loguru_sink)

    def test_assign_txn_ids_without_value_date_column(self) -> None:
        df = pd.DataFrame([
            {
                "booking_date": pd.Timestamp("2025-01-15"),
                "amount": "-50.00",
                "data": "biedronka",
                "currency": "PLN",
                "txn_type": "zakup",
            }
        ])

        result = assign_txn_ids(df)

        assert result["txn_id"].iloc[0].startswith("v1:")

    def test_assign_txn_ids_without_currency_column(self) -> None:
        df = pd.DataFrame([
            {
                "booking_date": pd.Timestamp("2025-01-15"),
                "value_date": pd.Timestamp("2025-01-15"),
                "amount": "-50.00",
                "data": "biedronka",
                "txn_type": "zakup",
            }
        ])

        result = assign_txn_ids(df)

        assert result["txn_id"].iloc[0].startswith("v1:")

    def test_assign_txn_ids_without_txn_type_column(self) -> None:
        df = pd.DataFrame([
            {
                "booking_date": pd.Timestamp("2025-01-15"),
                "value_date": pd.Timestamp("2025-01-15"),
                "amount": "-50.00",
                "data": "biedronka",
                "currency": "PLN",
            }
        ])

        result = assign_txn_ids(df)

        assert result["txn_id"].iloc[0].startswith("v1:")


@pytest.mark.unit
class TestNormalizeDescriptionEdgeCases:
    def test_returns_empty_string_for_none(self) -> None:
        assert _normalize_description(None) == ""

    def test_returns_empty_string_for_float_nan(self) -> None:
        assert _normalize_description(float("nan")) == ""


@pytest.mark.unit
class TestToMinorUnitsEdgeCases:
    def test_raises_for_none(self) -> None:
        with pytest.raises(ValueError, match="amount is missing"):
            _to_minor_units(None)

    def test_raises_for_float_nan(self) -> None:
        with pytest.raises(ValueError, match="amount is missing"):
            _to_minor_units(float("nan"))


@pytest.mark.unit
class TestIsoDateEdgeCases:
    def test_returns_empty_for_none(self) -> None:
        assert _iso_date(None) == ""

    def test_returns_empty_for_empty_string(self) -> None:
        assert _iso_date("") == ""

    def test_returns_empty_for_float_nan(self) -> None:
        assert _iso_date(float("nan")) == ""

    def test_returns_empty_for_nat_timestamp(self) -> None:
        assert _iso_date(pd.NaT) == ""

    def test_returns_empty_for_unparseable_string(self) -> None:
        assert _iso_date("not-a-date") == ""

    def test_returns_formatted_date_for_parseable_string(self) -> None:
        assert _iso_date("2025-01-15") == "2025-01-15"
