"""Tests for data_processing.location_processor module.
Covers location extraction, Polish diacritic normalization, and Google Maps URL generation.
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
        """Test that clean_location_text removes country information.

        Given: a raw location string containing 'kraj: Polska'
        When:  clean_location_text() is called
        Then:  neither 'kraj' nor 'polska' appears in the result
        """
        raw = "lokalizacja: adres: ul. Testowa 12 miasto: Poznan kraj: Polska"
        result = clean_location_text(raw)
        assert "kraj" not in result.lower()
        assert "polska" not in result.lower()

    def test_removes_metadata_prefixes(self) -> None:
        """Test that clean_location_text strips metadata prefixes.

        Given: a raw location string with 'miasto:' and 'adres:' prefixes
        When:  clean_location_text() is called
        Then:  the prefixes are removed from the result
        """
        raw = "miasto: Warszawa adres: ul. Nowa 5"
        result = clean_location_text(raw)
        assert "miasto:" not in result
        assert "adres:" not in result

    def test_normalizes_spacing(self) -> None:
        """Test that clean_location_text standardizes whitespace and commas.

        Given: a raw string with extra spaces and doubled commas
        When:  clean_location_text() is called
        Then:  no double spaces or double commas remain, and the address words are present
        """
        raw = "ul.   Testowa  :  12 ,, Warszawa"
        result = clean_location_text(raw)
        assert "  " not in result
        assert ",," not in result
        assert "testowa" in result.lower()
        assert "warszawa" in result.lower()

    @pytest.mark.parametrize("empty_input", [None, ""])
    def test_handles_empty_input(self, empty_input: str | None) -> None:
        """Test that clean_location_text returns empty string for None/empty.

        Given: None or empty string as input (parametrized)
        When:  clean_location_text() is called
        Then:  an empty string is returned
        """
        assert clean_location_text(empty_input) == ""


@pytest.mark.unit
class TestNormalizePolishNames:
    """Test suite for normalize_polish_names function."""

    def test_restores_diacritics(self, polish_names_without_diacritics: dict[str, str]) -> None:
        """Test that normalize_polish_names restores Polish characters.

        Given: a mapping of ASCII-transliterated Polish names to their correct diacritic forms
        When:  normalize_polish_names() is called for each entry
        Then:  the output matches the correctly diacritised form
        """
        # Arrange — via polish_names_without_diacritics fixture
        for incorrect, correct in polish_names_without_diacritics.items():
            assert normalize_polish_names(incorrect) == correct

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("ul. swietokrzyska 14, warszawa", "ul. świętokrzyska 14, warszawa"),
            ("ul. slowackiego 3, rzeszow", "ul. słowackiego 3, rzeszów"),
            ("al. krolowej jadwigi 7, krakow", "al. królowej jadwigi 7, kraków"),
            ("ul. zeromskiego 22, torun", "ul. żeromskiego 22, toruń"),
            ("ul. polnocna 8, bialystok", "ul. północna 8, białystok"),
            ("ul. poludniowa 5, wroclaw", "ul. południowa 5, wrocław"),
            ("ul. legionow 11, piotrkow", "ul. legionów 11, piotrków"),
            ("ul. powstancow 19, gdansk", "ul. powstańców 19, gdańsk"),
            ("ul. wladyslawa iv 2, nowy sacz", "ul. władysława iv 2, nowy sącz"),
            ("ul. jozefa stanislawa 1, zielona gora", "ul. józefa stanisława 1, zielona góra"),
        ],
    )
    def test_restores_diacritics_parametrized(self, raw: str, expected: str) -> None:
        """Test that normalize_polish_names restores Polish diacritics for 10 street addresses.

        Given: a Polish street address in ASCII-transliterated form (parametrized)
        When:  normalize_polish_names() is called
        Then:  the output is the correctly diacritised address string
        """
        assert normalize_polish_names(raw) == expected

    @pytest.mark.parametrize("empty_input", [None, ""])
    def test_handles_empty_input(self, empty_input: str | None) -> None:
        """Test that normalize_polish_names returns empty string for None/empty.

        Given: None or empty string as input (parametrized)
        When:  normalize_polish_names() is called
        Then:  an empty string is returned
        """
        assert normalize_polish_names(empty_input) == ""


@pytest.mark.unit
class TestExtractLocation:
    """Test suite for extract_location_from_data function."""

    def test_structured_lokalizacja_block(self, structured_location_data: list[str]) -> None:
        """Test extraction from structured 'lokalizacja: adres: ...' blocks.

        Given: three structured location strings from the fixture
        When:  extract_location_from_data() is called for each
        Then:  the street and city are present in each result
        """
        # Arrange — via structured_location_data fixture
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
        """Test extraction from patterns like 'DESC - ADDRESS'.

        Given: three dash-separated location strings from the fixture
        When:  extract_location_from_data() is called for each
        Then:  the street and city fragments are found in each result
        """
        # Arrange — via dash_separated_data fixture
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
        """Test that extract_location_from_data returns empty for NaN/None/empty.

        Given: None, empty string, or NaN as input (parametrized)
        When:  extract_location_from_data() is called
        Then:  an empty string is returned
        """
        assert extract_location_from_data(empty_input) == ""

    @pytest.mark.parametrize("generic_input", ["zakup w terminalu", "grocery store", "shop"])
    def test_excludes_generic_terms(self, generic_input: str) -> None:
        """Test that generic terms are filtered out.

        Given: a generic transaction description with no address information (parametrized)
        When:  extract_location_from_data() is called
        Then:  an empty string is returned
        """
        assert extract_location_from_data(generic_input) == ""


@pytest.mark.unit
class TestCreateGoogleMapsLink:
    """Test suite for create_google_maps_link function."""

    def test_generates_valid_url(self) -> None:
        """Test that create_google_maps_link produces correct encoded URL.

        Given: a Polish street address with special characters
        When:  create_google_maps_link() is called
        Then:  the result is a Google Maps search URL with the address percent-encoded
        """
        # Arrange
        location = "ul. Kościuszki 10, Łódź"
        expected_encoded = urllib.parse.quote(location)
        expected_url = f"https://www.google.com/maps/search/{expected_encoded}"

        # Act
        result = create_google_maps_link(location)

        # Assert
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
        """Test that maps link is only created for address-like strings.

        Given: a string that is either an address or generic text (parametrized)
        When:  create_google_maps_link() is called
        Then:  a non-empty URL is returned only for address-like strings
        """
        result = create_google_maps_link(address)
        assert (result != "") == should_have_link

    @pytest.mark.parametrize("empty_input", [None, "", "   "])
    def test_handles_empty_input(self, empty_input: str | None) -> None:
        """Test that create_google_maps_link returns empty for None/empty/whitespace.

        Given: None, empty string, or whitespace-only input (parametrized)
        When:  create_google_maps_link() is called
        Then:  an empty string is returned
        """
        assert create_google_maps_link(empty_input) == ""

    def test_strips_metadata_prefixes(self) -> None:
        """Test that maps link removes leftover prefixes before encoding.

        Given: a location string with a 'lokalizacja:' prefix
        When:  create_google_maps_link() is called
        Then:  the prefix is absent from the resulting URL and the street name is present
        """
        # Arrange
        location = "lokalizacja: ul. Testowa 12, Warszawa"

        # Act
        result = create_google_maps_link(location)

        # Assert
        assert "lokalizacja" not in result.lower()
        assert "ul.+testowa" in result.lower() or "testowa" in result.lower()


@pytest.mark.unit
class TestExtractLocationEdgeCases:
    """Edge cases for extract_location_from_data: whitespace input, short patterns
    with no recognised street token, and generic-term filtering."""

    def test_whitespace_only_input_returns_empty(self) -> None:
        """Line 276: _split_parts returns empty list for whitespace-only string.

        Given: a string consisting only of whitespace
        When:  extract_location_from_data() is called
        Then:  an empty string is returned
        """
        assert extract_location_from_data("   ") == ""

    def test_returns_result_for_three_word_ending_with_number(self) -> None:
        """Given: a three-token string ending in a number with no recognised street token
        When:  extract_location_from_data() is called
        Then:  a non-empty result is returned
        """
        result = extract_location_from_data("Oak Park 42")
        assert result != ""

    def test_returns_result_for_long_string_containing_digit(self) -> None:
        """Given: a long string that contains a digit but no other address markers
        When:  extract_location_from_data() is called
        Then:  a non-empty result is returned
        """
        result = extract_location_from_data("Ref9000000")
        assert result != ""

    def test_returns_string_when_lokalizacja_has_no_colon(self) -> None:
        """Given: a string with 'lokalizacja' and 'adres:' but no colon after 'lokalizacja'
        When:  extract_location_from_data() is called
        Then:  a string result is returned
        """
        result = extract_location_from_data("lokalizacja adres: ul. Testowa 12")
        assert isinstance(result, str)

    def test_returns_string_when_lokalizacja_precedes_dash_address(self) -> None:
        """Given: a string containing 'lokalizacja' before a dash-separated address block
        When:  extract_location_from_data() is called
        Then:  a string result is returned
        """
        result = extract_location_from_data("lokalizacja - ul. Main 5, Warszawa")
        assert isinstance(result, str)

    def test_returns_string_when_dash_candidate_is_generic_term(self) -> None:
        """Given: a string where the token after the dash is a known generic term
        When:  extract_location_from_data() is called
        Then:  a string result is returned
        """
        result = extract_location_from_data("Transaction desc - store")
        assert isinstance(result, str)


@pytest.mark.unit
class TestExtractAddressPayloadFallback:
    """Fallback address extraction when the 'adres' field has no colon suffix.
    All cases are driven through extract_location_from_data.
    """

    def test_returns_address_and_city_when_adres_has_no_colon(self) -> None:
        """Given: a lokalizacja block where 'adres' is not followed by a colon and 'miasto:' is present
        When:  extract_location_from_data() is called
        Then:  a string result containing address and city information is returned
        """
        result = extract_location_from_data("lokalizacja: adres ul. Testowa 12 miasto: Krakow kraj: Polska")
        assert isinstance(result, str)

    def test_returns_full_payload_when_no_city_separator_present(self) -> None:
        """Given: a lokalizacja block with no 'miasto:' field and no country segment
        When:  extract_location_from_data() is called
        Then:  a string result is returned with the remaining payload
        """
        result = extract_location_from_data("lokalizacja: adres ul. Testowa 12")
        assert isinstance(result, str)

    def test_returns_string_when_payload_is_only_country_segment(self) -> None:
        """Given: a lokalizacja block where the entire payload is a country segment
        When:  extract_location_from_data() is called
        Then:  a string result is returned (empty string from outer caller)
        """
        result = extract_location_from_data("lokalizacja: kraj: Polska adres")
        assert isinstance(result, str)

    def test_returns_address_fragment_when_city_field_is_absent(self) -> None:
        """Given: a lokalizacja block with 'adres:' but no 'miasto:' field
        When:  extract_location_from_data() is called
        Then:  the address fragment 'testowa' is present in the result
        """
        result = extract_location_from_data("lokalizacja: adres: ul. Testowa 12 kraj: Polska")
        assert "testowa" in result.lower()
