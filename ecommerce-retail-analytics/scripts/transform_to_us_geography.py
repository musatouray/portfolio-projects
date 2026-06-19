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

    filtered_count = 0
    for state in unique_states:
        state_zips = zcta_df[zcta_df['state'] == state].copy()

        # Filter out ZIP codes with null coordinates (ensures all selections have valid coords)
        before_filter = len(state_zips)
        state_zips = state_zips.dropna(subset=['latitude', 'longitude'])
        filtered_count += before_filter - len(state_zips)

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

    if filtered_count > 0:
        print(f"  Filtered {filtered_count:,} ZIP codes with missing coordinates")
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


def transform_geolocation(br_df: pd.DataFrame, zip_mapping: dict[str, dict]) -> pd.DataFrame:
    """
    Transform Brazilian geolocation data to US geolocation.

    Creates one row per unique US zip from the mapping.
    Note: Output has fewer rows than input (BR has multiple lat/lng per zip).

    Args:
        br_df: Brazilian geolocation DataFrame
        zip_mapping: Dictionary mapping BR zip to US zip data

    Returns:
        DataFrame with US geolocation data (one row per unique US zip)
        Schema: geolocation_zip_code_prefix, geolocation_lat, geolocation_lng,
                geolocation_city, geolocation_state
    """
    print("Transforming geolocation data to US geography...")

    # Extract unique US ZIP codes from mapping
    us_zips = {}
    for br_zip, us_data in zip_mapping.items():
        us_zip = us_data['us_zip']

        # Only keep first occurrence of each US ZIP (deterministic)
        if us_zip not in us_zips:
            us_zips[us_zip] = {
                'geolocation_zip_code_prefix': us_zip,
                'geolocation_lat': us_data['us_lat'],
                'geolocation_lng': us_data['us_lng'],
                'geolocation_city': us_data['us_city'],
                'geolocation_state': us_data['us_state']
            }

    # Convert to DataFrame
    us_geo_df = pd.DataFrame(list(us_zips.values()))

    # Sort by zip code for consistency
    us_geo_df = us_geo_df.sort_values('geolocation_zip_code_prefix').reset_index(drop=True)

    # Fill any null cities with "Unknown"
    null_cities = us_geo_df['geolocation_city'].isnull().sum()
    if null_cities > 0:
        us_geo_df['geolocation_city'] = us_geo_df['geolocation_city'].fillna('Unknown')
        print(f"  Filled {null_cities:,} records with unknown city")

    print(f"  Input: {len(br_df):,} Brazilian geolocation records")
    print(f"  Output: {len(us_geo_df):,} US geolocation records (unique US ZIPs)")

    return us_geo_df


def transform_customers(br_df: pd.DataFrame, zip_mapping: dict[str, dict]) -> pd.DataFrame:
    """
    Transform Brazilian customers data to US geography.

    Preserves customer_id and customer_unique_id unchanged.
    Row count must match exactly.

    Args:
        br_df: Brazilian customers DataFrame
        zip_mapping: Dictionary mapping BR zip to US zip data

    Returns:
        DataFrame with US customer data (same row count as input)
    """
    print("Transforming customers data to US geography...")

    # Copy DataFrame to avoid modifying original
    us_df = br_df.copy()

    # Normalize Brazilian zip codes (ensure 5 digits with leading zeros)
    br_zips = us_df['customer_zip_code_prefix'].astype(str).str.zfill(5)

    # Map each BR zip to US values using the mapping dict
    # For zips not in mapping, use a default US zip (most common state = CA)
    default_entry = {'us_zip': '90001', 'us_city': 'Los Angeles', 'us_state': 'CA',
                     'us_lat': 33.9731, 'us_lng': -118.2479}

    us_df['customer_zip_code_prefix'] = br_zips.map(
        lambda br_zip: zip_mapping.get(br_zip, default_entry)['us_zip']
    )
    us_df['customer_city'] = br_zips.map(
        lambda br_zip: zip_mapping.get(br_zip, default_entry)['us_city']
    )
    us_df['customer_state'] = br_zips.map(
        lambda br_zip: zip_mapping.get(br_zip, default_entry)['us_state']
    )

    # Count unmapped records
    unmapped = br_zips.apply(lambda z: z not in zip_mapping).sum()
    if unmapped > 0:
        print(f"  Warning: {unmapped:,} customers with unmapped BR zips (defaulted to Los Angeles, CA)")

    # Fill any null cities with "Unknown"
    null_cities = us_df['customer_city'].isnull().sum()
    if null_cities > 0:
        us_df['customer_city'] = us_df['customer_city'].fillna('Unknown')
        print(f"  Filled {null_cities:,} records with unknown city")

    print(f"  Input: {len(br_df):,} customers")
    print(f"  Output: {len(us_df):,} customers (row count preserved)")

    # Verify row count matches exactly
    assert len(us_df) == len(br_df), f"Row count mismatch: {len(us_df)} != {len(br_df)}"

    return us_df


def transform_sellers(br_df: pd.DataFrame, zip_mapping: dict[str, dict]) -> pd.DataFrame:
    """
    Transform Brazilian sellers data to US geography.

    Preserves seller_id unchanged.
    Row count must match exactly.

    Args:
        br_df: Brazilian sellers DataFrame
        zip_mapping: Dictionary mapping BR zip to US zip data

    Returns:
        DataFrame with US seller data (same row count as input)
    """
    print("Transforming sellers data to US geography...")

    # Copy DataFrame to avoid modifying original
    us_df = br_df.copy()

    # Normalize Brazilian zip codes (ensure 5 digits with leading zeros)
    br_zips = us_df['seller_zip_code_prefix'].astype(str).str.zfill(5)

    # Map each BR zip to US values using the mapping dict
    # For zips not in mapping, use a default US zip (most common state = CA)
    default_entry = {'us_zip': '90001', 'us_city': 'Los Angeles', 'us_state': 'CA',
                     'us_lat': 33.9731, 'us_lng': -118.2479}

    us_df['seller_zip_code_prefix'] = br_zips.map(
        lambda br_zip: zip_mapping.get(br_zip, default_entry)['us_zip']
    )
    us_df['seller_city'] = br_zips.map(
        lambda br_zip: zip_mapping.get(br_zip, default_entry)['us_city']
    )
    us_df['seller_state'] = br_zips.map(
        lambda br_zip: zip_mapping.get(br_zip, default_entry)['us_state']
    )

    # Count unmapped records
    unmapped = br_zips.apply(lambda z: z not in zip_mapping).sum()
    if unmapped > 0:
        print(f"  Warning: {unmapped:,} sellers with unmapped BR zips (defaulted to Los Angeles, CA)")

    # Fill any null cities with "Unknown"
    null_cities = us_df['seller_city'].isnull().sum()
    if null_cities > 0:
        us_df['seller_city'] = us_df['seller_city'].fillna('Unknown')
        print(f"  Filled {null_cities:,} records with unknown city")

    print(f"  Input: {len(br_df):,} sellers")
    print(f"  Output: {len(us_df):,} sellers (row count preserved)")

    # Verify row count matches exactly
    assert len(us_df) == len(br_df), f"Row count mismatch: {len(us_df)} != {len(br_df)}"

    return us_df


def main():
    """
    Full pipeline to transform Brazilian datasets to US geography and write CSV files.

    Steps:
    1. Download US ZCTA data and build lookup
    2. Load Brazilian CSV files (geolocation, customers, sellers)
    3. Create deterministic ZIP mapping
    4. Transform all 3 datasets
    5. Write to CSV files
    6. Print validation summary
    """
    print("=" * 80)
    print("US GEOGRAPHY TRANSFORMATION PIPELINE")
    print("=" * 80)

    # Step 1: Download US data and build lookup
    print("\n[Step 1/6] Downloading US ZCTA data...")
    zcta_df = download_zcta_data()

    print("\n[Step 2/6] Building ZIP code lookup...")
    us_zip_lookup = build_zip_lookup(zcta_df)

    # Step 2: Load Brazilian datasets
    print("\n[Step 3/6] Loading Brazilian datasets...")

    br_geo_path = DATA_RAW_DIR / "olist_geolocation_dataset.csv"
    br_customers_path = DATA_RAW_DIR / "olist_customers_dataset.csv"
    br_sellers_path = DATA_RAW_DIR / "olist_sellers_dataset.csv"

    # Check files exist
    for path in [br_geo_path, br_customers_path, br_sellers_path]:
        if not path.exists():
            print(f"ERROR: File not found: {path}")
            print("Please run download_kaggle_data.py first")
            exit(1)

    # Load datasets
    br_geo_df = pd.read_csv(br_geo_path, dtype={'geolocation_zip_code_prefix': str})
    br_customers_df = pd.read_csv(br_customers_path, dtype={'customer_zip_code_prefix': str})
    br_sellers_df = pd.read_csv(br_sellers_path, dtype={'seller_zip_code_prefix': str})

    print(f"  - Geolocation: {len(br_geo_df):,} records")
    print(f"  - Customers: {len(br_customers_df):,} records")
    print(f"  - Sellers: {len(br_sellers_df):,} records")

    # Step 3: Create ZIP mapping
    print("\n[Step 4/6] Creating ZIP code mapping...")
    zip_mapping = create_zip_mapping(br_geo_df, us_zip_lookup)

    # Step 4: Transform datasets
    print("\n[Step 5/6] Transforming datasets...")
    us_geo_df = transform_geolocation(br_geo_df, zip_mapping)
    us_customers_df = transform_customers(br_customers_df, zip_mapping)
    us_sellers_df = transform_sellers(br_sellers_df, zip_mapping)

    # Step 5: Write CSV files
    print("\n[Step 6/6] Writing CSV files...")

    us_geo_path = DATA_RAW_DIR / "us_geolocation_dataset.csv"
    us_customers_path = DATA_RAW_DIR / "us_customers_dataset.csv"
    us_sellers_path = DATA_RAW_DIR / "us_sellers_dataset.csv"

    us_geo_df.to_csv(us_geo_path, index=False)
    us_customers_df.to_csv(us_customers_path, index=False)
    us_sellers_df.to_csv(us_sellers_path, index=False)

    print(f"  - {us_geo_path}")
    print(f"  - {us_customers_path}")
    print(f"  - {us_sellers_path}")

    # Step 6: Validation summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    # Row counts
    print("\nRow Counts:")
    print(f"  - Geolocation: {len(us_geo_df):,} (reduced from {len(br_geo_df):,})")
    print(f"  - Customers: {len(us_customers_df):,} (expected: 99,441)")
    print(f"  - Sellers: {len(us_sellers_df):,} (expected: 3,095)")

    # Validate customer count
    customer_match = len(us_customers_df) == 99_441
    print(f"    [OK] Customers count matches" if customer_match else f"    [ERROR] Customers count MISMATCH")

    # Validate seller count
    seller_match = len(us_sellers_df) == 3_095
    print(f"    [OK] Sellers count matches" if seller_match else f"    [ERROR] Sellers count MISMATCH")

    # Coordinate bounds
    print("\nCoordinate Bounds (US: lat 24-50, lng -125 to -66):")
    lat_min = us_geo_df['geolocation_lat'].min()
    lat_max = us_geo_df['geolocation_lat'].max()
    lng_min = us_geo_df['geolocation_lng'].min()
    lng_max = us_geo_df['geolocation_lng'].max()

    print(f"  - Latitude: {lat_min:.2f} to {lat_max:.2f}")
    print(f"  - Longitude: {lng_min:.2f} to {lng_max:.2f}")

    lat_valid = 24 <= lat_min and lat_max <= 50
    lng_valid = -125 <= lng_min and lng_max <= -66

    print(f"    [OK] Coordinates in valid US range" if (lat_valid and lng_valid) else f"    [ERROR] Coordinates OUT OF RANGE")

    # Check for null values
    print("\nNull Values:")
    print(f"  - Geolocation: {us_geo_df.isnull().sum().sum()} nulls")
    print(f"  - Customers: {us_customers_df.isnull().sum().sum()} nulls")
    print(f"  - Sellers: {us_sellers_df.isnull().sum().sum()} nulls")

    print("\n" + "=" * 80)
    print("TRANSFORMATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    main()
