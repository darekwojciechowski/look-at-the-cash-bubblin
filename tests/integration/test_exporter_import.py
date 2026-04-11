"""
Tests for data_processing.exporter module import.
Ensures module-level code executes without errors.
"""

from pathlib import Path

import pytest


@pytest.mark.unit
class TestExporterModuleImport:
    """Test suite for exporter module import and module-level code."""

    def test_module_imports_successfully(self):
        """Verify the exporter module imports without raising an error.

        Given: the data_processing.exporter module on the Python path
        When:  the module is imported
        Then:  no ImportError is raised
        """
        # Arrange — module available on sys.path

        # Act + Assert
        try:
            import data_processing.exporter  # noqa: F401

            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import exporter module: {e}")

    def test_get_data_accepts_path_parameter(self):
        """Verify get_data has a path parameter with the expected default.

        Given: the data_processing.exporter module is imported
        When:  the signature of get_data is inspected
        Then:  a 'path' parameter exists with default Path('data/processed_transactions.csv')
        """
        # Arrange
        import inspect

        import data_processing.exporter

        # Act
        sig = inspect.signature(data_processing.exporter.get_data)

        # Assert
        assert "path" in sig.parameters
        assert sig.parameters["path"].default == Path("data/processed_transactions.csv")

    def test_module_has_expected_functions(self):
        """Verify the exporter module exposes the four expected public functions.

        Given: the data_processing.exporter module is imported
        When:  each expected function name is checked with hasattr and callable
        Then:  all four functions exist and are callable
        """
        # Arrange
        import data_processing.exporter

        expected_functions = [
            "export_for_google_sheets",
            "export_misc_transactions",
            "export_unassigned_transactions_to_csv",
            "get_data",
        ]

        # Act + Assert
        for func_name in expected_functions:
            assert hasattr(data_processing.exporter, func_name)
            assert callable(getattr(data_processing.exporter, func_name))
