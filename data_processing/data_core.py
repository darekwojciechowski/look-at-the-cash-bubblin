import numpy as np
import pandas as pd

from data_processing.mappings import mappings


def clean_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the 'data' column in the DataFrame by replacing specific patterns with shorter or corrected text.

    Parameters:
    df (pandas.DataFrame): The input DataFrame with a column named 'data'.

    Returns:
    pandas.DataFrame: The DataFrame with the cleaned 'data' column.
    """
    replacements = {
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

    for old, new in replacements.items():
        df["data"] = df["data"].str.replace(old, new)

    return df


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the DataFrame: clean, categorize, and filter transactions.
    Returns the cleaned and categorized DataFrame.
    """
    # Clean transaction descriptions
    df = clean_date(df)

    # Map categories
    df["category"] = df["data"].map(mappings)

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

    # Remove unwanted markers from category
    df["category"] = df["category"].astype(str).str.replace("🔖🔖🔖", "")

    return df
