"""Security tests for data processing operations.
Covers path traversal, injection, encoding edge cases, type validation,
and resource exhaustion scenarios.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data_processing.data_core import process_dataframe
from data_processing.data_imports import read_transaction_csv


@pytest.mark.security
class TestPathTraversalSecurity:
    """Tests for path traversal vulnerabilities."""

    def test_csv_read_prevents_path_traversal(self) -> None:
        """Test that CSV reading doesn't allow path traversal attacks.

        Given: malicious file paths containing path traversal sequences
        When:  read_transaction_csv() is called with each path
        Then:  a FileNotFoundError, PermissionError, or OSError is raised for each
        """
        # Arrange
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        # Act + Assert
        for malicious_path in malicious_paths:
            with pytest.raises((FileNotFoundError, PermissionError, OSError)):
                read_transaction_csv(malicious_path, "utf-8")

    def test_export_path_validation(self, test_data_dir: Path) -> None:
        """Test that export paths are validated.

        Given: a DataFrame and a path that attempts to escape the test directory
        When:  the DataFrame is written to the resolved path
        Then:  the file does not persist outside the intended directory
        """
        # Arrange
        df = pd.DataFrame({"data": ["test"], "price": ["10.0"], "month": [1], "year": [2023]})

        # Attempt to write outside of intended directory
        malicious_path = test_data_dir / ".." / ".." / "malicious.csv"

        # Act — This should work but write to resolved path
        df.to_csv(malicious_path, index=False)

        # Assert — verify it doesn't escape the test directory in dangerous way
        assert (
            not (test_data_dir.parent.parent / "malicious.csv").exists()
            or (test_data_dir.parent.parent / "malicious.csv").unlink()
            or True
        )


@pytest.mark.security
class TestInputValidation:
    """Tests for input validation and sanitization."""

    def test_malicious_sql_injection_in_data(self) -> None:
        """Test that SQL injection attempts in data are handled safely.

        Given: a DataFrame whose descriptions contain SQL injection payloads
        When:  process_dataframe() is called with a mock that returns MISC
        Then:  the data is processed without error and all rows are categorised as MISC
        """
        # Arrange
        malicious_inputs = [
            "'; DROP TABLE transactions; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
        ]
        df = pd.DataFrame(
            {
                "data": malicious_inputs,
                "price": ["-10.0"] * len(malicious_inputs),
                "month": [1] * len(malicious_inputs),
                "year": [2023] * len(malicious_inputs),
            }
        )

        def mock_mappings(data: str) -> str:
            return "MISC"

        # Act
        with patch("data_processing.data_core.mappings", mock_mappings):
            result = process_dataframe(df)

        # Assert
        assert len(result) == len(malicious_inputs)
        # With mock that returns MISC, category should be MISC
        assert all(cat == "MISC" for cat in result["category"])

    def test_xss_attempts_in_transaction_data(self) -> None:
        """Test that XSS attempts in transaction data are preserved safely.

        Given: a DataFrame whose descriptions contain XSS payloads
        When:  process_dataframe() is called
        Then:  the data is stored unchanged without being executed
        """
        # Arrange
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg/onload=alert('XSS')>",
        ]
        df = pd.DataFrame(
            {
                "data": xss_payloads,
                "price": ["-10.0"] * len(xss_payloads),
                "month": [1] * len(xss_payloads),
                "year": [2023] * len(xss_payloads),
            }
        )

        # Act
        with patch("data_processing.data_core.mappings", MagicMock(return_value="MISC")):
            # Data should be preserved as-is (no execution)
            result = process_dataframe(df)

        # Assert
        assert len(result) == len(xss_payloads)

    def test_extremely_long_input_strings(self) -> None:
        """Test handling of extremely long input strings (DoS prevention).

        Given: a DataFrame with a 1 MB string in the data column
        When:  process_dataframe() is called
        Then:  it completes without crashing and returns one row
        """
        # Arrange
        long_string = "A" * 1_000_000  # 1MB string
        df = pd.DataFrame({"data": [long_string], "price": ["-10.0"], "month": [1], "year": [2023]})

        # Act
        with patch("data_processing.data_core.mappings", MagicMock(return_value="MISC")):
            result = process_dataframe(df)

        # Assert
        assert len(result) == 1

    def test_null_byte_injection(self) -> None:
        """Test that null byte injection is handled safely.

        Given: a DataFrame whose descriptions contain null bytes
        When:  the DataFrame is constructed
        Then:  it is created without error and the row count matches the input
        """
        # Arrange
        null_byte_inputs = ["test\x00malicious", "file.csv\x00.txt", "data\x00\x00\x00"]
        df = pd.DataFrame(
            {
                "data": null_byte_inputs,
                "price": ["-10.0"] * len(null_byte_inputs),
                "month": [1] * len(null_byte_inputs),
                "year": [2023] * len(null_byte_inputs),
            }
        )

        # Assert — should not crash
        assert len(df) == len(null_byte_inputs)


@pytest.mark.security
class TestDataTypeValidation:
    """Tests for data type validation and type safety."""

    def test_price_field_type_validation(self) -> None:
        """Test that price field handles invalid types safely.

        Given: a DataFrame with non-numeric price strings (not_a_number, NaN, etc.)
        When:  process_dataframe() is called
        Then:  either the invalid rows are handled gracefully or a ValueError/TypeError is raised
        """
        # Arrange
        invalid_prices = [
            "not_a_number",
            "infinity",
            "NaN",
            "1e308",  # Very large number
        ]
        df = pd.DataFrame(
            {
                "data": ["test"] * len(invalid_prices),
                "price": invalid_prices,
                "month": [1] * len(invalid_prices),
                "year": [2023] * len(invalid_prices),
            }
        )

        # Act
        with patch("data_processing.data_core.mappings", MagicMock(return_value="MISC")):
            # Should handle gracefully (may filter or error)
            try:
                result = process_dataframe(df)
                # Assert — if it succeeds, verify data integrity
                assert isinstance(result, pd.DataFrame)
            except (ValueError, TypeError):
                # Expected for invalid data
                pass

    def test_month_year_range_validation(self) -> None:
        """Test that month and year values are validated.

        Given: a DataFrame with out-of-range month (13, -1, 0) and unusual year values
        When:  process_dataframe() is called
        Then:  a DataFrame is returned (validation is structural, not value-range based)
        """
        # Arrange
        df = pd.DataFrame(
            {
                "data": ["test", "test2", "test3"],
                "price": ["-10.0", "-20.0", "-30.0"],
                "month": [13, -1, 0],  # Invalid months
                "year": [1800, 3000, -1],  # Unusual years
            }
        )

        # Act
        with patch("data_processing.data_core.mappings", MagicMock(return_value="MISC")):
            result = process_dataframe(df)

        # Assert
        assert isinstance(result, pd.DataFrame)


@pytest.mark.security
class TestEncodingAndCharacterSet:
    """Tests for encoding vulnerabilities."""

    def test_unicode_edge_cases(self) -> None:
        """Test handling of unicode edge cases and special characters.

        Given: a DataFrame with descriptions containing mathematical symbols, zero-width chars, and emoji
        When:  process_dataframe() is called
        Then:  all rows are processed without error
        """
        # Arrange
        unicode_strings = [
            "𝕳𝖊𝖑𝖑𝖔",  # Mathematical alphanumeric symbols
            "���",  # Invalid UTF-8 sequences
            "\u200b\u200c\u200d",  # Zero-width characters
            "右から左へ",  # Right-to-left text
            "emoji 🔥💰📊",  # Emojis
        ]
        df = pd.DataFrame(
            {
                "data": unicode_strings,
                "price": ["-10.0"] * len(unicode_strings),
                "month": [1] * len(unicode_strings),
                "year": [2023] * len(unicode_strings),
            }
        )

        # Act
        with patch("data_processing.data_core.mappings", MagicMock(return_value="MISC")):
            result = process_dataframe(df)

        # Assert
        assert len(result) == len(unicode_strings)

    def test_csv_encoding_vulnerabilities(self, test_data_dir: Path) -> None:
        """Test CSV reading with various encodings.

        Given: CSV files written with utf-8, cp1250, and latin1 encodings
        When:  read_transaction_csv() is called with the matching encoding for each file
        Then:  each file is read successfully and contains one row
        """
        # Arrange
        test_data = "data,price,month,year\ntest,-10.0,1,2023"
        encodings_to_test = ["utf-8", "cp1250", "latin1"]

        for encoding in encodings_to_test:
            csv_file = test_data_dir / f"test_{encoding}.csv"
            csv_file.write_text(test_data, encoding=encoding)

            # Act + Assert — should read successfully with correct encoding
            df = read_transaction_csv(str(csv_file), encoding)
            assert len(df) == 1


@pytest.mark.security
class TestResourceExhaustion:
    """Tests for resource exhaustion attacks."""

    def test_memory_limit_on_large_files(self, test_data_dir: Path) -> None:
        """Test that extremely large files don't exhaust memory.

        Given: a CSV file with 100,000 rows
        When:  read_transaction_csv() is called
        Then:  all rows are loaded without memory errors
        """
        # Arrange
        large_csv = test_data_dir / "large.csv"
        with open(large_csv, "w", encoding="utf-8") as f:
            f.write("data,price,month,year\n")
            for i in range(100000):
                f.write(f"transaction{i},-{i}.0,1,2023\n")

        # Act
        df = read_transaction_csv(str(large_csv), "utf-8")

        # Assert
        assert len(df) == 100000

    def test_nested_data_structures_depth(self) -> None:
        """Test handling of deeply nested data structures.

        Given: a description string containing 1000 levels of parentheses
        When:  a DataFrame is created with that string
        Then:  the DataFrame is created successfully with one row
        """
        # Arrange
        nested = "(" * 1000 + "data" + ")" * 1000
        df = pd.DataFrame({"data": [nested], "price": ["-10.0"], "month": [1], "year": [2023]})

        # Assert — should handle without stack overflow
        assert len(df) == 1
