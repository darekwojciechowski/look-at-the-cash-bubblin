import pandas as pd
import urllib.parse
import re


def normalize_polish_names(location):
    """Replace Polish names without diacritics with proper Polish characters"""
    if not location:
        return location

    # Only keep the most common replacements for names without diacritics
    replacements = {
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
        'sw ': 'św. '
    }

    location_lower = location.lower()
    for incorrect, correct in replacements.items():
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(incorrect) + r'\b'
        location = re.sub(pattern, correct, location, flags=re.IGNORECASE)

    return location


def extract_location_from_data(data_string):
    """Extract potential location from data string"""
    if pd.isna(data_string) or data_string == "":
        return ""

    parts = str(data_string).split('//')

    # First priority: Look for structured location data
    for part in parts:
        part = part.strip()
        if 'lokalizacja:' in part.lower():
            # Extract after "lokalizacja:"
            lokalizacja_pos = part.lower().find('lokalizacja:')
            lokalizacja_text = part[lokalizacja_pos +
                                    len('lokalizacja:'):].strip()

            # Extract address and city
            address = ""
            city = ""

            if 'adres:' in lokalizacja_text.lower():
                adres_start = lokalizacja_text.lower().find('adres:') + len('adres:')
                miasto_pos = lokalizacja_text.lower().find('miasto:', adres_start)

                if miasto_pos != -1:
                    address = lokalizacja_text[adres_start:miasto_pos].strip()
                    miasto_start = miasto_pos + len('miasto:')
                    kraj_pos = lokalizacja_text.lower().find('kraj:', miasto_start)

                    if kraj_pos != -1:
                        city = lokalizacja_text[miasto_start:kraj_pos].strip()
                    else:
                        city = lokalizacja_text[miasto_start:].strip()
                else:
                    address = lokalizacja_text[adres_start:].strip()

            # Combine address and city
            if address and city:
                location = f"{address}, {city}"
            elif address:
                location = address
            elif city:
                location = city
            else:
                location = lokalizacja_text.strip()

            return normalize_polish_names(location) if location else ""

    # Second priority: Look for location after " - "
    for part in parts:
        part = part.strip()
        if ' - ' in part:
            potential_location = part.split(' - ')[-1].strip()
            if potential_location and potential_location.lower() not in ['nan', 'null']:
                return normalize_polish_names(potential_location)

    # Third priority: Look for address patterns
    for part in parts:
        part = part.strip()
        if part and part.lower() not in ['nan', 'null', '']:
            # Check for address indicators or patterns
            if (any(keyword in part.lower() for keyword in ['ul.', 'al.', 'pl.', 'os.', 'centrum'])
                or re.search(r'\w+\s+\w+\s+\d+', part)
                    or (re.search(r'\d+', part) and len(part) > 8)):
                return normalize_polish_names(part)

    # Fourth priority: Any meaningful text
    exclude_terms = ['nan', 'null', 'zakup w terminalu', 'pc game purchase',
                     'grocery store', 'groceries', 'store', 'shop', 'market']
    for part in parts:
        part = part.strip()
        if part and part.lower() not in exclude_terms and len(part) > 3:
            return normalize_polish_names(part)

    return ""


def create_google_maps_link(location):
    """Create Google Maps search link for location"""
    if not location:
        return ""

    # Clean up the location string
    location = location.strip()
    if not location:
        return ""

    # URL encode the location for Google Maps
    encoded_location = urllib.parse.quote(location)
    return f"https://www.google.com/maps/search/{encoded_location}"


# This module is now integrated into the main data processing pipeline
# The functions above are imported and used in data_core.py
