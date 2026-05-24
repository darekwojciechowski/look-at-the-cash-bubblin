"""Default output paths for processed CSVs.

Centralised here so callers in main.py and exporter.py reference a single
source of truth instead of duplicating Path() literals.
"""

from pathlib import Path

GOOGLE_SHEETS_EXPENSES_PATH: Path = Path("google_sheets_expenses.csv")
GOOGLE_SHEETS_INCOME_PATH: Path = Path("google_sheets_income.csv")
PROCESSED_TRANSACTIONS_PATH: Path = Path("data/processed_transactions.csv")
PROCESSED_INCOME_PATH: Path = Path("data/processed_income.csv")
UNASSIGNED_TRANSACTIONS_PATH: Path = Path("unassigned_transactions.csv")
UNASSIGNED_INCOME_PATH: Path = Path("unassigned_income.csv")
