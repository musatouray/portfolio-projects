"""
Transform Brazilian e-commerce data to US geography using mapping tables and ZCTA data.

This script provides:
1. State and city mappings from Brazil to US
2. ZCTA (ZIP Code Tabulation Area) data download and processing
3. ZIP code lookup utilities for geographic transformation
"""

import hashlib
import io
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd
import requests

# Path constants
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# ZCTA data sources
ZCTA_COORDS_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_zcta_national.zip"
# GitHub-hosted ZIP code database (includes state, county, city)
ZIP_DATABASE_URL = "https://raw.githubusercontent.com/scpike/us-state-county-zip/master/geo-data.csv"

# Brazilian state → US state mapping
STATE_MAPPING = {
    "SP": "CA",  # São Paulo → California
    "RJ": "NY",  # Rio de Janeiro → New York
    "MG": "TX",  # Minas Gerais → Texas
    "RS": "FL",  # Rio Grande do Sul → Florida
    "PR": "IL",  # Paraná → Illinois
    "SC": "WA",  # Santa Catarina → Washington
    "BA": "GA",  # Bahia → Georgia
    "DF": "DC",  # Distrito Federal → District of Columbia
    "ES": "NJ",  # Espírito Santo → New Jersey
    "GO": "AZ",  # Goiás → Arizona
    "PE": "NC",  # Pernambuco → North Carolina
    "CE": "TN",  # Ceará → Tennessee
    "PA": "OR",  # Pará → Oregon
    "MT": "CO",  # Mato Grosso → Colorado
    "MA": "AL",  # Maranhão → Alabama
    "MS": "NV",  # Mato Grosso do Sul → Nevada
    "PB": "SC",  # Paraíba → South Carolina
    "RN": "LA",  # Rio Grande do Norte → Louisiana
    "PI": "AR",  # Piauí → Arkansas
    "AL": "MS",  # Alagoas → Mississippi
    "SE": "OK",  # Sergipe → Oklahoma
    "TO": "KS",  # Tocantins → Kansas
    "RO": "NM",  # Rondônia → New Mexico
    "AM": "AK",  # Amazonas → Alaska
    "AC": "MT",  # Acre → Montana
    "AP": "WY",  # Amapá → Wyoming
    "RR": "VT",  # Roraima → Vermont
}

# (lowercase BR city, BR state) → (US city, US state) mapping
CITY_MAPPING = {
    ("sao paulo", "SP"): ("Los Angeles", "CA"),
    ("rio de janeiro", "RJ"): ("New York", "NY"),
    ("belo horizonte", "MG"): ("Houston", "TX"),
    ("brasilia", "DF"): ("Washington", "DC"),
    ("curitiba", "PR"): ("Chicago", "IL"),
    ("porto alegre", "RS"): ("Miami", "FL"),
    ("salvador", "BA"): ("Atlanta", "GA"),
    ("recife", "PE"): ("Charlotte", "NC"),
    ("fortaleza", "CE"): ("Nashville", "TN"),
    ("campinas", "SP"): ("San Diego", "CA"),
}


def download_zip_database() -> pd.DataFrame:
    """
    Download ZIP code database with state and city information.

    Returns:
        DataFrame with columns: zip_code, state, city
    """
    print(f"Downloading ZIP code database from {ZIP_DATABASE_URL}...")

    # Download the CSV file
    response = requests.get(ZIP_DATABASE_URL, timeout=60)
    response.raise_for_status()

    # Read CSV file
    df = pd.read_csv(io.StringIO(response.text), dtype={'zipcode': str})

    print(f"Loaded {len(df):,} ZIP code records")

    # Select and rename columns (select first to avoid duplicate column names)
    df = df[['zipcode', 'state_abbr', 'city']].copy()
    df = df.rename(columns={
        'zipcode': 'zip_code',
        'state_abbr': 'state'
    })

    # Get unique ZIP codes (first occurrence)
    df = df.drop_duplicates(subset=['zip_code'], keep='first')

    print(f"Found {len(df):,} unique ZIP codes")

    return df


def download_zcta_coords() -> pd.DataFrame:
    """
    Download ZCTA coordinate data from US Census Bureau.

    Returns:
        DataFrame with columns: zip_code, latitude, longitude
    """
    print(f"Downloading ZCTA coordinates from {ZCTA_COORDS_URL}...")
    response = requests.get(ZCTA_COORDS_URL, timeout=60)
    response.raise_for_status()

    # Extract the .txt file from the ZIP
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        # Find the .txt file in the archive
        txt_files = [name for name in z.namelist() if name.endswith('.txt')]
        if not txt_files:
            raise ValueError("No .txt file found in ZCTA ZIP archive")

        txt_file = txt_files[0]
        print(f"Extracting {txt_file}...")

        with z.open(txt_file) as f:
            # Parse tab-delimited file, ensuring GEOID is read as string
            df = pd.read_csv(f, sep='\t', dtype={'GEOID': str})

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    print(f"Loaded {len(df):,} ZCTA coordinate records")

    # Rename columns to match our schema
    df = df.rename(columns={
        'GEOID': 'zip_code',
        'INTPTLAT': 'latitude',
        'INTPTLONG': 'longitude'
    })

    # Select only needed columns
    df = df[['zip_code', 'latitude', 'longitude']]

    return df


def download_zcta_data() -> pd.DataFrame:
    """
    Download and process ZCTA (ZIP Code Tabulation Area) data from US Census Bureau.
    Combines ZIP database with Census coordinate data.

    Returns:
        DataFrame with columns: zip_code, state, city, latitude, longitude
    """
    # Download ZIP database with state and city
    zip_db_df = download_zip_database()

    # Download ZCTA coordinates
    coords_df = download_zcta_coords()

    # Merge the two datasets
    print("Merging ZIP database with coordinates...")
    df = zip_db_df.merge(coords_df, on='zip_code', how='left')

    # Select final columns
    df = df[['zip_code', 'state', 'city', 'latitude', 'longitude']]

    print(f"Final dataset: {len(df):,} ZIP codes with state, city, and coordinates")

    return df


def build_zip_lookup(zcta_df: pd.DataFrame) -> dict[str, list[dict]]:
    """
    Build a lookup dictionary of US ZIP codes grouped by state.

    Args:
        zcta_df: DataFrame with ZCTA data

    Returns:
        Dictionary mapping state code to list of ZIP code entries.
        Each entry contains: zip_code, latitude, longitude, city
    """
    print("Building ZIP code lookup by state...")

    lookup = {}

    # Get unique states
    unique_states = zcta_df['state'].dropna().unique()

    for state in unique_states:
        state_zips = zcta_df[zcta_df['state'] == state].copy()

        # Sort by zip_code for deterministic ordering
        state_zips = state_zips.sort_values('zip_code')

        # Convert to list of dicts
        lookup[state] = [
            {
                'zip_code': row['zip_code'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'city': row['city']
            }
            for _, row in state_zips.iterrows()
        ]

    print(f"Built lookup for {len(lookup)} states")
    return lookup


def deterministic_choice(items: list, seed_string: str):
    """
    Deterministically select an item from a list using a hash-based seed.

    Args:
        items: List of items to choose from
        seed_string: String to use as seed (e.g., Brazilian zip code)

    Returns:
        A single item from the list, always the same for the same seed
    """
    # Hash the seed string using MD5
    hash_obj = hashlib.md5(seed_string.encode('utf-8'))

    # Convert first 8 bytes to integer
    hash_bytes = hash_obj.digest()[:8]
    hash_int = int.from_bytes(hash_bytes, byteorder='big')

    # Use modulo to select an item
    index = hash_int % len(items)
    return items[index]


def normalize_city_name(city: str) -> str:
    """
    Normalize city name by removing accents and converting to lowercase.

    Args:
        city: City name to normalize

    Returns:
        Normalized city name (lowercase, no accents)
    """
    # NFKD normalization separates base characters from combining marks
    normalized = unicodedata.normalize('NFKD', city)

    # Filter out combining characters (accents)
    without_accents = ''.join([c for c in normalized if not unicodedata.combining(c)])

    # Return lowercase and stripped
    return without_accents.lower().strip()


def create_zip_mapping(
    br_geolocation_df: pd.DataFrame,
    us_zip_lookup: dict[str, list[dict]]
) -> dict[str, dict]:
    """
    Create deterministic mapping from Brazilian ZIP codes to US ZIP codes.

    Args:
        br_geolocation_df: DataFrame with Brazilian geolocation data
        us_zip_lookup: Dictionary mapping US state to list of ZIP entries

    Returns:
        Dictionary mapping Brazilian zip code to US zip data:
        {br_zip: {us_zip, us_city, us_state, us_lat, us_lng}}
    """
    print("Creating deterministic ZIP code mapping...")

    # Get unique Brazilian ZIP codes with their city/state
    br_zips = (
        br_geolocation_df
        .groupby('geolocation_zip_code_prefix')
        .agg({
            'geolocation_city': 'first',
            'geolocation_state': 'first'
        })
        .reset_index()
    )

    print(f"Found {len(br_zips):,} unique Brazilian ZIP codes")

    # Build city_zips lookup: (normalized_city, state) -> list of zip entries
    print("Building city-based lookup...")
    city_zips = {}

    for state, zip_list in us_zip_lookup.items():
        for zip_entry in zip_list:
            if pd.notna(zip_entry['city']):
                normalized_city = normalize_city_name(zip_entry['city'])
                key = (normalized_city, state)

                if key not in city_zips:
                    city_zips[key] = []

                city_zips[key].append(zip_entry)

    print(f"Built city lookup with {len(city_zips):,} unique (city, state) combinations")

    # Create mapping for each Brazilian ZIP
    zip_mapping = {}
    city_matched = 0
    state_matched = 0

    for _, row in br_zips.iterrows():
        br_zip = row['geolocation_zip_code_prefix']
        br_city = row['geolocation_city']
        br_state = row['geolocation_state']

        # Get corresponding US state
        us_state = STATE_MAPPING.get(br_state)
        if not us_state:
            print(f"Warning: No US state mapping for {br_state}")
            continue

        # Normalize Brazilian city name
        normalized_br_city = normalize_city_name(br_city)

        # Try city mapping first
        city_mapping_key = (normalized_br_city, br_state)
        if city_mapping_key in CITY_MAPPING:
            us_city, us_state_from_mapping = CITY_MAPPING[city_mapping_key]
            normalized_us_city = normalize_city_name(us_city)
            city_state_key = (normalized_us_city, us_state_from_mapping)

            if city_state_key in city_zips:
                # Use deterministic choice from city's ZIP codes
                us_zip_entry = deterministic_choice(city_zips[city_state_key], br_zip)
                city_matched += 1
            else:
                # Fall back to state-level if city not found
                us_zip_entry = deterministic_choice(us_zip_lookup[us_state], br_zip)
                state_matched += 1
        else:
            # Use state-level mapping
            us_zip_entry = deterministic_choice(us_zip_lookup[us_state], br_zip)
            state_matched += 1

        # Store the mapping
        zip_mapping[br_zip] = {
            'us_zip': us_zip_entry['zip_code'],
            'us_city': us_zip_entry['city'],
            'us_state': us_state,
            'us_lat': us_zip_entry['latitude'],
            'us_lng': us_zip_entry['longitude']
        }

    print(f"Created {len(zip_mapping):,} ZIP mappings:")
    print(f"  - City-matched: {city_matched:,}")
    print(f"  - State-matched: {state_matched:,}")

    return zip_mapping


if __name__ == "__main__":
    # Test the functionality
    print("Testing ZCTA download and ZIP mapping creation...")
    print("=" * 60)

    # Download ZCTA data
    zcta_df = download_zcta_data()
    print(f"\nTotal US ZIP codes: {len(zcta_df):,}")
    print(f"Total US states: {zcta_df['state'].nunique()}")

    # Build lookup
    zip_lookup = build_zip_lookup(zcta_df)

    # Print California example
    ca_zips = zip_lookup.get('CA', [])
    print(f"\nCalifornia ZIP codes: {len(ca_zips):,}")
    if ca_zips:
        print(f"First CA ZIP: {ca_zips[0]}")
        print(f"Last CA ZIP: {ca_zips[-1]}")

    # Load Brazilian geolocation data
    print("\n" + "=" * 60)
    print("Loading Brazilian geolocation data...")

    br_geo_path = DATA_RAW_DIR / "olist_geolocation_dataset.csv"
    if not br_geo_path.exists():
        print(f"ERROR: Brazilian geolocation file not found at {br_geo_path}")
        print("Please run download_kaggle_data.py first")
        exit(1)

    br_geo_df = pd.read_csv(
        br_geo_path,
        dtype={'geolocation_zip_code_prefix': str}
    )
    print(f"Loaded {len(br_geo_df):,} Brazilian geolocation records")

    # Create ZIP mapping
    print("\n" + "=" * 60)
    zip_mapping = create_zip_mapping(br_geo_df, zip_lookup)

    # Print sample mappings
    print("\n" + "=" * 60)
    print("Sample ZIP mappings:")
    print("-" * 60)

    sample_count = 0
    for br_zip, us_data in zip_mapping.items():
        if sample_count >= 10:
            break

        print(f"\nBrazilian ZIP: {br_zip}")
        print(f"  -> US ZIP: {us_data['us_zip']}")
        print(f"  -> US City: {us_data['us_city']}")
        print(f"  -> US State: {us_data['us_state']}")
        print(f"  -> Coordinates: ({us_data['us_lat']:.4f}, {us_data['us_lng']:.4f})")

        sample_count += 1

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print(f"Total ZIP mappings created: {len(zip_mapping):,}")
