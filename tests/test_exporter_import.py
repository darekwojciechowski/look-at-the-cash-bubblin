"""
Tests for data_processing.exporter module import.
Ensures module-level code executes without errors.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestExporterModuleImport:
    """Test suite for exporter module import and module-level code."""

    def test_module_imports_successfully(self):
        """Test that the exporter module can be imported without errors."""
        try:
            import data_processing.exporter
            # If we get here, import was successful
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import exporter module: {e}")

    def test_module_level_variables_exist(self):
        """Test that module-level variables are created correctly."""
        import data_processing.exporter

        # Check that the module has the expected attributes
        assert hasattr(data_processing.exporter, 'CSV_OUT_FILE')
        assert data_processing.exporter.CSV_OUT_FILE == 'data/processed_transactions.csv'

    def test_module_has_expected_functions(self):
        """Test that the module exports expected functions."""
        import data_processing.exporter

        expected_functions = [
            'export_for_google_sheets',
            'export_misc_transactions',
            'export_unassigned_transactions_to_csv',
            'export_final_data',
            'export_final_date_for_google_spreadsheet',
            'get_data'
        ]

        for func_name in expected_functions:
            assert hasattr(data_processing.exporter, func_name)
            assert callable(getattr(data_processing.exporter, func_name))
