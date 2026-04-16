"""Audit log tests for the PKO transaction pipeline.

In fintech, an audit trail is a compliance requirement, not an option.
These tests verify that the correct events are emitted to the log at each
pipeline stage so that:
  - Operators can confirm that a file was loaded and with which encoding.
  - Compliance tooling can replay the sequence of operations.
  - On-call engineers can diagnose failures from logs alone.

Markers: unit
"""

import pandas as pd
import pytest
from loguru import logger
from pytest_mock import MockerFixture

from config.logging_setup import log_dataframe_preview, setup_logging
from data_processing.data_imports import read_transaction_csv
from data_processing.exporter import export_for_google_sheets, export_misc_transactions

# ─────────────────────────────────────────────────────────────────────────────
# 1. setup_logging audit
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestSetupLoggingAudit:
    """setup_logging() must configure two handlers and emit an init message."""

    def test_emits_logging_initialized_message(self, mocker: MockerFixture) -> None:
        """setup_logging() logs 'Logging initialized' after configuration.

        Given: logger.remove, logger.level, and logger.add are patched
        When:  setup_logging() is called
        Then:  logger.info is called with a message containing 'Logging initialized'
        """
        # Arrange
        mocker.patch.object(logger, "remove")
        mocker.patch.object(logger, "level")
        mocker.patch.object(logger, "add")
        mock_info = mocker.patch.object(logger, "info")

        # Act
        setup_logging()

        # Assert
        mock_info.assert_called_once()
        assert "Logging initialized" in mock_info.call_args[0][0]

    def test_logger_add_called_twice_for_stderr_and_file(self, mocker: MockerFixture) -> None:
        """setup_logging() registers exactly two handlers: stderr and file.

        Given: logger.remove, logger.level, and logger.info are patched
        When:  setup_logging() is called
        Then:  logger.add is called exactly twice
        """
        # Arrange
        mocker.patch.object(logger, "remove")
        mocker.patch.object(logger, "level")
        mocker.patch.object(logger, "info")
        mock_add = mocker.patch.object(logger, "add")

        # Act
        setup_logging()

        # Assert
        assert mock_add.call_count == 2

    def test_is_defensive_against_os_error_during_file_handler_setup(
        self, mocker: MockerFixture, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """setup_logging() prints the error and does not re-raise on OSError.

        Given: logger.add raises OSError (e.g. disk full or permission denied)
        When:  setup_logging() is called
        Then:  no exception propagates and the error text is printed to stdout
        """
        # Arrange
        mocker.patch.object(logger, "remove")
        mocker.patch.object(logger, "level")
        mocker.patch.object(logger, "add", side_effect=OSError("disk full"))

        # Act — must not raise
        setup_logging()

        # Assert — error message captured on stdout
        captured = capsys.readouterr()
        assert "disk full" in captured.out or "Error" in captured.out


# ─────────────────────────────────────────────────────────────────────────────
# 2. Exporter audit logs
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestExporterAuditLogs:
    """Exporter functions must log DataFrame preview, output path, and completion."""

    @pytest.fixture(autouse=True)
    def _change_to_tmp(self, tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch) -> None:
        """Redirect file-system writes to a temporary directory for each test."""
        monkeypatch.chdir(tmp_path)

    @pytest.fixture
    def minimal_export_df(self) -> pd.DataFrame:
        """Minimal DataFrame suitable for all export functions."""
        return pd.DataFrame({
            "month": [1],
            "year": [2023],
            "price": ["100.0"],
            "category": ["MISC"],
            "data": ["test transaction"],
        })

    def test_dataframe_preview_is_logged_by_export_for_google_sheets(
        self, loguru_sink: list[str], minimal_export_df: pd.DataFrame
    ) -> None:
        """export_for_google_sheets() must log the DataFrame contents.

        Given: a minimal processed DataFrame and a loguru sink
        When:  export_for_google_sheets() is called
        Then:  at least one log record contains 'Final DataFrame'
        """
        # Act
        export_for_google_sheets(minimal_export_df)

        # Assert
        assert any("Final DataFrame" in msg for msg in loguru_sink)

    def test_output_path_appears_in_export_log(self, loguru_sink: list[str], minimal_export_df: pd.DataFrame) -> None:
        """export_for_google_sheets() must log the output file path.

        Given: a minimal processed DataFrame and a loguru sink
        When:  export_for_google_sheets() is called
        Then:  at least one log record mentions 'for_google_spreadsheet.csv'
        """
        # Act
        export_for_google_sheets(minimal_export_df)

        # Assert
        assert any("for_google_spreadsheet.csv" in msg for msg in loguru_sink)

    def test_misc_completion_is_logged_by_export_misc_transactions(
        self, loguru_sink: list[str], minimal_export_df: pd.DataFrame
    ) -> None:
        """export_misc_transactions() must emit an [EXPORT] completion message.

        Given: a DataFrame containing MISC-category rows and a loguru sink
        When:  export_misc_transactions() is called
        Then:  at least one log record contains 'MISC'
        """
        # Act
        export_misc_transactions(minimal_export_df)

        # Assert
        assert any("MISC" in msg for msg in loguru_sink)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Data import audit logs
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestDataImportsAuditLogs:
    """read_transaction_csv() must log success, errors, and tried encodings."""

    def test_success_message_logged_after_valid_file_load(
        self, loguru_sink: list[str], tmp_path: pytest.TempPathFactory
    ) -> None:
        """[SUCCESS] must appear in the log after a valid CSV is loaded.

        Given: a valid UTF-8 CSV file on disk and a loguru sink
        When:  read_transaction_csv() is called
        Then:  at least one log record contains '[SUCCESS]'
        """
        # Arrange
        csv_file = tmp_path / "transactions.csv"
        csv_file.write_text("data,price,month,year\norlen,-100.0,1,2023\n", encoding="utf-8")

        # Act
        read_transaction_csv(csv_file, "utf-8")

        # Assert
        assert any("[SUCCESS]" in msg for msg in loguru_sink)

    def test_error_logged_and_exception_reraised_for_missing_file(self, loguru_sink: list[str]) -> None:
        """[ERROR] must be logged and FileNotFoundError re-raised for missing files.

        Given: a path that does not exist and a loguru sink
        When:  read_transaction_csv() is called
        Then:  FileNotFoundError is raised AND at least one log record contains '[ERROR]'
        """
        # Act / Assert — exception re-raised
        with pytest.raises(FileNotFoundError):
            read_transaction_csv("nonexistent_file.csv", "utf-8")

        # Assert — error was also logged
        assert any("[ERROR]" in msg for msg in loguru_sink)

    def test_log_dataframe_preview_emits_data_tag(self, loguru_sink: list[str]) -> None:
        """log_dataframe_preview() must emit a '[DATA]' prefixed INFO message.

        Given: a small DataFrame and a loguru sink
        When:  log_dataframe_preview() is called
        Then:  at least one log record contains '[DATA]'
        """
        # Arrange
        df = pd.DataFrame({"month": [1], "price": ["100.0"]})

        # Act
        log_dataframe_preview(df)

        # Assert
        assert any("[DATA]" in msg for msg in loguru_sink)
