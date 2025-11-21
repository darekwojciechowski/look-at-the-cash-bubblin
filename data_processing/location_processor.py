import pandas as pd
import urllib.parse
import re


def clean_location_text(location):
    """Remove unnecessary country information and clean up formatting"""
    if not location:
        return location

    # Remove country information (any pattern like "kraj: xxxxx")
    location = re.sub(r'\s*kraj\s*:\s*[^,]*',
                      '', location, flags=re.IGNORECASE)

    # Clean up common prefixes that might remain
    prefixes_to_remove = ['miasto :', 'miasto:',
                          'adres :', 'adres:', 'lokalizacja :', 'lokalizacja:']
    for prefix in prefixes_to_remove:
        location = location.replace(prefix, ' ')

    # Clean up formatting
    location = re.sub(r'\s*:\s*', ', ', location)  # Replace colons with commas
    # Replace multiple spaces with single
    location = re.sub(r'\s+', ' ', location)
    location = re.sub(r',\s*,', ',', location)  # Remove double commas
    # Remove leading/trailing spaces and commas
    location = location.strip(' ,')

    return location


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

    # First priority: Look for structured location data in any part
    for part in parts:
        part = part.strip()
        # Check if this part contains structured location data (with or without spaces before colons)
        if ('lokalizacja:' in part.lower() or 'lokalizacja :' in part.lower()) and ('adres:' in part.lower() or 'adres :' in part.lower()):
            # Extract the structured part - it might be after " - "
            if ' - ' in part:
                # Take everything after the last " - " if it contains lokalizacja
                location_part = part.split(' - ')[-1].strip()
                if 'lokalizacja:' in location_part.lower() or 'lokalizacja :' in location_part.lower():
                    part = location_part

            # Extract after "lokalizacja:" or "lokalizacja :"
            if 'lokalizacja:' in part.lower():
                lokalizacja_pos = part.lower().find('lokalizacja:')
                lokalizacja_text = part[lokalizacja_pos +
                                        len('lokalizacja:'):].strip()
            else:
                lokalizacja_pos = part.lower().find('lokalizacja :')
                lokalizacja_text = part[lokalizacja_pos +
                                        len('lokalizacja :'):].strip()

            # Extract address and city with improved parsing
            address = ""
            city = ""

            if 'adres:' in lokalizacja_text.lower() or 'adres :' in lokalizacja_text.lower():
                if 'adres:' in lokalizacja_text.lower():
                    adres_start = lokalizacja_text.lower().find('adres:') + len('adres:')
                else:
                    adres_start = lokalizacja_text.lower().find('adres :') + len('adres :')

                # Look for explicit "miasto:" first
                miasto_pos = lokalizacja_text.lower().find('miasto:', adres_start)

                if miasto_pos != -1:
                    # Standard format: "adres: ... miasto: ... kraj: ..."
                    address = lokalizacja_text[adres_start:miasto_pos].strip()
                    miasto_start = miasto_pos + len('miasto:')
                    kraj_pos = lokalizacja_text.lower().find('kraj:', miasto_start)

                    if kraj_pos != -1:
                        city = lokalizacja_text[miasto_start:kraj_pos].strip()
                    else:
                        city = lokalizacja_text[miasto_start:].strip()
                else:
                    # Alternative format: "adres: ul. name : city kraj: ..."
                    # Look for "kraj:" to find where city ends
                    kraj_pos = lokalizacja_text.lower().find('kraj:', adres_start)

                    if kraj_pos != -1:
                        # Extract everything between "adres:" and "kraj:"
                        full_address = lokalizacja_text[adres_start:kraj_pos].strip(
                        )

                        # Try to split by last colon to separate address from city
                        colon_parts = full_address.split(':')
                        if len(colon_parts) >= 2:
                            # Last part after colon is likely the city
                            city = colon_parts[-1].strip()
                            # Everything before last colon is the address
                            address = ':'.join(colon_parts[:-1]).strip()
                        else:
                            # No additional colon found, treat as address only
                            address = full_address
                    else:
                        # No "kraj:" found, treat everything as address
                        address = lokalizacja_text[adres_start:].strip()

            # Clean up and combine address and city
            if address and city:
                location = f"{address}, {city}"
            elif address:
                location = address
            elif city:
                location = city
            else:
                # If structured parsing failed, try to extract just the useful part
                location = lokalizacja_text.strip()

            # Always clean the location before returning
            location = clean_location_text(location)
            return normalize_polish_names(location) if location else ""
    # Second priority: Look for location after " - " (but only for non-structured data)
    for part in parts:
        part = part.strip()
        if ' - ' in part and 'lokalizacja:' not in part.lower() and 'lokalizacja :' not in part.lower():
            potential_location = part.split(' - ')[-1].strip()
            if potential_location and potential_location.lower() not in ['nan', 'null']:
                cleaned_location = clean_location_text(potential_location)
                return normalize_polish_names(cleaned_location)

    # Third priority: Look for address patterns
    for part in parts:
        part = part.strip()
        if part and part.lower() not in ['nan', 'null', '']:
            # Check for address indicators or patterns
            if (any(keyword in part.lower() for keyword in ['ul.', 'al.', 'pl.', 'os.', 'centrum'])
                or re.search(r'\w+\s+\w+\s+\d+', part)
                    or (re.search(r'\d+', part) and len(part) > 8)):
                cleaned_part = clean_location_text(part)
                return normalize_polish_names(cleaned_part)

    # Fourth priority: Any meaningful text
    exclude_terms = ['nan', 'null', 'zakup w terminalu', 'pc game purchase',
                     'grocery store', 'groceries', 'store', 'shop', 'market']
    for part in parts:
        part = part.strip()
        if part and part.lower() not in exclude_terms and len(part) > 3:
            cleaned_part = clean_location_text(part)
            return normalize_polish_names(cleaned_part)

    return ""


def create_google_maps_link(location):
    """Create Google Maps search link for location"""
    if not location:
        return ""

    # Clean up the location string
    location = location.strip()
    if not location:
        return ""

    # Check if the location contains actual address information
    # Only create links for locations that have:
    # - Street indicators (ul., al., pl., os.)
    # - Numbers (suggesting address)
    # - City names (common Polish cities)
    # - Commas (suggesting structured address like "ul. name, city")
    location_lower = location.lower()

    has_street_indicator = any(indicator in location_lower for indicator in [
                               'ul.', 'al.', 'pl.', 'os.', 'aleja', 'ulica', 'plac', 'osiedle'])
    has_comma = ',' in location
    has_number = re.search(r'\d+', location)
    has_city_keywords = any(city in location_lower for city in [
                            'warszawa', 'kraków', 'łódź', 'wrocław', 'poznań', 'gdańsk', 'szczecin', 'bydgoszcz', 'lublin', 'katowice'])

    # Only generate link if location looks like a real address
    if not (has_street_indicator or (has_comma and (has_number or has_city_keywords))):
        return ""

    # Remove any leftover prefixes that shouldn't be in Google Maps links
    prefixes_to_remove = [
        'lokalizacja:',
        'lokalizacja :',
        'adres:',
        'adres :',
        'miasto:',
        'miasto :',
        'kraj:',
        'kraj :'
    ]

    for prefix in prefixes_to_remove:
        if location_lower.startswith(prefix):
            location = location[len(prefix):].strip()
            location_lower = location.lower()

    # Additional cleanup for Google Maps - remove internal prefixes and format nicely
    # Replace patterns like ": warszawa kraj : polska" with ", warszawa"
    location = re.sub(r'\s*:\s*([^:]+?)\s+kraj\s*:\s*\w+$', r', \1', location)
    # Clean up any remaining colons and multiple spaces
    location = re.sub(r'\s*:\s*', ', ', location)
    location = re.sub(r'\s+', ' ', location)
    location = re.sub(r',\s*,', ',', location)
    location = location.strip(' ,')

    # URL encode the location for Google Maps
    encoded_location = urllib.parse.quote(location)
    return f"https://www.google.com/maps/search/{encoded_location}"
# This module is now integrated into the main data processing pipeline
# The functions above are imported and used in data_core.py
