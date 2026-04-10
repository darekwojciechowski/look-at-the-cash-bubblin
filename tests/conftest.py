"""
Shared pytest fixtures and configuration for all tests.
Standardizes test data and reduces duplication across test modules.

Scope conventions:
  - function (default) : mutable objects (DataFrames, lists, Expense instances)
                         that tests may modify; recreated per test for isolation.
  - module             : purely immutable / read-only data (plain strings, frozen
                         dicts/lists that tests only read); shared across every
                         test in the importing module to cut setup overhead.
  - session            : expensive one-time resources (not needed here yet).
"""

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_loader import Expense

# Canonical schema for transaction DataFrames used throughout the test suite.
_TRANSACTION_COLUMNS: list[str] = ["data", "price", "month", "year"]

# Type alias used by the make_transaction_dataframe factory fixture.
type TransactionRow = dict[str, str | int | float]

# ============================================================================
# DataFrame Fixtures - Common test data
# ============================================================================


@pytest.fixture
def sample_raw_dataframe() -> pd.DataFrame:
    """Raw transaction DataFrame as it arrives from ipko_import().

    Designed to be used together with ``expected_cleaned_data``:
    ``clean_descriptions(sample_raw_dataframe)`` should equal
    ``expected_cleaned_data``.  Recreated per test so mutations are isolated.
    """
    return pd.DataFrame(
        {
            "data": [
                "purchase in terminal - mobile code",
                "web payment - mobile code",
                "orlen",
                "starbucks",
                "piotrkowska 157a",
            ],
            "price": ["-50.0", "-20.0", "-100.0", "-15.0", "200.0"],
            "month": [1, 1, 1, 1, 1],
            "year": [2023, 2023, 2023, 2023, 2023],
        }
    )


@pytest.fixture
def sample_processed_dataframe() -> pd.DataFrame:
    """Fixture providing expected processed transaction data."""
    return pd.DataFrame(
        {
            "month": [1, 1, 2, 2],
            "year": [2023, 2023, 2023, 2023],
            "price": [100.0, 200.0, 300.0, 50.0],
            "category": ["MISC", "FOOD", "MISC", "FUEL"],
            "data": [
                "unknown transaction",
                "biedronka shopping",
                "misc item",
                "orlen fuel",
            ],
        }
    )


@pytest.fixture
def sample_dataframe_with_categories() -> pd.DataFrame:
    """Provides realistic transaction DataFrame with categories."""
    return pd.DataFrame(
        {
            "category": ["MISC", "FOOD", "MISC", "FUEL"],
            "price": [100.0, 200.0, 300.0, 50.0],
            "month": [1, 1, 2, 2],
            "year": [2023, 2023, 2023, 2023],
            "data": [
                "unknown transaction",
                "biedronka shopping",
                "misc item",
                "orlen fuel",
            ],
        }
    )


@pytest.fixture
def sample_ipko_dataframe() -> pd.DataFrame:
    """Provides a sample DataFrame for testing the ipko_import function."""
    return pd.DataFrame(
        {
            0: ["2023-01-01", "2023-01-02"],
            1: ["PLN", "PLN"],
            2: ["transfer", "payment"],
            3: ["-100.0", "-50.0"],
            4: ["PLN", "PLN"],
            5: ["description1", "description2"],
            6: ["extra1", "extra2"],
            7: ["data1", "data2"],
            8: ["extra3", "extra4"],
        }
    )


@pytest.fixture
def expected_cleaned_data() -> pd.DataFrame:
    """Expected output after ``clean_descriptions()`` is applied to ``sample_raw_dataframe``.

    The two fixtures form a matched input/output pair for description-cleaning
    tests.  Recreated per test so mutations are isolated.
    """
    return pd.DataFrame(
        {
            "data": [
                "terminal purchase",
                "web payment",
                "Orlen gas station",
                "Starbucks coffee shop",
                "Biedronka - Piotrkowska 157a",
            ],
            "price": ["-50.0", "-20.0", "-100.0", "-15.0", "200.0"],
            "month": [1, 1, 1, 1, 1],
            "year": [2023, 2023, 2023, 2023, 2023],
        }
    )


@pytest.fixture
def empty_transaction_dataframe() -> pd.DataFrame:
    """Empty DataFrame with the canonical transaction schema.

    Use whenever a test needs to validate behaviour on an empty input without
    constructing the schema inline.  Recreated per test for isolation.
    """
    return pd.DataFrame(columns=_TRANSACTION_COLUMNS)


@pytest.fixture
def make_transaction_dataframe() -> Callable[[list[TransactionRow]], pd.DataFrame]:
    """Factory fixture that builds a typed transaction DataFrame from a list of row dicts.

    Eliminates the repetitive ``pd.DataFrame({...})`` boilerplate in
    parametrized tests that need a single- or multi-row input.  Each call
    returns a new DataFrame, so there is no shared-state risk.

    Example usage inside a test::

        def test_something(make_transaction_dataframe):
            df = make_transaction_dataframe(
                [{"data": "orlen", "price": "-100.0", "month": 1, "year": 2023}]
            )
            result = clean_descriptions(df)
            assert result["data"].iloc[0] == "Orlen gas station"
    """

    def _factory(rows: list[TransactionRow]) -> pd.DataFrame:
        return pd.DataFrame(rows, columns=_TRANSACTION_COLUMNS)

    return _factory


# ============================================================================
# Expense Fixtures
# ============================================================================


@pytest.fixture
def sample_expenses() -> list[Expense]:
    """Provides realistic Expense objects for testing."""
    return [
        Expense(1, 2023, "apartment rent", 1200),
        Expense(1, 2023, "groceries", 200),
        Expense(2, 2023, "fuel", 100),
    ]


# ============================================================================
# Location Processing Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def structured_location_data() -> list[str]:
    """Structured IPKO ``lokalizacja:`` location strings (read-only, module-scoped).

    Tests must not mutate this list.  Use ``scope="module"`` so the list is
    constructed once and shared across every test in the importing module.
    """
    return [
        "lokalizacja: adres: ul. Testowa 12 miasto: Poznan kraj: Polska",
        "lokalizacja : adres : ul. Kosciuszki 5 miasto : Krakow kraj : Polska",
        "random // lokalizacja: adres: ul. Pilsudskiego 10 miasto: Lodz kraj: Polska",
    ]


@pytest.fixture(scope="module")
def dash_separated_data() -> list[str]:
    """Dash-separated ``DESCRIPTION - ADDRESS`` location strings (read-only, module-scoped).

    Tests must not mutate this list.  Use ``scope="module"`` so the list is
    constructed once and shared across every test in the importing module.
    """
    return [
        "TRANSACTION DESC - ul. Slowackiego 8, Warszawa",
        "PAYMENT INFO - Paseo de Gracia 12, Barcelona",
        "STORE - Via Roma 45, Milano",
    ]


@pytest.fixture(scope="module")
def polish_names_without_diacritics() -> dict[str, str]:
    """ASCII → Unicode diacritic mapping for ``normalize_polish_names()`` tests (read-only, module-scoped).

    Keys are ASCII-only inputs; values are the expected normalised outputs.
    Tests must not mutate this dict.  Use ``scope="module"`` so it is
    constructed once and shared across every test in the importing module.
    """
    return {
        "ul. kosciuszki 10, lodz": "ul. kościuszki 10, łódź",
        "al. pilsudskiego, krakow": "al. piłsudskiego, kraków",
        "poznan, wroclaw, gdansk": "poznań, wrocław, gdańsk",
        "ul. swietokrzyska 14, warszawa": "ul. świętokrzyska 14, warszawa",
        "ul. slowackiego 3, rzeszow": "ul. słowackiego 3, rzeszów",
        "al. krolowej jadwigi 7, krakow": "al. królowej jadwigi 7, kraków",
        "ul. zeromskiego 22, torun": "ul. żeromskiego 22, toruń",
        "ul. polnocna 8, bialystok": "ul. północna 8, białystok",
        "ul. poludniowa 5, wroclaw": "ul. południowa 5, wrocław",
        "ul. legionow 11, piotrkow": "ul. legionów 11, piotrków",
        "ul. powstancow 19, gdansk": "ul. powstańców 19, gdańsk",
        "ul. wladyslawa iv 2, nowy sacz": "ul. władysława iv 2, nowy sącz",
        "ul. jozefa stanislawa 1, zielona gora": "ul. józefa stanisława 1, zielona góra",
    }


# ============================================================================
# Mapping Fixtures
# ============================================================================


@pytest.fixture
def mappings_mock() -> Callable[[str], str]:
    """Callable drop-in replacement for the production ``mappings()`` function.

    Returns a named callable (not an anonymous ``lambda``) so that:
    - mypy can fully type-check call sites.
    - Failed assertions show a readable function name in tracebacks.
    - Known test-data strings map to explicit categories that match the
      ``expected_cleaned_data`` / ``sample_raw_dataframe`` pair.
    - Any unknown string falls back to ``"MISC"``, honouring the real
      ``mappings()`` contract.

    Usage with pytest-mock::

        mocker.patch("data_processing.data_core.mappings", side_effect=mappings_mock)
    """
    _mapping: dict[str, str] = {
        "terminal purchase": "SHOPPING",
        "web payment": "ONLINE_PAYMENT",
        "Orlen gas station": "FUEL",
        "Starbucks coffee shop": "COFFEE",
        "Biedronka - Piotrkowska 157a": "GROCERIES",
    }

    def _mock_mappings(data: str) -> str:
        return _mapping.get(str(data), "MISC")

    return _mock_mappings


# ============================================================================
# CSV Mock Data
# ============================================================================


@pytest.fixture(scope="module")
def csv_data_mock() -> str:
    """Minimal CSV string for testing file-reading operations (read-only, module-scoped).

    Plain strings are immutable in Python, so ``scope="module"`` is safe: the
    object cannot be mutated by any test, and sharing it avoids repeated
    allocation for every test function.
    """
    return "month,year,item,price\n1,2023,item1,100\n2,2023,item2,200\n"


# ============================================================================
# Path Fixtures
# ============================================================================


@pytest.fixture
def test_data_dir(tmp_path: Path) -> Path:
    """Provides a temporary directory for test data."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_csv_file(test_data_dir: Path) -> Path:
    """Creates a sample CSV file for testing."""
    csv_path = test_data_dir / "test_transactions.csv"
    csv_content = """data,price,month,year
orlen,-100.0,1,2023
biedronka,-50.0,1,2023
"""
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path
