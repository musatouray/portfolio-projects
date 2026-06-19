"""
Transform Brazilian e-commerce data to US geography using mapping tables and ZCTA data.

This script provides:
1. State and city mappings from Brazil to US
2. ZCTA (ZIP Code Tabulation Area) data download and processing
3. ZIP code lookup utilities for geographic transformation
"""

import hashlib
import io
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


if __name__ == "__main__":
    # Test the functionality
    print("Testing ZCTA download and lookup building...")
    print("=" * 60)

    # Download ZCTA data
    zcta_df = download_zcta_data()
    print(f"\nTotal ZIP codes: {len(zcta_df):,}")
    print(f"Total states: {zcta_df['state'].nunique()}")

    # Build lookup
    zip_lookup = build_zip_lookup(zcta_df)

    # Print California example
    ca_zips = zip_lookup.get('CA', [])
    print(f"\nCalifornia ZIP codes: {len(ca_zips):,}")
    if ca_zips:
        print(f"First CA ZIP: {ca_zips[0]}")
        print(f"Last CA ZIP: {ca_zips[-1]}")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
