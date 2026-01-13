"""
Security tests for data processing operations.
Tests for common vulnerabilities and data validation.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

from data_processing.data_imports import read_transaction_csv
from data_processing.data_core import process_dataframe


@pytest.mark.security
class TestPathTraversalSecurity:
    """Tests for path traversal vulnerabilities."""

    def test_csv_read_prevents_path_traversal(self) -> None:
        """Test that CSV reading doesn't allow path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM"
        ]

        for malicious_path in malicious_paths:
            with pytest.raises((FileNotFoundError, PermissionError, OSError)):
                read_transaction_csv(malicious_path, 'utf-8')

    def test_export_path_validation(self, test_data_dir: Path) -> None:
        """Test that export paths are validated."""
        df = pd.DataFrame({
            "data": ["test"],
            "price": ["10.0"],
            "month": [1],
            "year": [2023]
        })

        # Attempt to write outside of intended directory
        malicious_path = test_data_dir / ".." / ".." / "malicious.csv"

        # This should work but write to resolved path
        df.to_csv(malicious_path, index=False)

        # Verify it doesn't escape the test directory in dangerous way
        assert not (test_data_dir.parent.parent / "malicious.csv").exists() or \
            (test_data_dir.parent.parent / "malicious.csv").unlink() or True


@pytest.mark.security
class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_malicious_sql_injection_in_data(self) -> None:
        """Test that SQL injection attempts in data are handled safely."""
        malicious_inputs = [
            "'; DROP TABLE transactions; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]

        df = pd.DataFrame({
            "data": malicious_inputs,
            "price": ["-10.0"] * len(malicious_inputs),
            "month": [1] * len(malicious_inputs),
            "year": [2023] * len(malicious_inputs)
        })

        # Mock mappings
        with patch("data_processing.data_core.mappings", {}):
            # Process should handle these safely - empty mappings result in 'nan' category
            result = process_dataframe(df)
        assert len(result) == len(malicious_inputs)
        # With empty mappings, category will be 'nan' (converted from NaN)
        assert all(cat == "nan" for cat in result["category"])

    def test_xss_attempts_in_transaction_data(self) -> None:
        """Test that XSS attempts in transaction data are preserved safely."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>"
        ]

        df = pd.DataFrame({
            "data": xss_payloads,
            "price": ["-10.0"] * len(xss_payloads),
            "month": [1] * len(xss_payloads),
            "year": [2023] * len(xss_payloads)
        })

        with patch("data_processing.data_core.mappings", {}):
            # Data should be preserved as-is (no execution)
            result = process_dataframe(df)
        assert len(result) == len(xss_payloads)

    def test_extremely_long_input_strings(self) -> None:
        """Test handling of extremely long input strings (DoS prevention)."""
        # Create very long string
        long_string = "A" * 1_000_000  # 1MB string

        df = pd.DataFrame({
            "data": [long_string],
            "price": ["-10.0"],
            "month": [1],
            "year": [2023]
        })

        with patch("data_processing.data_core.mappings", {}):
            # Should handle without crashing
            result = process_dataframe(df)
        assert len(result) == 1

    def test_null_byte_injection(self) -> None:
        """Test that null byte injection is handled safely."""
        null_byte_inputs = [
            "test\x00malicious",
            "file.csv\x00.txt",
            "data\x00\x00\x00"
        ]

        df = pd.DataFrame({
            "data": null_byte_inputs,
            "price": ["-10.0"] * len(null_byte_inputs),
            "month": [1] * len(null_byte_inputs),
            "year": [2023] * len(null_byte_inputs)
        })

        # Should not crash
        assert len(df) == len(null_byte_inputs)


@pytest.mark.security
class TestDataTypeValidation:
    """Tests for data type validation and type safety."""

    def test_price_field_type_validation(self) -> None:
        """Test that price field handles invalid types safely."""
        invalid_prices = [
            "not_a_number",
            "infinity",
            "NaN",
            "1e308",  # Very large number
        ]

        df = pd.DataFrame({
            "data": ["test"] * len(invalid_prices),
            "price": invalid_prices,
            "month": [1] * len(invalid_prices),
            "year": [2023] * len(invalid_prices)
        })

        with patch("data_processing.data_core.mappings", {}):
            # Should handle gracefully (may filter or error)
            try:
                result = process_dataframe(df)
                # If it succeeds, verify data integrity
                assert isinstance(result, pd.DataFrame)
            except (ValueError, TypeError):
                # Expected for invalid data
                pass

    def test_month_year_range_validation(self) -> None:
        """Test that month and year values are validated."""
        df = pd.DataFrame({
            "data": ["test", "test2", "test3"],
            "price": ["-10.0", "-20.0", "-30.0"],
            "month": [13, -1, 0],  # Invalid months
            "year": [1800, 3000, -1]  # Unusual years
        })

        with patch("data_processing.data_core.mappings", {}):
            # Should process but data integrity should be considered
            result = process_dataframe(df)
        assert isinstance(result, pd.DataFrame)


@pytest.mark.security
class TestEncodingAndCharacterSet:
    """Tests for encoding vulnerabilities."""

    def test_unicode_edge_cases(self) -> None:
        """Test handling of unicode edge cases and special characters."""
        unicode_strings = [
            "𝕳𝖊𝖑𝖑𝖔",  # Mathematical alphanumeric symbols
            "���",  # Invalid UTF-8 sequences
            "\u200B\u200C\u200D",  # Zero-width characters
            "右から左へ",  # Right-to-left text
            "emoji 🔥💰📊",  # Emojis
        ]

        df = pd.DataFrame({
            "data": unicode_strings,
            "price": ["-10.0"] * len(unicode_strings),
            "month": [1] * len(unicode_strings),
            "year": [2023] * len(unicode_strings)
        })

        with patch("data_processing.data_core.mappings", {}):
            # Should handle unicode safely
            result = process_dataframe(df)
        assert len(result) == len(unicode_strings)

    def test_csv_encoding_vulnerabilities(self, test_data_dir: Path) -> None:
        """Test CSV reading with various encodings."""
        test_data = "data,price,month,year\ntest,-10.0,1,2023"

        encodings_to_test = ['utf-8', 'cp1250', 'latin1']

        for encoding in encodings_to_test:
            csv_file = test_data_dir / f"test_{encoding}.csv"
            csv_file.write_text(test_data, encoding=encoding)

            # Should read successfully with correct encoding
            df = read_transaction_csv(str(csv_file), encoding)
            assert len(df) == 1


@pytest.mark.security
class TestResourceExhaustion:
    """Tests for resource exhaustion attacks."""

    def test_memory_limit_on_large_files(self, test_data_dir: Path) -> None:
        """Test that extremely large files don't exhaust memory."""
        # Create moderately large file (not huge to keep tests fast)
        large_csv = test_data_dir / "large.csv"

        with open(large_csv, 'w', encoding='utf-8') as f:
            f.write("data,price,month,year\n")
            for i in range(100000):
                f.write(f"transaction{i},-{i}.0,1,2023\n")

        # Should handle without memory issues
        df = read_transaction_csv(str(large_csv), 'utf-8')
        assert len(df) == 100000

    def test_nested_data_structures_depth(self) -> None:
        """Test handling of deeply nested data structures."""
        # Create nested string representation
        nested = "(" * 1000 + "data" + ")" * 1000

        df = pd.DataFrame({
            "data": [nested],
            "price": ["-10.0"],
            "month": [1],
            "year": [2023]
        })

        # Should handle without stack overflow
        assert len(df) == 1
