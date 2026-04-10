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
        """Test that the exporter module can be imported without errors."""
        try:
            import data_processing.exporter  # noqa: F401

            # If we get here, import was successful
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import exporter module: {e}")

    def test_get_data_accepts_path_parameter(self):
        """Test that get_data accepts an optional path parameter."""
        import inspect

        import data_processing.exporter

        sig = inspect.signature(data_processing.exporter.get_data)
        assert "path" in sig.parameters
        assert sig.parameters["path"].default == Path("data/processed_transactions.csv")

    def test_module_has_expected_functions(self):
        """Test that the module exports expected functions."""
        import data_processing.exporter

        expected_functions = [
            "export_for_google_sheets",
            "export_misc_transactions",
            "export_unassigned_transactions_to_csv",
            "get_data",
        ]

        for func_name in expected_functions:
            assert hasattr(data_processing.exporter, func_name)
            assert callable(getattr(data_processing.exporter, func_name))
