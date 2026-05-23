"""Deterministic transaction ID assignment for cross-import deduplication.

Each row produced by ``ipko_import`` is assigned a stable, content-derived
``txn_id`` that downstream consumers (e.g. the Financial Dashboard) use as a
UNIQUE idempotency key. Algorithm is frozen at ``v1``; any change to the
fields, normalization, or layout must bump the version prefix so previously
emitted IDs remain valid.

Algorithm v1 (PKO, single-account):

    txn_id = "v1:" + sha256_hex(
        booking_date | value_date | amount_minor | currency
        | txn_type_upper | description_norm | occurrence_index
    )

The hash is computed **before** ``clean_descriptions`` and **before** the
sign of ``amount`` is stripped — both transformations would otherwise
destabilize the ID across runs and across the expense/income tracks.
"""

import hashlib
import re
import unicodedata
from typing import Any

import pandas as pd
from loguru import logger

ALGORITHM_VERSION: str = "v1"
TXN_ID_LENGTH: int = 67  # len("v1:") + 64 hex chars

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_description(desc: object) -> str:
    """Apply NFKC + lowercase + whitespace-collapse to a description string.

    Punctuation, accents, and embedded references (e.g. "REF: 12345") are
    preserved — they carry uniqueness and must contribute to the hash.
    """
    if desc is None or (isinstance(desc, float) and pd.isna(desc)):
        return ""
    text = unicodedata.normalize("NFKC", str(desc))
    text = text.lower()
    return _WHITESPACE_RE.sub(" ", text).strip()


def _to_minor_units(amount: object) -> int:
    """Convert a signed decimal amount to integer minor units (grosze).

    Accepts ``float``, ``int``, or numeric strings (with ``.`` or ``,`` as
    decimal separator). Never uses float comparison against the hash —
    rounds half-away-from-zero to the nearest grosz.
    """
    if amount is None or (isinstance(amount, float) and pd.isna(amount)):
        raise ValueError("Cannot compute txn_id: amount is missing")
    value = float(amount) if isinstance(amount, int | float) else float(str(amount).replace(",", "."))
    # round() in Python is banker's rounding; use explicit half-away-from-zero
    # so -1.005 -> -101 (not -100) for stability.
    sign = -1 if value < 0 else 1
    return sign * int(abs(value) * 100 + 0.5)


def _iso_date(value: object) -> str:
    """Format a date-like value as ISO ``YYYY-MM-DD``; missing values become ``""``."""
    if value is None or value == "" or (isinstance(value, float) and pd.isna(value)):
        return ""
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):  # pragma: no cover
            return ""
        return str(value.strftime("%Y-%m-%d"))
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return str(parsed.strftime("%Y-%m-%d"))


def compute_txn_id(
    booking_date: str,
    value_date: str,
    amount_minor: int,
    currency: str,
    txn_type: str,
    description: str,
    occurrence_index: int,
) -> str:
    """Compute a single deterministic ``txn_id`` from normalized fields.

    All inputs must already be normalized except ``txn_type`` (uppercased
    and stripped here) and ``description`` (NFKC + lowercase + whitespace
    collapse here). This is the single source of truth for the hash layout;
    ``assign_txn_ids`` calls it once per row.
    """
    payload = "|".join([
        booking_date,
        value_date,
        str(amount_minor),
        currency.strip().upper(),
        txn_type.strip().upper(),
        _normalize_description(description),
        str(occurrence_index),
    ])
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{ALGORITHM_VERSION}:{digest}"


def assign_txn_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with a ``txn_id`` column inserted as the first column.

    Expects the schema produced by ``ipko_import``: ``booking_date``,
    ``value_date``, ``amount``, ``currency``, ``txn_type``, and ``data`` (the
    merged raw description). Rows are grouped by all hash fields within the
    same ``booking_date``; identical-row collisions receive a 0-based
    ``occurrence_index`` so two truly identical purchases on the same day
    still receive distinct IDs.

    Fails fast on missing required columns or unparseable amounts — a row
    that cannot produce a txn_id is a contract violation, not an edge case.
    """
    required = {"booking_date", "amount", "data"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"assign_txn_ids: missing required columns {sorted(missing)}")

    df = df.copy()

    booking_dates: pd.Series[Any] = df["booking_date"].apply(_iso_date)
    if "value_date" in df.columns:
        value_dates: pd.Series[Any] = df["value_date"].apply(_iso_date)
    else:
        value_dates = pd.Series([""] * len(df), index=df.index)
    amount_minors = df["amount"].apply(_to_minor_units)
    if "currency" in df.columns:
        currencies = df["currency"].astype(str).str.strip().str.upper()
    else:
        currencies = pd.Series(["PLN"] * len(df), index=df.index)
    if "txn_type" in df.columns:
        txn_types_norm = df["txn_type"].astype(str).str.strip().str.upper()
    else:
        txn_types_norm = pd.Series([""] * len(df), index=df.index)
    descriptions_norm = df["data"].apply(_normalize_description)

    group_key = pd.DataFrame({
        "bd": booking_dates,
        "vd": value_dates,
        "am": amount_minors,
        "cu": currencies,
        "tt": txn_types_norm,
        "dn": descriptions_norm,
    })
    occurrence = group_key.groupby(list(group_key.columns), sort=False).cumcount()

    txn_ids: list[str] = [
        compute_txn_id(
            booking_date=bd,
            value_date=vd,
            amount_minor=int(am),
            currency=str(cu),
            txn_type=str(tt),
            description=str(desc),
            occurrence_index=int(occ),
        )
        for bd, vd, am, cu, tt, desc, occ in zip(
            booking_dates,
            value_dates,
            amount_minors,
            currencies,
            txn_types_norm,
            df["data"],
            occurrence,
            strict=True,
        )
    ]

    duplicates = int((occurrence > 0).sum())
    if duplicates > 0:
        logger.warning(
            f"[TXN_ID] {duplicates} row(s) share identical hash fields within the same booking_date; "
            "occurrence_index was used to distinguish them (re-export from bank may shuffle IDs in these groups)"
        )

    df.insert(0, "txn_id", txn_ids)
    return df
