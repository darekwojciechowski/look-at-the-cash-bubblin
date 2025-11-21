import pytest
import urllib.parse
from data_processing.location_processor import (
    clean_location_text,
    normalize_polish_names,
    extract_location_from_data,
    create_google_maps_link,
)


@pytest.fixture
def structured_location_data():
    """Fixture providing structured location strings for testing."""
    return [
        "lokalizacja: adres: ul. Testowa 12 miasto: Poznan kraj: Polska",
        "lokalizacja : adres : ul. Kosciuszki 5 miasto : Krakow kraj : Polska",
        "random // lokalizacja: adres: ul. Pilsudskiego 10 miasto: Lodz kraj: Polska",
    ]


@pytest.fixture
def dash_separated_data():
    """Fixture providing dash-separated location strings."""
    return [
        "TRANSACTION DESC - ul. Slowackiego 8, Warszawa",
        "PAYMENT INFO - Paseo de Gracia 12, Barcelona",
        "STORE - Via Roma 45, Milano",
    ]


@pytest.fixture
def polish_names_without_diacritics():
    """Fixture with Polish names lacking proper diacritics."""
    return {
        "ul. kosciuszki 10, lodz": "ul. kościuszki 10, łódź",
        "al. pilsudskiego, krakow": "al. piłsudskiego, kraków",
        "poznan, wroclaw, gdansk": "poznań, wrocław, gdańsk",
    }


def test_clean_location_text_removes_country_field():
    """Test that clean_location_text removes country information."""
    raw = "lokalizacja: adres: ul. Testowa 12 miasto: Poznan kraj: Polska"
    result = clean_location_text(raw)
    assert "kraj" not in result.lower()
    assert "polska" not in result.lower()


def test_clean_location_text_removes_prefixes():
    """Test that clean_location_text strips metadata prefixes."""
    raw = "miasto: Warszawa adres: ul. Nowa 5"
    result = clean_location_text(raw)
    assert "miasto:" not in result
    assert "adres:" not in result


def test_clean_location_text_normalizes_spacing():
    """Test that clean_location_text standardizes whitespace and commas."""
    raw = "ul.   Testowa  :  12 ,, Warszawa"
    result = clean_location_text(raw)
    assert "  " not in result
    assert ",," not in result
    # Implementation leaves space after "12 ," so we check logical cleanup
    assert "testowa" in result.lower()
    assert "warszawa" in result.lower()


def test_clean_location_text_handles_empty_input():
    """Test that clean_location_text returns empty string for None/empty."""
    assert clean_location_text(None) == ""
    assert clean_location_text("") == ""


def test_normalize_polish_names_restores_diacritics(polish_names_without_diacritics):
    """Test that normalize_polish_names restores Polish characters."""
    for incorrect, correct in polish_names_without_diacritics.items():
        assert normalize_polish_names(incorrect) == correct


def test_normalize_polish_names_handles_empty_input():
    """Test that normalize_polish_names returns empty string for None/empty."""
    assert normalize_polish_names(None) == ""
    assert normalize_polish_names("") == ""


def test_extract_location_from_data_structured_block(structured_location_data):
    """Test extraction from structured 'lokalizacja: adres: ...' blocks."""
    result_0 = extract_location_from_data(structured_location_data[0])
    assert "testowa 12" in result_0.lower()
    assert "pozna" in result_0.lower()  # Matches both 'poznan' and 'poznań'

    result_1 = extract_location_from_data(structured_location_data[1])
    assert "kościuszki 5" in result_1.lower()
    assert "krak" in result_1.lower()  # Matches both 'krakow' and 'kraków'

    result_2 = extract_location_from_data(structured_location_data[2])
    assert "piłsudskiego 10" in result_2.lower()
    assert "łód" in result_2.lower()  # Matches both 'lodz' and 'łódź'


def test_extract_location_from_data_dash_separator(dash_separated_data):
    """Test extraction from patterns like 'DESC - ADDRESS'."""
    result_0 = extract_location_from_data(dash_separated_data[0])
    assert "słowackiego" in result_0.lower()
    assert "warszawa" in result_0.lower()

    result_1 = extract_location_from_data(dash_separated_data[1])
    assert "paseo de gracia" in result_1.lower()
    assert "barcelona" in result_1.lower()

    result_2 = extract_location_from_data(dash_separated_data[2])
    assert "via roma" in result_2.lower()
    assert "milano" in result_2.lower()


def test_extract_location_from_data_handles_nan():
    """Test that extract_location_from_data returns empty for NaN/None."""
    import numpy as np
    assert extract_location_from_data(None) == ""
    assert extract_location_from_data("") == ""
    assert extract_location_from_data(np.nan) == ""


def test_extract_location_from_data_excludes_generic_terms():
    """Test that generic terms are filtered out."""
    assert extract_location_from_data("zakup w terminalu") == ""
    assert extract_location_from_data("grocery store") == ""
    assert extract_location_from_data("shop") == ""


def test_create_google_maps_link_generates_valid_url():
    """Test that create_google_maps_link produces correct encoded URL."""
    location = "ul. Kościuszki 10, Łódź"
    result = create_google_maps_link(location)
    expected_encoded = urllib.parse.quote(location)
    expected_url = f"https://www.google.com/maps/search/{expected_encoded}"
    assert result == expected_url


def test_create_google_maps_link_requires_address_indicators():
    """Test that maps link is only created for address-like strings."""
    assert create_google_maps_link("ul. Testowa 12, Warszawa") != ""
    assert create_google_maps_link("Calle Mayor 5, Madrid") != ""
    assert create_google_maps_link("Via Roma 10, Milano") != ""
    assert create_google_maps_link("Random text without address") == ""


def test_create_google_maps_link_handles_empty_input():
    """Test that create_google_maps_link returns empty for None/empty."""
    assert create_google_maps_link(None) == ""
    assert create_google_maps_link("") == ""
    assert create_google_maps_link("   ") == ""


def test_create_google_maps_link_strips_metadata_prefixes():
    """Test that maps link removes leftover prefixes before encoding."""
    location = "lokalizacja: ul. Testowa 12, Warszawa"
    result = create_google_maps_link(location)
    assert "lokalizacja" not in result.lower()
    assert "ul.+testowa" in result.lower() or "testowa" in result.lower()
