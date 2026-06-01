"""Tests for data_processing.exporter module.
Covers CSV and Google Sheets export, MISC transaction filtering, and Expense loading.
"""

from pathlib import Path
from unittest.mock import MagicMock, call, mock_open

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from data_processing.expense import get_data
from data_processing.exporter import (
    export_cleaned_income_data,
    export_for_google_sheets,
    export_income_for_google_sheets,
    export_misc_transactions,
    export_unassigned_income,
    export_unassigned_transactions_to_csv,
)


@pytest.mark.unit
class TestExportForGoogleSheets:
    """Test suite for Google Sheets export functionality."""

    def test_export_for_google_sheets_success(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Google Sheets export writes tab-separated data with stable columns."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Act
        output = export_for_google_sheets(sample_dataframe_with_categories)
        result = pd.read_csv(output, sep="\t")

        # Assert
        assert output.resolve() == (tmp_path / "google_sheets_expenses.csv").resolve()
        assert list(result.columns) == ["Txn_Id", "Day", "Month", "Year", "Item", "Category", "Amount", "Importance"]
        assert len(result) == len(sample_dataframe_with_categories)
        assert result["Amount"].map(lambda value: "," in str(value)).all()

    def test_export_for_google_sheets_empty_dataframe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Google Sheets export of an empty frame preserves the output schema."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        empty_df = pd.DataFrame(columns=["category", "amount", "month", "year", "data"])

        # Act
        output = export_for_google_sheets(empty_df)
        result = pd.read_csv(output, sep="\t")

        # Assert
        assert output.resolve() == (tmp_path / "google_sheets_expenses.csv").resolve()
        assert list(result.columns) == ["Txn_Id", "Day", "Month", "Year", "Item", "Category", "Amount", "Importance"]
        assert result.empty


@pytest.mark.unit
class TestExportMiscTransactions:
    """Test suite for MISC category transaction export."""

    def test_export_misc_transactions_filters_correctly(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Only MISC rows are written to unassigned_transactions.csv."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Act
        export_misc_transactions(sample_dataframe_with_categories)
        result = pd.read_csv(tmp_path / "unassigned_transactions.csv", encoding="utf-8-sig")

        # Assert
        assert list(result.columns) == [
            "txn_id",
            "day",
            "month",
            "year",
            "amount",
            "category",
            "data",
            "extracted_location",
            "google_maps_link",
        ]
        assert len(result) == 2
        assert set(result["category"]) == {"MISC"}

    def test_export_misc_transactions_no_misc_category(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Export still writes a schema-only file when no MISC rows are present."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        df = pd.DataFrame({
            "category": ["FOOD", "FUEL"],
            "amount": [100.0, 50.0],
            "day": [1, 2],
            "month": [1, 1],
            "year": [2023, 2023],
            "data": ["groceries", "fuel"],
        })

        # Act
        export_misc_transactions(df)
        result = pd.read_csv(tmp_path / "unassigned_transactions.csv", encoding="utf-8-sig")

        # Assert
        assert result.empty
        assert list(result.columns) == [
            "txn_id",
            "day",
            "month",
            "year",
            "amount",
            "category",
            "data",
            "extracted_location",
            "google_maps_link",
        ]

    def test_export_misc_transactions_empty_dataframe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Export handles empty input DataFrames and keeps stable headers."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        empty_df = pd.DataFrame(columns=["txn_id", "day", "month", "year", "amount", "category", "data"])

        # Act
        export_misc_transactions(empty_df)
        result = pd.read_csv(tmp_path / "unassigned_transactions.csv", encoding="utf-8-sig")

        # Assert
        assert result.empty
        assert list(result.columns) == [
            "txn_id",
            "day",
            "month",
            "year",
            "amount",
            "category",
            "data",
            "extracted_location",
            "google_maps_link",
        ]


@pytest.mark.unit
class TestExportUnassignedTransactions:
    """Test suite for unassigned transactions export."""

    def test_export_unassigned_transactions_to_csv(
        self,
        sample_dataframe_with_categories: pd.DataFrame,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unassigned export writes enriched location columns and stable order."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Act
        export_unassigned_transactions_to_csv(sample_dataframe_with_categories)
        result = pd.read_csv(tmp_path / "unassigned_transactions.csv", encoding="utf-8-sig")

        # Assert
        assert len(result) == len(sample_dataframe_with_categories)
        assert list(result.columns) == [
            "txn_id",
            "day",
            "month",
            "year",
            "amount",
            "category",
            "data",
            "extracted_location",
            "google_maps_link",
        ]
        assert "google_maps_link" in result.columns
        assert "extracted_location" in result.columns

    def test_export_unassigned_transactions_does_not_duplicate_txn_id_column(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        df = pd.DataFrame({
            "txn_id": ["v1:abc123"],
            "day": [1],
            "month": [1],
            "year": [2025],
            "amount": ["-50.00"],
            "category": ["MISC"],
            "data": ["biedronka"],
        })

        export_unassigned_transactions_to_csv(df)

        result = pd.read_csv(tmp_path / "unassigned_transactions.csv", encoding="utf-8-sig")
        assert list(result.columns).count("txn_id") == 1


@pytest.mark.unit
class TestExportFinalData:
    """Test suite for final data export operations."""

    def test_get_data_success(self, mocker: MockerFixture, csv_data_mock: str) -> None:
        """Test successful parsing of final data from CSV.

        Given: a mocked DictReader that returns two row dicts
        When:  get_data() is called
        Then:  two Expense-like objects are returned with the correct field values
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_dict_reader = mocker.patch("csv.DictReader")
        mock_dict_reader.return_value = iter([
            {"month": "1", "year": "2023", "category": "item1", "amount": "100"},
            {"month": "2", "year": "2023", "category": "item2", "amount": "200"},
        ])

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 2
        assert expenses[0].month == "1"
        assert expenses[0].year == "2023"
        assert expenses[0].item == "item1"
        assert expenses[0].amount == "100"
        assert expenses[1].month == "2"
        assert expenses[1].year == "2023"

    def test_get_data_empty_csv(self, mocker: MockerFixture) -> None:
        """Test parsing empty CSV file.

        Given: a mocked DictReader that yields no rows
        When:  get_data() is called
        Then:  an empty list is returned
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_dict_reader = mocker.patch("csv.DictReader")
        mock_dict_reader.return_value = iter([])

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 0


@pytest.mark.unit
class TestGetData:
    """Test suite for get_data function."""

    def test_get_data_creates_expenses(self, mocker: MockerFixture) -> None:
        """
        Test get_data creates Expense objects from CSV.

        Given: a mocked DictReader with two row dicts and a patched Expense constructor
        When:  get_data() is called
        Then:  the Expense constructor is called twice with the expected keyword arguments
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_dict_reader = mocker.patch("csv.DictReader")
        mock_expense = mocker.patch("data_processing.expense.Expense")
        mock_dict_reader.return_value = iter([
            {"month": "1", "year": "2023", "category": "item1", "amount": "100"},
            {"month": "2", "year": "2023", "category": "item2", "amount": "200"},
        ])
        mock_expense_instance = MagicMock()
        mock_expense.return_value = mock_expense_instance

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 2
        expected_calls = [
            call(month="1", year="2023", item="item1", amount="100"),
            call(month="2", year="2023", item="item2", amount="200"),
        ]
        mock_expense.assert_has_calls(expected_calls)

    def test_get_data_empty_csv(self, mocker: MockerFixture) -> None:
        """Test get_data with empty CSV file.

        Given: a mocked DictReader yielding no rows
        When:  get_data() is called
        Then:  an empty list is returned and Expense is never called
        """
        # Arrange
        mocker.patch("builtins.open", new_callable=mock_open)
        mock_dict_reader = mocker.patch("csv.DictReader")
        mock_expense = mocker.patch("data_processing.expense.Expense")
        mock_dict_reader.return_value = iter([])
        mock_expense_instance = MagicMock()
        mock_expense.return_value = mock_expense_instance

        # Act
        expenses = get_data()

        # Assert
        assert len(expenses) == 0
        mock_expense.assert_not_called()


@pytest.mark.unit
class TestExporterModuleImport:
    """Smoke tests for the public API surface of data_processing.exporter."""

    def test_module_imports_successfully(self) -> None:
        """Verify the exporter module imports without raising an error.

        Given: the data_processing.exporter module on the Python path
        When:  the module is imported
        Then:  no ImportError is raised
        """
        # Arrange + Act + Assert — top-level import already succeeded; reaching
        # this line proves the module loaded cleanly.
        import data_processing.exporter  # noqa: F401

    def test_get_data_accepts_path_parameter(self) -> None:
        """Verify get_data has a path parameter with the expected default.

        Given: get_data imported from data_processing.expense
        When:  the signature of get_data is inspected
        Then:  a 'path' parameter exists with default Path('data/processed_transactions.csv')
        """
        # Arrange
        import inspect

        # Act
        sig = inspect.signature(get_data)

        # Assert
        assert "path" in sig.parameters
        assert sig.parameters["path"].default == Path("data/processed_transactions.csv")

    def test_module_has_expected_functions(self) -> None:
        """Verify the exporter exposes its export functions and get_data lives in expense.

        Given: the data_processing.exporter and data_processing.expense modules
        When:  each expected function name is checked with hasattr and callable
        Then:  the export functions live in exporter and get_data lives in expense
        """
        # Arrange
        import data_processing.expense
        import data_processing.exporter

        expected_functions = [
            "export_for_google_sheets",
            "export_misc_transactions",
            "export_unassigned_transactions_to_csv",
        ]

        # Act + Assert
        for func_name in expected_functions:
            assert hasattr(data_processing.exporter, func_name)
            assert callable(getattr(data_processing.exporter, func_name))

        assert callable(data_processing.expense.get_data)
        assert not hasattr(data_processing.exporter, "get_data")


@pytest.fixture
def sample_income_dataframe() -> pd.DataFrame:
    return pd.DataFrame({
        "day": [1, 15],
        "month": [1, 1],
        "year": [2023, 2023],
        "amount": ["5000.0", "200.0"],
        "category": ["SALARY", "INCOME_MISC"],
        "data": ["wynagrodzenie january", "unknown deposit"],
    })


@pytest.mark.unit
class TestExportIncomeForGoogleSheets:
    def test_writes_expected_headers_and_separator(
        self, sample_income_dataframe: pd.DataFrame, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        out = export_income_for_google_sheets(sample_income_dataframe)

        assert out.name == "google_sheets_income.csv"
        result = pd.read_csv(out, sep="\t")
        assert list(result.columns) == ["Txn_Id", "Day", "Month", "Year", "Item", "Category", "Amount", "Importance"]
        assert len(result) == 2

    def test_amount_uses_comma_decimal(
        self, sample_income_dataframe: pd.DataFrame, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        out = export_income_for_google_sheets(sample_income_dataframe)
        content = out.read_text(encoding="utf-8")
        assert "5000,0" in content


@pytest.mark.unit
class TestExportCleanedIncomeData:
    def test_writes_utf8_sig_with_income_schema(
        self, sample_income_dataframe: pd.DataFrame, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "income.csv"

        export_cleaned_income_data(sample_income_dataframe, output_file=target)

        raw = target.read_bytes()
        assert raw.startswith(b"\xef\xbb\xbf"), "expected utf-8-sig BOM"
        result = pd.read_csv(target, encoding="utf-8-sig")
        assert list(result.columns) == ["txn_id", "day", "month", "year", "category", "amount"]


@pytest.mark.unit
class TestExportUnassignedIncome:
    def test_filters_on_income_misc(
        self, sample_income_dataframe: pd.DataFrame, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        export_unassigned_income(sample_income_dataframe)

        result = pd.read_csv(tmp_path / "unassigned_income.csv", encoding="utf-8-sig")
        assert len(result) == 1
        assert result["category"].iloc[0] == "INCOME_MISC"

    def test_no_location_columns(
        self, sample_income_dataframe: pd.DataFrame, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        export_unassigned_income(sample_income_dataframe)

        result = pd.read_csv(tmp_path / "unassigned_income.csv", encoding="utf-8-sig")
        assert "extracted_location" not in result.columns
        assert "google_maps_link" not in result.columns
        assert list(result.columns) == ["txn_id", "day", "month", "year", "amount", "category", "data"]
