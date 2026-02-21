"""Core transformation pipeline: description cleaning and transaction categorization."""

import numpy as np
import pandas as pd

from data_processing.mappings import mappings

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
        df["data"] = df["data"].str.replace(old, new)

    return df


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning and categorization pipeline on a transaction DataFrame.

    Steps applied in order:
    1. Normalize descriptions via ``clean_descriptions``.
    2. Assign a category to each row via ``mappings``.
    3. Drop ``REMOVE_ENTRY`` rows (refunds / reversals).
    4. Drop rows with positive prices (income).
    5. Strip the leading ``-`` from price strings.
    6. Reorder columns to ``[month, year, price, category, data]``.
    7. Drop rows where price is ``nan``.

    Args:
        df: DataFrame produced by ``ipko_import`` with columns
            ``price``, ``data``, ``month``, ``year``.

    Returns:
        Cleaned and categorized DataFrame ready for export.
    """
    # Clean transaction descriptions
    df = clean_descriptions(df)

    # Map categories
    df["category"] = df["data"].map(mappings)

    # Remove refund/return entries
    df = df[df["category"] != "REMOVE_ENTRY"].reset_index(drop=True)

    # Remove income (positive prices)
    df["price"] = df["price"].astype(float)
    df.loc[df["price"] > 0, "price"] = np.nan

    # Remove '-' from price column and convert to string
    df["price"] = df["price"].astype(str).str.replace("-", "")

    # Reorder columns
    desired_columns = ["month", "year", "price", "category", "data"]
    df = df[desired_columns]

    # Drop rows with NaN in 'price'
    df = df[df["price"] != "nan"].reset_index(drop=True)

    return df
