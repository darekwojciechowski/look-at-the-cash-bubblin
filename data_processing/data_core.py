"""Core transformation pipeline: description cleaning and transaction categorization."""

import pandas as pd
from loguru import logger

from data_processing.mappings import lookup_income_category, mappings

# Keyword replacements applied to IPKO transaction descriptions during cleaning.
# Separated from the function so callers can inject a different mapping for other
# bank formats without modifying clean_descriptions itself (OCP).
IPKO_DESCRIPTION_REPLACEMENTS: dict[str, str] = {
    "purchase in terminal - mobile code": "terminal purchase",
    "web payment - mobile code": "web payment",
    "transfer from account": "account transfer",
    "transfer to account": "account deposit",
    "recipient account": "recipient",
    "phone number": "phone",
    "location: address": "location",
    "title": "description",
    "payer references": "references",
    "orlen": "Orlen gas station",
    "starbucks": "Starbucks coffee shop",
    "mcd": "McDonalds restaurant",
    "netflix": "Netflix subscription",
    "investment platform deposit": "investment deposit",
    "amazon": "Amazon shopping",
    "piotrkowska 157a": "Biedronka - Piotrkowska 157a",
    "drewnowska 58a": "Manufaktura - Drewnowska 58a",
    "pabianicka 245": "Port Łódź - Pabianicka 245",
    "maratonska 24": "Retkinia Mall - Maratońska 24",
}


def clean_descriptions(
    df: pd.DataFrame,
    replacements: dict[str, str] = IPKO_DESCRIPTION_REPLACEMENTS,
) -> pd.DataFrame:
    """Replace substrings in the ``data`` column to normalize transaction text.

    Args:
        df: DataFrame with a ``data`` column containing raw transaction text.
        replacements: Substring-to-replacement mapping. Defaults to
            ``IPKO_DESCRIPTION_REPLACEMENTS``. Pass a custom dict to support
            other bank formats without modifying this function.

    Returns:
        DataFrame with the ``data`` column cleaned in place.
    """
    for old, new in replacements.items():
        df["data"] = df["data"].str.replace(old, new, regex=False)

    return df


_PROCESSED_COLUMNS: list[str] = ["txn_id", "day", "month", "year", "amount", "category", "data"]


def _prepare_common(df: pd.DataFrame) -> pd.DataFrame:
    """Run the steps shared by the expense and income tracks.

    Cleans descriptions, applies the expense keyword map to detect refund/
    reversal rows (REMOVE_ENTRY), drops those, coerces ``amount`` to float,
    and drops rows whose amount cannot be parsed. The provisional expense
    ``category`` column is preserved on the returned DataFrame so the
    expense track can reuse it without re-mapping; the income track
    overwrites it via ``lookup_income_category``.

    In production, ``main.py`` calls ``assign_txn_ids`` before this function
    so the ``txn_id`` column is always present. Tests that construct minimal
    DataFrames directly may omit it — in that case we synthesize an empty
    placeholder so the downstream column schema stays stable.
    """
    if "txn_id" not in df.columns:
        df = df.copy()
        df["txn_id"] = ""
    df = clean_descriptions(df)
    df["category"] = df["data"].map(mappings)
    df = df[df["category"] != "REMOVE_ENTRY"].reset_index(drop=True)
    df["amount"] = df["amount"].astype(float)
    nan_count = int(df["amount"].isna().sum())
    if nan_count:
        logger.warning("[DATA] Dropping {} row(s) with unparseable amount values", nan_count)
    df = df[df["amount"].notna()].reset_index(drop=True)
    return df


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned and categorized expense DataFrame ready for export.

    Refunds, reversals, and income (positive amounts) are excluded. Amounts are
    converted to absolute values. Output columns are
    ``[txn_id, day, month, year, amount, category, data]``.

    Args:
        df: DataFrame produced by ``ipko_import`` with columns
            ``amount``, ``data``, ``month``, ``year``, ``day``.

    Returns:
        Cleaned and categorized DataFrame ready for export.
    """
    df = _prepare_common(df)
    df = df[df["amount"] <= 0].reset_index(drop=True)
    df["amount"] = df["amount"].abs().astype(str)
    return df[_PROCESSED_COLUMNS]


def process_income_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned and categorized income DataFrame ready for export.

    Refunds and expenses (non-positive amounts) are excluded. Amounts are
    stringified as-is — no absolute-value conversion, since income amounts
    are already positive. Output columns match the expense schema:
    ``[txn_id, day, month, year, amount, category, data]``.

    Args:
        df: DataFrame produced by ``ipko_import`` with columns
            ``amount``, ``data``, ``month``, ``year``, ``day``.

    Returns:
        Cleaned and categorized income DataFrame ready for export.
    """
    df = _prepare_common(df)
    df = df[df["amount"] > 0].reset_index(drop=True)
    df["amount"] = df["amount"].astype(str)
    df["category"] = df["data"].map(lookup_income_category)
    return df[_PROCESSED_COLUMNS]
