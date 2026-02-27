"""
Shared pytest fixtures and configuration for all tests.
Standardizes test data and reduces duplication across test modules.
"""

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from data_processing.data_loader import Expense

# ============================================================================
# DataFrame Fixtures - Common test data
# ============================================================================


@pytest.fixture
def sample_raw_dataframe() -> pd.DataFrame:
    """Fixture providing realistic raw transaction data."""
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
    """Expected output after cleaning transaction descriptions."""
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


@pytest.fixture
def structured_location_data() -> list[str]:
    """Fixture providing structured location strings for testing."""
    return [
        "lokalizacja: adres: ul. Testowa 12 miasto: Poznan kraj: Polska",
        "lokalizacja : adres : ul. Kosciuszki 5 miasto : Krakow kraj : Polska",
        "random // lokalizacja: adres: ul. Pilsudskiego 10 miasto: Lodz kraj: Polska",
    ]


@pytest.fixture
def dash_separated_data() -> list[str]:
    """Fixture providing dash-separated location strings."""
    return [
        "TRANSACTION DESC - ul. Slowackiego 8, Warszawa",
        "PAYMENT INFO - Paseo de Gracia 12, Barcelona",
        "STORE - Via Roma 45, Milano",
    ]


@pytest.fixture
def polish_names_without_diacritics() -> dict[str, str]:
    """Fixture with Polish names lacking proper diacritics."""
    return {
        "ul. kosciuszki 10, lodz": "ul. kościuszki 10, łódź",
        "al. pilsudskiego, krakow": "al. piłsudskiego, kraków",
        "poznan, wroclaw, gdansk": "poznań, wrocław, gdańsk",
    }


# ============================================================================
# Mapping Fixtures
# ============================================================================


@pytest.fixture
def mappings_mock() -> Callable[[str], str]:
    """Fixture providing a callable mock for the mappings() function.

    Returns a callable (not a plain dict) so that:
    - Known test-data strings map to explicit categories.
    - Any unknown string falls back to "MISC", matching the real mappings() contract.

    Using a callable via mocker.patch() ensures df["data"].map(mock) behaves
    identically to the production code path.
    """
    _mapping: dict[str, str] = {
        "terminal purchase": "SHOPPING",
        "web payment": "ONLINE_PAYMENT",
        "Orlen gas station": "FUEL",
        "Starbucks coffee shop": "COFFEE",
        "Biedronka - Piotrkowska 157a": "GROCERIES",
    }
    return lambda data: _mapping.get(str(data), "MISC")


# ============================================================================
# CSV Mock Data
# ============================================================================


@pytest.fixture
def csv_data_mock() -> str:
    """Mock CSV data for testing file reading operations."""
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


# ============================================================================
# Pytest Configuration
# ============================================================================
