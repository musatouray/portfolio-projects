# US Geography Transformation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Brazilian Olist e-commerce geography data to US equivalents for portfolio presentation with accurate Azure Maps coordinates.

**Architecture:** A Python transformation script downloads US Census ZCTA data, builds deterministic mappings from Brazilian to US geography (state→state, city→city, zip→zip), and generates three new CSV files. The existing `load_to_snowflake.py` is updated to load the US files instead of Brazilian files.

**Tech Stack:** Python 3.12, pandas, requests (for Census data download)

## Global Constraints

- Python 3.12 required (per pyproject.toml)
- Use `uv` for dependency management
- Deterministic output: same input always produces same output (hash-based seeding)
- Preserve all non-geographic columns unchanged (customer_id, seller_id, etc.)
- Row counts must match exactly: customers=99,441, sellers=3,095
- US coordinates must be valid: latitude 24°-50°N, longitude 66°-125°W

---

## File Structure

```
ecommerce-retail-analytics/
├── scripts/
│   ├── transform_to_us_geography.py    # NEW - Main transformation script
│   └── load_to_snowflake.py            # MODIFY - Update TABLE_MAPPING
├── data/
│   └── raw/
│       ├── olist_geolocation_dataset.csv   # Existing (preserved)
│       ├── olist_customers_dataset.csv     # Existing (preserved)
│       ├── olist_sellers_dataset.csv       # Existing (preserved)
│       ├── us_geolocation_dataset.csv      # NEW - Generated output
│       ├── us_customers_dataset.csv        # NEW - Generated output
│       └── us_sellers_dataset.csv          # NEW - Generated output
└── pyproject.toml                          # MODIFY - Add requests dependency
```

---

### Task 1: Add requests dependency

**Files:**
- Modify: `pyproject.toml:6-13`

**Interfaces:**
- Consumes: None
- Produces: `requests` package available for HTTP downloads

- [ ] **Step 1: Add requests to dependencies**

Edit `pyproject.toml` to add `requests>=2.31.0` to the dependencies list:

```toml
dependencies = [
    "dbt-snowflake>=1.7.0",
    "kaggle>=1.6.0",
    "python-dotenv>=1.0.0",
    "pandas>=2.0.0",
    "snowflake-connector-python[pandas]>=3.6.0",
    "cryptography>=42.0.0",
    "requests>=2.31.0",
]
```

- [ ] **Step 2: Sync dependencies**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv sync`

Expected: Dependencies installed successfully, including requests

- [ ] **Step 3: Verify requests is available**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python -c "import requests; print(requests.__version__)"`

Expected: Version number printed (e.g., `2.31.0` or higher)

- [ ] **Step 4: Commit**

```bash
cd C:\dev\portfolios\ecommerce-retail-analytics
git add pyproject.toml uv.lock
git commit -m "chore: add requests dependency for Census data download"
```

---

### Task 2: Create transformation script with mapping tables

**Files:**
- Create: `scripts/transform_to_us_geography.py`

**Interfaces:**
- Consumes: `requests` package, Census ZCTA URL
- Produces:
  - `STATE_MAPPING: dict[str, str]` - Brazilian state code → US state code
  - `CITY_MAPPING: dict[tuple[str, str], tuple[str, str]]` - (BR city, BR state) → (US city, US state)
  - `download_zcta_data() -> pd.DataFrame` - Downloads and parses Census ZCTA file
  - `build_zip_lookup(zcta_df: pd.DataFrame) -> dict` - Groups US zips by state and city

- [ ] **Step 1: Create script with imports and constants**

Create `scripts/transform_to_us_geography.py`:

```python
"""
Transform Brazilian Olist e-commerce geography data to US equivalents.

Downloads US Census ZCTA data and creates deterministic mappings from
Brazilian states/cities/zips to US equivalents.
"""

import hashlib
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Census ZCTA Gazetteer file URL
ZCTA_URL = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_zcta_national.zip"

# Brazilian state → US state mapping (by economic role and population weight)
STATE_MAPPING: dict[str, str] = {
    "SP": "CA",  # Economic powerhouse, tech hub
    "RJ": "NY",  # Second city, finance, culture
    "MG": "TX",  # Large interior, industrial
    "RS": "FL",  # Southern, tourism
    "PR": "IL",  # Industrial midwest
    "SC": "WA",  # Tech-friendly, quality of life
    "BA": "GA",  # Southern, growing economy
    "DF": "DC",  # Capital district
    "ES": "NJ",  # Small coastal near major metro
    "GO": "AZ",  # Interior growth state
    "PE": "NC",  # Regional hub, growing tech
    "CE": "TN",  # Regional center
    "PA": "OR",  # Natural resources
    "MT": "CO",  # Interior, agriculture
    "MA": "AL",  # Southern, developing
    "MS": "NV",  # Interior, sparse
    "PB": "SC",  # Small southern coastal
    "RN": "LA",  # Coastal southern
    "PI": "AR",  # Interior southern
    "AL": "MS",  # Small southern
    "SE": "OK",  # Small interior
    "TO": "KS",  # Central interior
    "RO": "NM",  # Western interior
    "AM": "AK",  # Remote, natural resources
    "AC": "MT",  # Remote, sparse
    "AP": "WY",  # Sparse, remote
    "RR": "VT",  # Small, remote
}

# Top 10 Brazilian cities → US metros (for urban clustering)
# Key: (lowercase BR city, BR state) → (US city, US state)
CITY_MAPPING: dict[tuple[str, str], tuple[str, str]] = {
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


def download_zcta_data() -> pd.DataFrame:
    """Download and parse US Census ZCTA Gazetteer data.

    Returns:
        DataFrame with columns: zip_code, state, city, latitude, longitude
    """
    print("Downloading US Census ZCTA data...")
    response = requests.get(ZCTA_URL, timeout=60)
    response.raise_for_status()

    # Extract the text file from the zip
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        # Find the .txt file in the archive
        txt_files = [f for f in zf.namelist() if f.endswith(".txt")]
        if not txt_files:
            raise ValueError("No .txt file found in ZCTA zip archive")

        with zf.open(txt_files[0]) as f:
            # ZCTA file is tab-delimited with specific columns
            df = pd.read_csv(
                f,
                sep="\t",
                dtype={"GEOID": str},
                encoding="latin-1",
            )

    print(f"  Downloaded {len(df):,} zip codes")

    # Rename and select columns
    # GEOID = zip code, USPS_ZIP_PREF_STATE = state, INTPTLAT/INTPTLONG = coordinates
    df = df.rename(columns={
        "GEOID": "zip_code",
        "USPS_ZIP_PREF_STATE": "state",
        "INTPTLAT": "latitude",
        "INTPTLONG": "longitude",
    })

    # The ZCTA file doesn't have city names directly
    # We'll use a placeholder and assign cities based on zip ranges
    df["city"] = "Unknown"

    return df[["zip_code", "state", "city", "latitude", "longitude"]]


def build_zip_lookup(zcta_df: pd.DataFrame) -> dict[str, list[dict]]:
    """Build lookup tables for US zips grouped by state.

    Args:
        zcta_df: DataFrame from download_zcta_data()

    Returns:
        Dict mapping US state code to list of zip info dicts
        Each dict has: zip_code, latitude, longitude, city
    """
    lookup: dict[str, list[dict]] = {}

    for _, row in zcta_df.iterrows():
        state = row["state"]
        if state not in lookup:
            lookup[state] = []
        lookup[state].append({
            "zip_code": row["zip_code"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "city": row["city"],
        })

    # Sort each state's zips for deterministic selection
    for state in lookup:
        lookup[state].sort(key=lambda x: x["zip_code"])

    print(f"  Built lookup for {len(lookup)} US states")
    return lookup


if __name__ == "__main__":
    # Test download
    zcta_df = download_zcta_data()
    print(zcta_df.head())
    lookup = build_zip_lookup(zcta_df)
    print(f"CA has {len(lookup.get('CA', []))} zip codes")
```

- [ ] **Step 2: Run script to verify download works**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python scripts/transform_to_us_geography.py`

Expected:
```
Downloading US Census ZCTA data...
  Downloaded ~33,000 zip codes
  Built lookup for ~50 US states
CA has ~2,000+ zip codes
```

- [ ] **Step 3: Commit**

```bash
cd C:\dev\portfolios\ecommerce-retail-analytics
git add scripts/transform_to_us_geography.py
git commit -m "feat: add transformation script with mapping tables and ZCTA download"
```

---

### Task 3: Add city name enrichment from supplemental data

**Files:**
- Modify: `scripts/transform_to_us_geography.py`

**Interfaces:**
- Consumes: `download_zcta_data()`, `build_zip_lookup()`
- Produces:
  - `enrich_cities_from_free_zipcode_data(lookup: dict) -> dict` - Adds city names to zip lookup
  - Updated `build_zip_lookup()` that includes city names

The Census ZCTA file lacks city names. We'll use a supplemental free zip code database to add them.

- [ ] **Step 1: Add supplemental zip code data source**

Add these constants after ZCTA_URL in `scripts/transform_to_us_geography.py`:

```python
# Supplemental zip code data with city names (free, public domain)
# Source: https://simplemaps.com/data/us-zips (free version)
SIMPLEMAPS_URL = "https://simplemaps.com/static/data/us-zips/1.82/basic/simplemaps_uszips_basicv1.82.zip"
```

- [ ] **Step 2: Add function to download and merge city data**

Add this function after `build_zip_lookup()`:

```python
def download_city_data() -> dict[str, str]:
    """Download zip-to-city mapping from SimpleMaps.

    Returns:
        Dict mapping zip code string to city name
    """
    print("Downloading city name data...")
    response = requests.get(SIMPLEMAPS_URL, timeout=60)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        csv_files = [f for f in zf.namelist() if f.endswith(".csv")]
        if not csv_files:
            raise ValueError("No .csv file found in SimpleMaps zip archive")

        with zf.open(csv_files[0]) as f:
            df = pd.read_csv(f, dtype={"zip": str})

    # Create zip -> city mapping
    zip_to_city = dict(zip(df["zip"].str.zfill(5), df["city"]))
    print(f"  Downloaded {len(zip_to_city):,} zip-to-city mappings")

    return zip_to_city


def enrich_zip_lookup_with_cities(
    lookup: dict[str, list[dict]],
    zip_to_city: dict[str, str]
) -> dict[str, list[dict]]:
    """Add city names to zip lookup using SimpleMaps data.

    Args:
        lookup: Dict from build_zip_lookup()
        zip_to_city: Dict from download_city_data()

    Returns:
        Updated lookup with city names populated
    """
    enriched = 0
    for state_zips in lookup.values():
        for zip_info in state_zips:
            zip_code = zip_info["zip_code"].zfill(5)
            if zip_code in zip_to_city:
                zip_info["city"] = zip_to_city[zip_code]
                enriched += 1

    print(f"  Enriched {enriched:,} zip codes with city names")
    return lookup
```

- [ ] **Step 3: Update main block to test enrichment**

Replace the `if __name__ == "__main__":` block:

```python
if __name__ == "__main__":
    # Test download and enrichment
    zcta_df = download_zcta_data()
    lookup = build_zip_lookup(zcta_df)

    zip_to_city = download_city_data()
    lookup = enrich_zip_lookup_with_cities(lookup, zip_to_city)

    # Show sample from California
    ca_zips = lookup.get("CA", [])[:5]
    print("\nSample CA zip codes:")
    for z in ca_zips:
        print(f"  {z['zip_code']}: {z['city']}, CA ({z['latitude']}, {z['longitude']})")
```

- [ ] **Step 4: Run script to verify city enrichment**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python scripts/transform_to_us_geography.py`

Expected:
```
Downloading US Census ZCTA data...
  Downloaded ~33,000 zip codes
  Built lookup for ~50 US states
Downloading city name data...
  Downloaded ~33,000 zip-to-city mappings
  Enriched ~33,000 zip codes with city names

Sample CA zip codes:
  90001: Los Angeles, CA (33.97, -118.25)
  ...
```

- [ ] **Step 5: Commit**

```bash
cd C:\dev\portfolios\ecommerce-retail-analytics
git add scripts/transform_to_us_geography.py
git commit -m "feat: add city name enrichment from SimpleMaps data"
```

---

### Task 4: Add deterministic zip code mapping function

**Files:**
- Modify: `scripts/transform_to_us_geography.py`

**Interfaces:**
- Consumes: `STATE_MAPPING`, `CITY_MAPPING`, zip lookup dict
- Produces:
  - `create_zip_mapping(br_geolocation_df: pd.DataFrame, us_zip_lookup: dict) -> dict[str, dict]`
    - Returns: Dict mapping BR zip code → {us_zip, us_city, us_state, us_lat, us_lng}

- [ ] **Step 1: Add deterministic zip selection function**

Add after `enrich_zip_lookup_with_cities()`:

```python
def deterministic_choice(items: list, seed_string: str) -> any:
    """Select an item deterministically based on a seed string.

    Uses MD5 hash of the seed to pick an index, ensuring the same
    seed always returns the same item.

    Args:
        items: List to select from
        seed_string: String to hash for deterministic selection

    Returns:
        Selected item from the list
    """
    if not items:
        raise ValueError("Cannot select from empty list")

    # Hash the seed and use it to pick an index
    hash_bytes = hashlib.md5(seed_string.encode()).digest()
    hash_int = int.from_bytes(hash_bytes[:8], byteorder="big")
    index = hash_int % len(items)

    return items[index]


def normalize_city_name(city: str) -> str:
    """Normalize Brazilian city name for matching.

    Handles accents and common variations.
    """
    import unicodedata

    # Remove accents
    normalized = unicodedata.normalize("NFKD", city)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))

    # Lowercase and strip
    return normalized.lower().strip()


def create_zip_mapping(
    br_geolocation_df: pd.DataFrame,
    us_zip_lookup: dict[str, list[dict]],
) -> dict[str, dict]:
    """Create deterministic mapping from Brazilian zips to US zips.

    Args:
        br_geolocation_df: DataFrame with Brazilian geolocation data
        us_zip_lookup: Dict from build_zip_lookup() with city enrichment

    Returns:
        Dict mapping BR zip code string → {
            us_zip: str,
            us_city: str,
            us_state: str,
            us_lat: float,
            us_lng: float
        }
    """
    # Get unique BR zip codes with their city/state
    unique_zips = (
        br_geolocation_df
        .groupby("geolocation_zip_code_prefix")
        .agg({
            "geolocation_city": "first",
            "geolocation_state": "first",
        })
        .reset_index()
    )

    # Build city-to-zips lookup for mapped metros
    city_zips: dict[tuple[str, str], list[dict]] = {}
    for us_state, zips in us_zip_lookup.items():
        for zip_info in zips:
            city_key = (zip_info["city"], us_state)
            if city_key not in city_zips:
                city_zips[city_key] = []
            city_zips[city_key].append(zip_info)

    mapping: dict[str, dict] = {}
    mapped_to_city = 0
    mapped_to_state = 0

    for _, row in unique_zips.iterrows():
        br_zip = str(row["geolocation_zip_code_prefix"]).zfill(5)
        br_city = normalize_city_name(str(row["geolocation_city"]))
        br_state = str(row["geolocation_state"]).upper()

        # Get mapped US state
        us_state = STATE_MAPPING.get(br_state)
        if not us_state:
            print(f"  Warning: No state mapping for {br_state}, skipping {br_zip}")
            continue

        # Check if this is a mapped city
        city_key = (br_city, br_state)
        if city_key in CITY_MAPPING:
            us_city, us_state_from_city = CITY_MAPPING[city_key]
            # Get zips for this US city
            us_city_key = (us_city, us_state_from_city)
            available_zips = city_zips.get(us_city_key, [])

            if available_zips:
                selected = deterministic_choice(available_zips, br_zip)
                mapping[br_zip] = {
                    "us_zip": selected["zip_code"],
                    "us_city": us_city,
                    "us_state": us_state_from_city,
                    "us_lat": selected["latitude"],
                    "us_lng": selected["longitude"],
                }
                mapped_to_city += 1
                continue

        # Fall back to random zip from mapped state
        state_zips = us_zip_lookup.get(us_state, [])
        if not state_zips:
            print(f"  Warning: No zips for state {us_state}, skipping {br_zip}")
            continue

        selected = deterministic_choice(state_zips, br_zip)
        mapping[br_zip] = {
            "us_zip": selected["zip_code"],
            "us_city": selected["city"],
            "us_state": us_state,
            "us_lat": selected["latitude"],
            "us_lng": selected["longitude"],
        }
        mapped_to_state += 1

    print(f"  Mapped {mapped_to_city:,} zips to specific cities")
    print(f"  Mapped {mapped_to_state:,} zips to state-level random selection")
    print(f"  Total: {len(mapping):,} zip mappings created")

    return mapping
```

- [ ] **Step 2: Update main block to test mapping**

Replace the `if __name__ == "__main__":` block:

```python
if __name__ == "__main__":
    # Download US data
    zcta_df = download_zcta_data()
    lookup = build_zip_lookup(zcta_df)
    zip_to_city = download_city_data()
    lookup = enrich_zip_lookup_with_cities(lookup, zip_to_city)

    # Load Brazilian geolocation
    br_geo_path = DATA_RAW_DIR / "olist_geolocation_dataset.csv"
    br_geo_df = pd.read_csv(br_geo_path, dtype={"geolocation_zip_code_prefix": str})
    print(f"\nLoaded {len(br_geo_df):,} Brazilian geolocation records")

    # Create mapping
    print("\nCreating zip code mapping...")
    zip_mapping = create_zip_mapping(br_geo_df, lookup)

    # Show sample mappings
    print("\nSample mappings:")
    for br_zip, us_info in list(zip_mapping.items())[:5]:
        print(f"  {br_zip} -> {us_info['us_zip']} ({us_info['us_city']}, {us_info['us_state']})")
```

- [ ] **Step 3: Run script to verify mapping**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python scripts/transform_to_us_geography.py`

Expected:
```
Downloading US Census ZCTA data...
...
Loaded 1,000,163 Brazilian geolocation records

Creating zip code mapping...
  Mapped X zips to specific cities
  Mapped Y zips to state-level random selection
  Total: ~19,000 zip mappings created

Sample mappings:
  01037 -> 90001 (Los Angeles, CA)
  ...
```

- [ ] **Step 4: Commit**

```bash
cd C:\dev\portfolios\ecommerce-retail-analytics
git add scripts/transform_to_us_geography.py
git commit -m "feat: add deterministic zip code mapping function"
```

---

### Task 5: Add dataset transformation and CSV output functions

**Files:**
- Modify: `scripts/transform_to_us_geography.py`

**Interfaces:**
- Consumes: `zip_mapping: dict[str, dict]` from `create_zip_mapping()`
- Produces:
  - `transform_geolocation(br_df: pd.DataFrame, zip_mapping: dict) -> pd.DataFrame`
  - `transform_customers(br_df: pd.DataFrame, zip_mapping: dict) -> pd.DataFrame`
  - `transform_sellers(br_df: pd.DataFrame, zip_mapping: dict) -> pd.DataFrame`
  - `main()` - Full pipeline that writes output CSVs

- [ ] **Step 1: Add transformation functions**

Add after `create_zip_mapping()`:

```python
def transform_geolocation(
    br_df: pd.DataFrame,
    zip_mapping: dict[str, dict],
) -> pd.DataFrame:
    """Transform Brazilian geolocation to US geography.

    Note: Output may have fewer rows than input because we deduplicate
    to one row per zip code (original has multiple lat/lng per zip).

    Args:
        br_df: Brazilian geolocation DataFrame
        zip_mapping: Dict from create_zip_mapping()

    Returns:
        US geolocation DataFrame with same schema as input
    """
    rows = []
    seen_zips = set()

    for br_zip, us_info in zip_mapping.items():
        if br_zip in seen_zips:
            continue
        seen_zips.add(br_zip)

        rows.append({
            "geolocation_zip_code_prefix": us_info["us_zip"],
            "geolocation_lat": us_info["us_lat"],
            "geolocation_lng": us_info["us_lng"],
            "geolocation_city": us_info["us_city"],
            "geolocation_state": us_info["us_state"],
        })

    us_df = pd.DataFrame(rows)
    print(f"  Geolocation: {len(us_df):,} unique zip codes")
    return us_df


def transform_customers(
    br_df: pd.DataFrame,
    zip_mapping: dict[str, dict],
) -> pd.DataFrame:
    """Transform Brazilian customers to US geography.

    Preserves all customer IDs, only changes location fields.

    Args:
        br_df: Brazilian customers DataFrame
        zip_mapping: Dict from create_zip_mapping()

    Returns:
        US customers DataFrame with same schema as input
    """
    us_df = br_df.copy()

    # Normalize BR zip codes for lookup
    us_df["_br_zip"] = us_df["customer_zip_code_prefix"].astype(str).str.zfill(5)

    # Map to US values
    us_df["customer_zip_code_prefix"] = us_df["_br_zip"].map(
        lambda z: zip_mapping.get(z, {}).get("us_zip", z)
    )
    us_df["customer_city"] = us_df["_br_zip"].map(
        lambda z: zip_mapping.get(z, {}).get("us_city", "Unknown")
    )
    us_df["customer_state"] = us_df["_br_zip"].map(
        lambda z: zip_mapping.get(z, {}).get("us_state", "XX")
    )

    # Drop temp column
    us_df = us_df.drop(columns=["_br_zip"])

    # Count unmapped
    unmapped = us_df["customer_state"].eq("XX").sum()
    if unmapped > 0:
        print(f"  Warning: {unmapped} customers with unmapped zip codes")

    print(f"  Customers: {len(us_df):,} records transformed")
    return us_df


def transform_sellers(
    br_df: pd.DataFrame,
    zip_mapping: dict[str, dict],
) -> pd.DataFrame:
    """Transform Brazilian sellers to US geography.

    Preserves seller IDs, only changes location fields.

    Args:
        br_df: Brazilian sellers DataFrame
        zip_mapping: Dict from create_zip_mapping()

    Returns:
        US sellers DataFrame with same schema as input
    """
    us_df = br_df.copy()

    # Normalize BR zip codes for lookup
    us_df["_br_zip"] = us_df["seller_zip_code_prefix"].astype(str).str.zfill(5)

    # Map to US values
    us_df["seller_zip_code_prefix"] = us_df["_br_zip"].map(
        lambda z: zip_mapping.get(z, {}).get("us_zip", z)
    )
    us_df["seller_city"] = us_df["_br_zip"].map(
        lambda z: zip_mapping.get(z, {}).get("us_city", "Unknown")
    )
    us_df["seller_state"] = us_df["_br_zip"].map(
        lambda z: zip_mapping.get(z, {}).get("us_state", "XX")
    )

    # Drop temp column
    us_df = us_df.drop(columns=["_br_zip"])

    # Count unmapped
    unmapped = us_df["seller_state"].eq("XX").sum()
    if unmapped > 0:
        print(f"  Warning: {unmapped} sellers with unmapped zip codes")

    print(f"  Sellers: {len(us_df):,} records transformed")
    return us_df
```

- [ ] **Step 2: Add main function with full pipeline**

Replace the `if __name__ == "__main__":` block with a proper `main()` function:

```python
def main():
    """Run the full transformation pipeline."""
    print("=" * 60)
    print("US Geography Transformation")
    print("=" * 60)

    # Step 1: Download US reference data
    print("\n[1/5] Downloading US Census ZCTA data...")
    zcta_df = download_zcta_data()
    lookup = build_zip_lookup(zcta_df)

    print("\n[2/5] Downloading city name data...")
    zip_to_city = download_city_data()
    lookup = enrich_zip_lookup_with_cities(lookup, zip_to_city)

    # Step 2: Load Brazilian source data
    print("\n[3/5] Loading Brazilian source data...")
    br_geo_df = pd.read_csv(
        DATA_RAW_DIR / "olist_geolocation_dataset.csv",
        dtype={"geolocation_zip_code_prefix": str},
    )
    br_customers_df = pd.read_csv(
        DATA_RAW_DIR / "olist_customers_dataset.csv",
        dtype={"customer_zip_code_prefix": str},
    )
    br_sellers_df = pd.read_csv(
        DATA_RAW_DIR / "olist_sellers_dataset.csv",
        dtype={"seller_zip_code_prefix": str},
    )
    print(f"  Geolocation: {len(br_geo_df):,} records")
    print(f"  Customers: {len(br_customers_df):,} records")
    print(f"  Sellers: {len(br_sellers_df):,} records")

    # Step 3: Create zip mapping
    print("\n[4/5] Creating zip code mapping...")
    zip_mapping = create_zip_mapping(br_geo_df, lookup)

    # Step 4: Transform datasets
    print("\n[5/5] Transforming datasets...")
    us_geo_df = transform_geolocation(br_geo_df, zip_mapping)
    us_customers_df = transform_customers(br_customers_df, zip_mapping)
    us_sellers_df = transform_sellers(br_sellers_df, zip_mapping)

    # Step 5: Write output files
    print("\nWriting output files...")
    us_geo_df.to_csv(DATA_RAW_DIR / "us_geolocation_dataset.csv", index=False)
    us_customers_df.to_csv(DATA_RAW_DIR / "us_customers_dataset.csv", index=False)
    us_sellers_df.to_csv(DATA_RAW_DIR / "us_sellers_dataset.csv", index=False)

    print(f"  Written: us_geolocation_dataset.csv ({len(us_geo_df):,} rows)")
    print(f"  Written: us_customers_dataset.csv ({len(us_customers_df):,} rows)")
    print(f"  Written: us_sellers_dataset.csv ({len(us_sellers_df):,} rows)")

    # Validation summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"  Customer rows match: {len(us_customers_df) == len(br_customers_df)}")
    print(f"  Seller rows match: {len(us_sellers_df) == len(br_sellers_df)}")

    # Check coordinate bounds (continental US)
    lat_valid = us_geo_df["geolocation_lat"].between(24, 50).all()
    lng_valid = us_geo_df["geolocation_lng"].between(-125, -66).all()
    print(f"  Latitude in bounds (24-50): {lat_valid}")
    print(f"  Longitude in bounds (-125 to -66): {lng_valid}")

    print("\nTransformation complete!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run full transformation**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python scripts/transform_to_us_geography.py`

Expected:
```
============================================================
US Geography Transformation
============================================================

[1/5] Downloading US Census ZCTA data...
...
[5/5] Transforming datasets...
  Geolocation: ~19,000 unique zip codes
  Customers: 99,441 records transformed
  Sellers: 3,095 records transformed

Writing output files...
  Written: us_geolocation_dataset.csv
  Written: us_customers_dataset.csv
  Written: us_sellers_dataset.csv

============================================================
Validation Summary
============================================================
  Customer rows match: True
  Seller rows match: True
  Latitude in bounds (24-50): True
  Longitude in bounds (-125 to -66): True

Transformation complete!
```

- [ ] **Step 4: Verify output files exist**

Run: `ls -la C:\dev\portfolios\ecommerce-retail-analytics\data\raw\us_*.csv`

Expected: Three new CSV files with reasonable sizes

- [ ] **Step 5: Commit**

```bash
cd C:\dev\portfolios\ecommerce-retail-analytics
git add scripts/transform_to_us_geography.py
git commit -m "feat: add dataset transformation and CSV output"
```

---

### Task 6: Update load_to_snowflake.py to use US files

**Files:**
- Modify: `scripts/load_to_snowflake.py:25-35`

**Interfaces:**
- Consumes: US CSV files in `data/raw/`
- Produces: Updated Snowflake tables with US data

- [ ] **Step 1: Update TABLE_MAPPING to use US files**

Edit `scripts/load_to_snowflake.py` to change the mapping for the three geography files:

```python
# CSV file to table name mapping
TABLE_MAPPING = {
    "olist_orders_dataset.csv": "orders",
    "us_customers_dataset.csv": "customers",  # Changed from olist_customers_dataset.csv
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "us_sellers_dataset.csv": "sellers",  # Changed from olist_sellers_dataset.csv
    "us_geolocation_dataset.csv": "geolocation",  # Changed from olist_geolocation_dataset.csv
    "product_category_name_translation.csv": "product_category_translation",
}
```

- [ ] **Step 2: Verify the load script finds the US files**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python -c "from scripts.load_to_snowflake import TABLE_MAPPING, DATA_RAW_DIR; print([f for f in TABLE_MAPPING.keys() if not (DATA_RAW_DIR / f).exists()])"`

Expected: Empty list `[]` (all files exist)

- [ ] **Step 3: Commit**

```bash
cd C:\dev\portfolios\ecommerce-retail-analytics
git add scripts/load_to_snowflake.py
git commit -m "feat: update Snowflake loader to use US geography files"
```

---

### Task 7: Run end-to-end validation

**Files:**
- None (validation only)

**Interfaces:**
- Consumes: All previous task outputs
- Produces: Validation report confirming data integrity

- [ ] **Step 1: Reload data to Snowflake (if connected)**

If you have Snowflake credentials configured:

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python scripts/load_to_snowflake.py`

Expected: All tables loaded successfully with US data

If Snowflake is not available, skip to Step 2.

- [ ] **Step 2: Verify CSV data integrity**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics && uv run python -c "
import pandas as pd
from pathlib import Path

data_dir = Path('data/raw')

# Load US files
us_geo = pd.read_csv(data_dir / 'us_geolocation_dataset.csv')
us_cust = pd.read_csv(data_dir / 'us_customers_dataset.csv')
us_sell = pd.read_csv(data_dir / 'us_sellers_dataset.csv')

# Load BR files for comparison
br_cust = pd.read_csv(data_dir / 'olist_customers_dataset.csv')
br_sell = pd.read_csv(data_dir / 'olist_sellers_dataset.csv')

print('Row count validation:')
print(f'  Customers: US={len(us_cust):,} BR={len(br_cust):,} Match={len(us_cust)==len(br_cust)}')
print(f'  Sellers: US={len(us_sell):,} BR={len(br_sell):,} Match={len(us_sell)==len(br_sell)}')

print('\nID preservation:')
print(f'  Customer IDs match: {(us_cust[\"customer_id\"] == br_cust[\"customer_id\"]).all()}')
print(f'  Seller IDs match: {(us_sell[\"seller_id\"] == br_sell[\"seller_id\"]).all()}')

print('\nCoordinate bounds:')
print(f'  Lat min/max: {us_geo[\"geolocation_lat\"].min():.2f} / {us_geo[\"geolocation_lat\"].max():.2f}')
print(f'  Lng min/max: {us_geo[\"geolocation_lng\"].min():.2f} / {us_geo[\"geolocation_lng\"].max():.2f}')

print('\nState distribution (top 5):')
print(us_cust['customer_state'].value_counts().head())
"
```

Expected:
```
Row count validation:
  Customers: US=99,441 BR=99,441 Match=True
  Sellers: US=3,095 BR=3,095 Match=True

ID preservation:
  Customer IDs match: True
  Seller IDs match: True

Coordinate bounds:
  Lat min/max: ~25-49
  Lng min/max: ~-124 to -70

State distribution (top 5):
CA    ~42,000
NY    ~13,000
TX    ~12,000
...
```

- [ ] **Step 3: Run dbt tests (if Snowflake data is loaded)**

Run: `cd C:\dev\portfolios\ecommerce-retail-analytics\dbt && dbt test --select staging.*`

Expected: All staging tests pass

- [ ] **Step 4: Commit validation results**

```bash
cd C:\dev\portfolios\ecommerce-retail-analytics
git add -A
git commit -m "chore: complete US geography transformation

- Transformed 99,441 customers to US geography
- Transformed 3,095 sellers to US geography
- Created ~19,000 unique US zip codes with coordinates
- State distribution mirrors original Brazilian distribution
- All IDs preserved, only location fields changed"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: All requirements from design doc are addressed
  - Portfolio presentation: US state/city names ✓
  - Map accuracy: Census ZCTA coordinates ✓
  - Preserve distribution: STATE_MAPPING mirrors BR percentages ✓
  - Referential integrity: Same zip_mapping used for all 3 files ✓
  - Reproducible: hash-based deterministic_choice() ✓

- [x] **Placeholder scan**: No TBD/TODO found

- [x] **Type consistency**: All function signatures match usage
  - `zip_mapping: dict[str, dict]` used consistently
  - `us_zip_lookup: dict[str, list[dict]]` used consistently
