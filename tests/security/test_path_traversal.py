"""Path-traversal security tests.

Covers: F01 (CSV read traversal), F02 (export path), M03 (export confinement),
M04 (symlink following on read), M13 (get_data traversal).
"""

from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_imports import read_transaction_csv
from data_processing.exporter import export_cleaned_data, get_data

pytestmark = pytest.mark.security


class TestPathTraversalOnRead:
    """read_transaction_csv must raise for non-existent or traversal paths."""

    @pytest.mark.parametrize(
        "vector",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "%2e%2e/%2e%2e/etc/passwd",
            "\x00etc/passwd",
        ],
        ids=["unix_dotdot", "win_dotdot", "abs_unix", "urlencoded", "null_byte"],
    )
    def test_read_refuses_traversal_paths(self, vector: str) -> None:
        """Given a path-traversal vector, read_transaction_csv must raise an OS or value error.

        When: read_transaction_csv() is called with the vector as the file path
        Then: FileNotFoundError, PermissionError, OSError, or ValueError is raised
              (null bytes cause ValueError: embedded null byte on some platforms)
        """
        # Act + Assert
        with pytest.raises((FileNotFoundError, PermissionError, OSError, ValueError)):
            read_transaction_csv(vector, "utf-8")

    def test_read_rejects_symlink_outside_base(self, tmp_path: Path) -> None:
        """Given a symlink inside tmp_path pointing at /etc/hosts, read must refuse.

        When:  read_transaction_csv() is called with the symlink path
        Then:  an error is raised — the function must not silently follow the link
        """
        symlink = tmp_path / "evil.csv"
        try:
            symlink.symlink_to("/etc/hosts")
        except OSError, NotImplementedError:
            pytest.skip("Cannot create symlink on this platform")

        with pytest.raises((OSError, PermissionError, ValueError)):
            read_transaction_csv(str(symlink), "utf-8")


class TestPathTraversalOnExport:
    """export_cleaned_data must refuse paths that escape the intended output directory."""

    def test_export_refuses_escape_from_base_dir(self, tmp_path: Path) -> None:
        """Given an output path outside the expected data dir, export must raise.

        When:  export_cleaned_data() is called with a path that escapes via '..'
        Then:  ValueError is raised
        """
        df = pd.DataFrame({
            "data": ["test"],
            "amount": ["10.0"],
            "month": [1],
            "year": [2023],
            "category": ["MISC"],
        })
        escape_path = tmp_path.parent / "escaped.csv"

        with pytest.raises(ValueError):
            export_cleaned_data(df, output_file=escape_path)


class TestPathTraversalOnGetData:
    """get_data must raise for non-existent traversal paths."""

    @pytest.mark.parametrize(
        "vector",
        [
            "../../../etc/passwd",
            "/nonexistent/path/transactions.csv",
        ],
        ids=["dotdot", "abs_nonexistent"],
    )
    def test_get_data_refuses_traversal(self, vector: str) -> None:
        """Given a traversal path, get_data must raise FileNotFoundError or OSError.

        When:  get_data() is called with the traversal path
        Then:  FileNotFoundError or OSError is raised
        """
        with pytest.raises((FileNotFoundError, OSError)):
            get_data(Path(vector))
