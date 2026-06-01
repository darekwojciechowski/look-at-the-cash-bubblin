"""Integration tests for main() using real CSV input and file outputs."""

from pathlib import Path

import pandas as pd
import pytest

import main as main_module


def _write_demo_ipko_csv(path: Path) -> None:
    """Write a realistic 9-column IPKO CSV for end-to-end main() execution."""
    rows = [
        ["2024-02-01", "2024-02-01", "purchase", "-45.0", "PLN", "orlen fuel station", "", "orlen", ""],
        ["2024-02-02", "2024-02-02", "purchase", "-25.0", "PLN", "biedronka groceries", "", "biedronka", ""],
        ["2024-02-03", "2024-02-03", "transfer", "5500.0", "PLN", "salary february", "", "salary", ""],
        ["2024-02-04", "2024-02-04", "transfer", "200.0", "PLN", "freelance payout", "", "freelance", ""],
    ]
    df = pd.DataFrame(rows, columns=[f"col_{idx}" for idx in range(9)])
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="cp1250")


@pytest.mark.integration
class TestMainWorkflowIntegration:
    """Integration-level workflow checks for main()."""

    def test_main_workflow_with_real_csv(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() reads real CSV input and writes valid expense and income artifacts."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        _write_demo_ipko_csv(tmp_path / "data" / "demo_ipko.csv")

        # Act
        main_module.main()

        # Assert — processed outputs exist with stable schemas
        processed_expenses_path = tmp_path / "data" / "processed_transactions.csv"
        processed_income_path = tmp_path / "data" / "processed_income.csv"
        assert processed_expenses_path.exists()
        assert processed_income_path.exists()

        processed_expenses = pd.read_csv(processed_expenses_path, encoding="utf-8-sig")
        processed_income = pd.read_csv(processed_income_path, encoding="utf-8-sig")

        assert list(processed_expenses.columns) == ["txn_id", "day", "month", "year", "category", "amount"]
        assert list(processed_income.columns) == ["txn_id", "day", "month", "year", "category", "amount"]

        assert len(processed_expenses) == 2
        assert len(processed_income) == 2
        assert (processed_expenses["amount"].astype(float) > 0).all()
        assert (processed_income["amount"].astype(float) > 0).all()
        assert processed_expenses["txn_id"].str.match(r"^v1:[0-9a-f]{64}$").all()
        assert processed_income["txn_id"].str.match(r"^v1:[0-9a-f]{64}$").all()

        # Assert — Google Sheets outputs are tab-separated and row-aligned
        gs_expenses = pd.read_csv(tmp_path / "google_sheets_expenses.csv", sep="\t")
        gs_income = pd.read_csv(tmp_path / "google_sheets_income.csv", sep="\t")
        assert len(gs_expenses) == len(processed_expenses)
        assert len(gs_income) == len(processed_income)
        expected_gs_columns = ["Txn_Id", "Day", "Month", "Year", "Item", "Category", "Amount", "Importance"]
        assert list(gs_expenses.columns) == expected_gs_columns
        assert list(gs_income.columns) == expected_gs_columns
