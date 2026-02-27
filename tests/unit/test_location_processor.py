"""Tests for data_processing.location_processor module.
Comprehensive testing of location extraction and Google Maps URL generation.
"""

import urllib.parse

import numpy as np
import pytest

from data_processing.location_processor import (
    clean_location_text,
    create_google_maps_link,
    extract_location_from_data,
    normalize_polish_names,
)


@pytest.mark.unit
class TestCleanLocationText:
    """Test suite for clean_location_text function."""

    def test_removes_country_field(self) -> None:
        """Test that clean_location_text removes country information."""
        raw = "lokalizacja: adres: ul. Testowa 12 miasto: Poznan kraj: Polska"
        result = clean_location_text(raw)
        assert "kraj" not in result.lower()
        assert "polska" not in result.lower()

    def test_removes_metadata_prefixes(self) -> None:
        """Test that clean_location_text strips metadata prefixes."""
        raw = "miasto: Warszawa adres: ul. Nowa 5"
        result = clean_location_text(raw)
        assert "miasto:" not in result
        assert "adres:" not in result

    def test_normalizes_spacing(self) -> None:
        """Test that clean_location_text standardizes whitespace and commas."""
        raw = "ul.   Testowa  :  12 ,, Warszawa"
        result = clean_location_text(raw)
        assert "  " not in result
        assert ",," not in result
        assert "testowa" in result.lower()
        assert "warszawa" in result.lower()

    @pytest.mark.parametrize("empty_input", [None, ""])
    def test_handles_empty_input(self, empty_input: str | None) -> None:
        """Test that clean_location_text returns empty string for None/empty."""
        assert clean_location_text(empty_input) == ""


@pytest.mark.unit
class TestNormalizePolishNames:
    """Test suite for normalize_polish_names function."""

    def test_restores_diacritics(self, polish_names_without_diacritics: dict[str, str]) -> None:
        """Test that normalize_polish_names restores Polish characters."""
        for incorrect, correct in polish_names_without_diacritics.items():
            assert normalize_polish_names(incorrect) == correct

    @pytest.mark.parametrize("empty_input", [None, ""])
    def test_handles_empty_input(self, empty_input: str | None) -> None:
        """Test that normalize_polish_names returns empty string for None/empty."""
        assert normalize_polish_names(empty_input) == ""


@pytest.mark.unit
class TestExtractLocation:
    """Test suite for extract_location_from_data function."""

    def test_structured_lokalizacja_block(self, structured_location_data: list[str]) -> None:
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

    def test_dash_separator_pattern(self, dash_separated_data: list[str]) -> None:
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

    @pytest.mark.parametrize("empty_input", [None, "", np.nan])
    def test_handles_nan_and_empty(self, empty_input: object) -> None:
        """Test that extract_location_from_data returns empty for NaN/None/empty."""
        assert extract_location_from_data(empty_input) == ""

    @pytest.mark.parametrize("generic_input", ["zakup w terminalu", "grocery store", "shop"])
    def test_excludes_generic_terms(self, generic_input: str) -> None:
        """Test that generic terms are filtered out."""
        assert extract_location_from_data(generic_input) == ""


@pytest.mark.unit
class TestCreateGoogleMapsLink:
    """Test suite for create_google_maps_link function."""

    def test_generates_valid_url(self) -> None:
        """Test that create_google_maps_link produces correct encoded URL."""
        location = "ul. Kościuszki 10, Łódź"
        result = create_google_maps_link(location)
        expected_encoded = urllib.parse.quote(location)
        expected_url = f"https://www.google.com/maps/search/{expected_encoded}"
        assert result == expected_url

    @pytest.mark.parametrize(
        "address,should_have_link",
        [
            ("ul. Testowa 12, Warszawa", True),
            ("Calle Mayor 5, Madrid", True),
            ("Via Roma 10, Milano", True),
            ("Random text without address", False),
        ],
    )
    def test_requires_address_indicators(self, address: str, should_have_link: bool) -> None:
        """Test that maps link is only created for address-like strings."""
        result = create_google_maps_link(address)
        assert (result != "") == should_have_link

    @pytest.mark.parametrize("empty_input", [None, "", "   "])
    def test_handles_empty_input(self, empty_input: str | None) -> None:
        """Test that create_google_maps_link returns empty for None/empty/whitespace."""
        assert create_google_maps_link(empty_input) == ""

    def test_strips_metadata_prefixes(self) -> None:
        """Test that maps link removes leftover prefixes before encoding."""
        location = "lokalizacja: ul. Testowa 12, Warszawa"
        result = create_google_maps_link(location)
        assert "lokalizacja" not in result.lower()
        assert "ul.+testowa" in result.lower() or "testowa" in result.lower()
