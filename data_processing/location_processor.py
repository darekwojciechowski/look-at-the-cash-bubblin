from __future__ import annotations

import re
import urllib.parse

import pandas as pd

_PREFIXES_TO_REMOVE: tuple[str, ...] = (
    'miasto :',
    'miasto:',
    'adres :',
    'adres:',
    'lokalizacja :',
    'lokalizacja:',
)

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

_ADDRESS_INDICATORS: tuple[str, ...] = ('ul.', 'al.', 'pl.', 'os.', 'centrum')

_MAPS_STREET_TOKENS: tuple[str, ...] = (
    'ul.', 'al.', 'pl.', 'os.', 'aleja', 'ulica', 'plac', 'osiedle',
    'street', 'st.', 'avenue', 'ave.', 'road', 'rd.', 'boulevard', 'blvd.',
    'lane', 'ln.', 'drive', 'dr.', 'calle', 'avenida', 'avda.', 'paseo', 'plaza',
    'via', 'viale', 'piazza', 'corso', 'strada',
)

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

_COUNTRY_FIELD_RE = re.compile(r'\s*kraj\s*:\s*[^,]*', re.IGNORECASE)
_COLON_SPACING_RE = re.compile(r'\s*:\s*')
_MULTIPLE_SPACE_RE = re.compile(r'\s+')
_DOUBLE_COMMA_RE = re.compile(r',\s*,')
_THREE_TOKEN_NUMBER_RE = re.compile(r'\w+\s+\w+\s+\d+')
_DIGIT_RE = re.compile(r'\d+')
_STRUCTURED_ADDRESS_RE = re.compile(
    r'adres\s*:\s*(?P<address>.*?)\s*(?:miasto\s*:\s*(?P<city>.*?))?(?:kraj\s*:\s*.*)?$',
    re.IGNORECASE,
)
_MAPS_SUFFIX_RE = re.compile(
    r'\s*:\s*([^:]+?)\s+kraj\s*:\s*\w+$', re.IGNORECASE)


def clean_location_text(location: str | None) -> str:
    """Strip boilerplate markers and standardise separators."""
    if not location:
        return ""

    cleaned = _COUNTRY_FIELD_RE.sub('', location)
    for prefix in _PREFIXES_TO_REMOVE:
        cleaned = cleaned.replace(prefix, ' ')

    cleaned = _COLON_SPACING_RE.sub(', ', cleaned)
    cleaned = _MULTIPLE_SPACE_RE.sub(' ', cleaned)
    cleaned = _DOUBLE_COMMA_RE.sub(',', cleaned)
    return cleaned.strip(' ,')


def normalize_polish_names(location: str | None) -> str:
    """Restore missing Polish diacritics for common tokens."""
    if not location:
        return ""

    normalised = location
    for incorrect, correct in _POLISH_REPLACEMENTS.items():
        pattern = r'\b' + re.escape(incorrect) + r'\b'
        normalised = re.sub(pattern, correct, normalised, flags=re.IGNORECASE)
    return normalised


def extract_location_from_data(data_string: str | float | None) -> str:
    """Derive the most reliable location fragment from raw transaction data."""
    if data_string is None or data_string == '' or pd.isna(data_string):
        return ''

    parts = _split_parts(data_string)
    if not parts:
        return ''

    for part in parts:
        structured = _parse_structured_part(part)
        if structured:
            return _finalise_location(structured)

    for part in parts:
        dash_location = _extract_dash_part(part)
        if dash_location:
            return _finalise_location(dash_location)

    for part in parts:
        if _looks_like_address(part):
            return _finalise_location(part)

    for part in parts:
        lowered = part.lower()
        if lowered not in _EXCLUDE_TERMS and len(part) > 3:
            return _finalise_location(part)

    return ''


def create_google_maps_link(location: str | None) -> str:
    """Return a Google Maps search URL when the text resembles an address."""
    if not location:
        return ''

    trimmed = location.strip()
    if not trimmed:
        return ''

    lowered = trimmed.lower()
    has_street_indicator = any(
        token in lowered for token in _MAPS_STREET_TOKENS)
    has_comma = ',' in trimmed
    has_number = bool(_DIGIT_RE.search(trimmed))
    has_city = any(city in lowered for city in _MAPS_CITY_KEYWORDS)

    if not (has_street_indicator or (has_comma and (has_number or has_city))):
        return ''

    for prefix in _PREFIXES_TO_REMOVE:
        if lowered.startswith(prefix):
            trimmed = trimmed[len(prefix):].strip()
            lowered = trimmed.lower()

    trimmed = _MAPS_SUFFIX_RE.sub(r', \1', trimmed)
    trimmed = _COLON_SPACING_RE.sub(', ', trimmed)
    trimmed = _MULTIPLE_SPACE_RE.sub(' ', trimmed)
    trimmed = _DOUBLE_COMMA_RE.sub(',', trimmed)
    trimmed = trimmed.strip(' ,')

    if not trimmed:
        return ''

    encoded = urllib.parse.quote(trimmed)
    return f"https://www.google.com/maps/search/{encoded}"


def _split_parts(data_string: str | float | None) -> list[str]:
    return [
        part.strip()
        for part in str(data_string).split('//')
        if part and part.strip()
    ]


def _parse_structured_part(part: str) -> str | None:
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
    lowered = part.lower()
    if lowered in _EXCLUDE_TERMS:
        return False

    if any(keyword in lowered for keyword in _ADDRESS_INDICATORS):
        return True

    if _THREE_TOKEN_NUMBER_RE.search(part):
        return True

    return bool(_DIGIT_RE.search(part) and len(part) > 8)


def _finalise_location(part: str) -> str:
    cleaned = clean_location_text(part)
    return normalize_polish_names(cleaned)
