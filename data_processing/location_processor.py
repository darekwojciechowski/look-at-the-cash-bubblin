"""Utilities for extracting and normalising location data from raw strings."""

from __future__ import annotations

import re
import urllib.parse

import pandas as pd

# Metadata prefixes commonly found in raw transaction strings that should be removed
# during cleanup to isolate the actual address text.
_PREFIXES_TO_REMOVE: tuple[str, ...] = (
    'miasto :',
    'miasto:',
    'adres :',
    'adres:',
    'lokalizacja :',
    'lokalizacja:',
)

# Mapping of common Polish names without diacritics to their proper Unicode forms.
# Used for normalizing addresses that may have been entered without proper characters.
_POLISH_REPLACEMENTS: dict[str, str] = {
    # Cities
    'lodz': 'łódź',
    'krakow': 'kraków',
    'poznan': 'poznań',
    'wroclaw': 'wrocław',
    'gdansk': 'gdańsk',
    'czestochowa': 'częstochowa',
    'torun': 'toruń',
    'bialystok': 'białystok',
    'rzeszow': 'rzeszów',
    'piotrkow': 'piotrków',
    'walbrzych': 'wałbrzych',
    'wloclawek': 'włocławek',
    'jelenia gora': 'jelenia góra',
    'nowy sacz': 'nowy sącz',
    'zielona gora': 'zielona góra',
    # Street names and common words
    'kosciuszki': 'kościuszki',
    'pilsudskiego': 'piłsudskiego',
    'slowackiego': 'słowackiego',
    'zeromskiego': 'żeromskiego',
    'swietokrzyska': 'świętokrzyska',
    'stanislawa': 'stanisława',
    'wladyslawa': 'władysława',
    'jozefa': 'józefa',
    'legionow': 'legionów',
    'zwyciestwa': 'zwycięstwa',
    'polnocna': 'północna',
    'poludniowa': 'południowa',
    'krolowej': 'królowej',
    'powstancow': 'powstańców',
    # Common prefixes
    'sw.': 'św.',
    'sw ': 'św. ',
}

# Keywords that strongly suggest a text fragment contains an address.
# Includes Polish, Spanish, and Italian street/location markers for international support.
_ADDRESS_INDICATORS: tuple[str, ...] = (
    'ul.',
    'al.',
    'pl.',
    'os.',
    'centrum',
    'calle',
    'avenida',
    'avda.',
    'paseo',
    'plaza',
    'via',
    'viale',
    'piazza',
    'corso',
    'strada',
)

# Extended set of street indicators used specifically for validating Google Maps links.
# More comprehensive than _ADDRESS_INDICATORS to reduce false positives in URL generation.
_MAPS_STREET_TOKENS: tuple[str, ...] = (
    'ul.', 'al.', 'pl.', 'os.', 'aleja', 'ulica', 'plac', 'osiedle',
    'street', 'st.', 'avenue', 'ave.', 'road', 'rd.', 'boulevard', 'blvd.',
    'lane', 'ln.', 'drive', 'dr.', 'calle', 'avenida', 'avda.', 'paseo', 'plaza',
    'via', 'viale', 'piazza', 'corso', 'strada',
)

# Major city names used to validate whether a location string is geocodable.
# Combined with other heuristics to determine if a Google Maps link should be generated.
_MAPS_CITY_KEYWORDS: tuple[str, ...] = (
    # Polish cities
    'warszawa', 'kraków', 'łódź', 'wrocław', 'poznań', 'gdańsk', 'szczecin',
    'bydgoszcz', 'lublin', 'katowice', 'białystok', 'gdynia', 'częstochowa',
    'radom', 'sosnowiec', 'toruń', 'kielce', 'gliwice', 'zabrze', 'bytom',
    'olsztyn', 'bielsko-biała', 'rzeszów',
    # Spanish cities
    'madrid', 'barcelona', 'valencia', 'sevilla', 'zaragoza', 'málaga',
    'murcia', 'palma', 'bilbao', 'alicante', 'córdoba', 'valladolid',
    'granada', 'salamanca', 'toledo',
    # Italian cities
    'roma', 'milano', 'napoli', 'torino', 'palermo', 'genova', 'bologna',
    'firenze', 'bari', 'catania', 'venezia', 'verona', 'messina', 'padova',
    'trieste', 'brescia', 'parma', 'modena',
)

# Generic transaction descriptions that should not be treated as locations.
# These terms are filtered out during extraction to avoid false positives.
_EXCLUDE_TERMS: set[str] = {
    'nan',
    'null',
    'zakup w terminalu',
    'pc game purchase',
    'grocery store',
    'groceries',
    'store',
    'shop',
    'market',
}

# Compiled regex patterns for efficient text processing and address extraction.
# Remove "kraj: ..." segments
_COUNTRY_FIELD_RE = re.compile(r'\s*kraj\s*:\s*[^,]*', re.IGNORECASE)
_COLON_SPACING_RE = re.compile(r'\s*:\s*')  # Normalize spacing around colons
_MULTIPLE_SPACE_RE = re.compile(r'\s+')  # Collapse multiple spaces
_DOUBLE_COMMA_RE = re.compile(r',\s*,')  # Remove duplicate commas
_THREE_TOKEN_NUMBER_RE = re.compile(
    r'\w+\s+\w+\s+\d+')  # Pattern like "street name 123"
_DIGIT_RE = re.compile(r'\d+')  # Any numeric sequence
_STRUCTURED_ADDRESS_RE = re.compile(
    r'adres\s*:\s*(?P<address>.*?)\s*(?:miasto\s*:\s*(?P<city>.*?))?(?:kraj\s*:\s*.*)?$',
    re.IGNORECASE,
)  # Parse "adres: ... miasto: ... kraj: ..." format
_MAPS_SUFFIX_RE = re.compile(
    # Clean trailing country info
    r'\s*:\s*([^:]+?)\s+kraj\s*:\s*\w+$', re.IGNORECASE)


def clean_location_text(location: str | None) -> str:
    """Strip boilerplate markers and standardise separators.

    Args:
        location: Raw location string potentially containing metadata prefixes.

    Returns:
        Cleaned location string with normalized spacing and punctuation.
    """
    if not location:
        return ""

    # Remove country information
    cleaned = _COUNTRY_FIELD_RE.sub('', location)

    # Strip metadata prefixes like "miasto:", "adres:"
    for prefix in _PREFIXES_TO_REMOVE:
        cleaned = cleaned.replace(prefix, ' ')

    # Standardize formatting
    # Colons → commas with spacing
    cleaned = _COLON_SPACING_RE.sub(', ', cleaned)
    cleaned = _MULTIPLE_SPACE_RE.sub(' ', cleaned)  # Collapse whitespace
    cleaned = _DOUBLE_COMMA_RE.sub(',', cleaned)    # Remove duplicate commas
    return cleaned.strip(' ,')


def normalize_polish_names(location: str | None) -> str:
    """Restore missing Polish diacritics for common tokens.

    Args:
        location: Location string potentially containing names without proper diacritics.

    Returns:
        Location string with Polish characters properly restored.
    """
    if not location:
        return ""

    normalised = location
    # Replace each ASCII variant with its proper Unicode form using word boundaries
    for incorrect, correct in _POLISH_REPLACEMENTS.items():
        pattern = r'\b' + re.escape(incorrect) + r'\b'
        normalised = re.sub(pattern, correct, normalised, flags=re.IGNORECASE)
    return normalised


def extract_location_from_data(data_string: str | float | None) -> str:
    """Derive the most reliable location fragment from raw transaction data.

    Uses a priority-based extraction strategy:
    1. Structured metadata blocks (lokalizacja: adres: ... miasto: ...)
    2. Dash-separated patterns (DESC - ADDRESS)
    3. Address-like heuristics (street indicators, numbers)
    4. Any remaining meaningful text

    Args:
        data_string: Raw transaction data potentially containing location info.

    Returns:
        Cleaned and normalized location string, or empty string if none found.
    """
    if data_string is None or data_string == '' or pd.isna(data_string):
        return ''

    parts = _split_parts(data_string)
    if not parts:
        return ''

    # Priority 1: Structured location blocks
    for part in parts:
        structured = _parse_structured_part(part)
        if structured:
            return _finalise_location(structured)

    # Priority 2: Dash-separated fallback
    for part in parts:
        dash_location = _extract_dash_part(part)
        if dash_location:
            return _finalise_location(dash_location)

    # Priority 3: Address-like patterns
    for part in parts:
        if _looks_like_address(part):
            return _finalise_location(part)

    # Priority 4: Any non-generic text
    for part in parts:
        lowered = part.lower()
        if lowered not in _EXCLUDE_TERMS and len(part) > 3:
            return _finalise_location(part)

    return ''


def create_google_maps_link(location: str | None) -> str:
    """Return a Google Maps search URL when the text resembles an address.

    Only generates links for strings that pass validation heuristics to avoid
    creating useless map searches for generic transaction descriptions.

    Args:
        location: Location string to potentially convert to a Maps URL.

    Returns:
        Encoded Google Maps search URL, or empty string if location is invalid.
    """
    if not location:
        return ''

    trimmed = location.strip()
    if not trimmed:
        return ''

    lowered = trimmed.lower()
    # Validate the location contains address-like features
    has_street_indicator = any(
        token in lowered for token in _MAPS_STREET_TOKENS)
    has_comma = ',' in trimmed
    has_number = bool(_DIGIT_RE.search(trimmed))
    has_city = any(city in lowered for city in _MAPS_CITY_KEYWORDS)

    # Require either street indicator OR (comma + number/city)
    if not (has_street_indicator or (has_comma and (has_number or has_city))):
        return ''

    # Remove any leftover metadata prefixes
    for prefix in _PREFIXES_TO_REMOVE:
        if lowered.startswith(prefix):
            trimmed = trimmed[len(prefix):].strip()
            lowered = trimmed.lower()

    # Final cleanup pass
    trimmed = _MAPS_SUFFIX_RE.sub(r', \1', trimmed)  # Clean "kraj:" suffixes
    trimmed = _COLON_SPACING_RE.sub(', ', trimmed)   # Normalize colons
    trimmed = _MULTIPLE_SPACE_RE.sub(' ', trimmed)   # Collapse spaces
    trimmed = _DOUBLE_COMMA_RE.sub(',', trimmed)     # Remove duplicate commas
    trimmed = trimmed.strip(' ,')

    if not trimmed:
        return ''

    # URL-encode and construct Maps search link
    encoded = urllib.parse.quote(trimmed)
    return f"https://www.google.com/maps/search/{encoded}"


def _split_parts(data_string: str | float | None) -> list[str]:
    """Split raw transaction text by '//' and trim whitespace."""
    return [
        part.strip()
        for part in str(data_string).split('//')
        if part and part.strip()
    ]


def _parse_structured_part(part: str) -> str | None:
    """Handle fragments that expose 'lokalizacja' metadata blocks."""
    lowered = part.lower()
    if 'lokalizacja' not in lowered or 'adres' not in lowered:
        return None

    candidate = part.split(' - ')[-1].strip()
    candidate_lower = candidate.lower()
    working = candidate if 'lokalizacja' in candidate_lower else part

    split_payload = re.split(r'(?i)lokalizacja\s*:\s*', working, maxsplit=1)
    if len(split_payload) != 2:
        return None

    return _extract_address_payload(split_payload[1])


def _extract_address_payload(payload: str) -> str | None:
    """Extract "adres", "miasto" chunks from the structured payload."""
    match = _STRUCTURED_ADDRESS_RE.search(payload)
    if match:
        address = (match.group('address') or '').strip(' ,')
        city = (match.group('city') or '').strip(' ,')
        if address and city:
            return f'{address}, {city}'
        return address or city or None

    without_country = re.split(
        r'(?i)kraj\s*:\s*', payload, maxsplit=1)[0].strip(' ,')
    if not without_country:
        return None

    if ':' in without_country:
        address, _, city = without_country.rpartition(':')
        address = address.strip(' ,')
        city = city.strip(' ,')
        if address and city:
            return f'{address}, {city}'

    return without_country


def _extract_dash_part(part: str) -> str | None:
    """Fallback for patterns like 'something - ADDRESS'."""
    if ' - ' not in part:
        return None

    lowered = part.lower()
    if 'lokalizacja' in lowered:
        return None

    candidate = part.split(' - ')[-1].strip()
    if candidate and candidate.lower() not in _EXCLUDE_TERMS:
        return candidate
    return None


def _looks_like_address(part: str) -> bool:
    """Decide whether the text resembles an address using heuristics."""
    lowered = part.lower()
    if lowered in _EXCLUDE_TERMS:
        return False

    if any(keyword in lowered for keyword in _ADDRESS_INDICATORS):
        return True

    if _THREE_TOKEN_NUMBER_RE.search(part):
        return True

    return bool(_DIGIT_RE.search(part) and len(part) > 8)


def _finalise_location(part: str) -> str:
    """Run the standard cleaning pipeline for a raw location candidate."""
    cleaned = clean_location_text(part)
    return normalize_polish_names(cleaned)
