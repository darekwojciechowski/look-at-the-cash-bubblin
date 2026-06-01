"""Behavior-first tests for the main module pipeline orchestration."""

from pathlib import Path

import pandas as pd
import pytest

import main as main_module


def _write_demo_ipko_csv(path: Path) -> None:
    """Write a realistic 9-column IPKO CSV with mixed expense and income rows."""
    rows = [
        ["2024-01-15", "2024-01-15", "purchase", "-50.0", "PLN", "orlen fuel station", "", "orlen", ""],
        ["2024-01-16", "2024-01-16", "purchase", "-20.0", "PLN", "biedronka groceries", "", "biedronka", ""],
        ["2024-01-20", "2024-01-20", "transfer", "5000.0", "PLN", "salary transfer", "", "salary", ""],
        ["2024-01-21", "2024-01-21", "transfer", "120.0", "PLN", "bonus", "", "bonus", ""],
    ]
    df = pd.DataFrame(rows, columns=[f"col_{idx}" for idx in range(9)])
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="cp1250")


def _expected_outputs(root: Path) -> dict[str, Path]:
    """Return the six output paths produced by main()."""
    return {
        "gs_expenses": root / "google_sheets_expenses.csv",
        "gs_income": root / "google_sheets_income.csv",
        "processed_expenses": root / "data" / "processed_transactions.csv",
        "processed_income": root / "data" / "processed_income.csv",
        "unassigned_expenses": root / "unassigned_transactions.csv",
        "unassigned_income": root / "unassigned_income.csv",
    }


@pytest.mark.unit
class TestMainWorkflow:
    """Behavior-first assertions for visible main() outcomes."""

    def test_main_creates_artifacts_with_expected_schema(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """main() writes all expected artifacts with stable column contracts."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(main_module, "setup_logging", lambda: None)
        _write_demo_ipko_csv(tmp_path / "data" / "demo_ipko.csv")

        # Act
        main_module.main()
        outputs = _expected_outputs(tmp_path)

        # Assert
        for output_path in outputs.values():
            assert output_path.exists(), f"Expected output file was not created: {output_path}"

        processed_expenses = pd.read_csv(outputs["processed_expenses"], encoding="utf-8-sig")
        assert list(processed_expenses.columns) == ["txn_id", "day", "month", "year", "category", "amount"]
        assert len(processed_expenses) == 2
        assert processed_expenses["txn_id"].str.match(r"^v1:[0-9a-f]{64}$").all()
        assert (processed_expenses["amount"].astype(float) > 0).all()

        processed_income = pd.read_csv(outputs["processed_income"], encoding="utf-8-sig")
        assert list(processed_income.columns) == ["txn_id", "day", "month", "year", "category", "amount"]
        assert len(processed_income) == 2
        assert processed_income["txn_id"].str.match(r"^v1:[0-9a-f]{64}$").all()
        assert (processed_income["amount"].astype(float) > 0).all()

        sheets_expenses = pd.read_csv(outputs["gs_expenses"], sep="\t")
        assert list(sheets_expenses.columns) == [
            "Txn_Id",
            "Day",
            "Month",
            "Year",
            "Item",
            "Category",
            "Amount",
            "Importance",
        ]
        assert len(sheets_expenses) == len(processed_expenses)

        sheets_income = pd.read_csv(outputs["gs_income"], sep="\t")
        assert list(sheets_income.columns) == [
            "Txn_Id",
            "Day",
            "Month",
            "Year",
            "Item",
            "Category",
            "Amount",
            "Importance",
        ]
        assert len(sheets_income) == len(processed_income)

    def test_main_propagates_csv_read_errors_without_writing_outputs(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If CSV read fails, main() surfaces the error and creates no artifacts."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(main_module, "setup_logging", lambda: None)

        def _raise_file_not_found(*_args: object, **_kwargs: object) -> pd.DataFrame:
            raise FileNotFoundError("File not found")

        monkeypatch.setattr(main_module, "read_transaction_csv", _raise_file_not_found)

        # Act + Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            main_module.main()

        assert not (tmp_path / "google_sheets_expenses.csv").exists()
        assert not (tmp_path / "google_sheets_income.csv").exists()
        assert not (tmp_path / "data" / "processed_transactions.csv").exists()
        assert not (tmp_path / "data" / "processed_income.csv").exists()

    def test_main_propagates_processing_errors_before_exports(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If processing fails, main() surfaces the error and export artifacts are not written."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(main_module, "setup_logging", lambda: None)
        _write_demo_ipko_csv(tmp_path / "data" / "demo_ipko.csv")

        def _raise_processing_error(*_args: object, **_kwargs: object) -> pd.DataFrame:
            raise KeyError("Invalid column")

        monkeypatch.setattr(main_module, "process_dataframe", _raise_processing_error)

        # Act + Assert
        with pytest.raises(KeyError, match="Invalid column"):
            main_module.main()

        assert not (tmp_path / "google_sheets_expenses.csv").exists()
        assert not (tmp_path / "google_sheets_income.csv").exists()
        assert not (tmp_path / "unassigned_transactions.csv").exists()
        assert not (tmp_path / "unassigned_income.csv").exists()
