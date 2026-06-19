# US Geography Transformation Design

**Date:** 2026-06-19
**Status:** Approved
**Purpose:** Transform Brazilian Olist e-commerce data to US geography for portfolio presentation

## Problem Statement

The Olist e-commerce dataset contains Brazilian geography (states, cities, zip codes, coordinates). For a US-focused portfolio, this data should be transformed to US equivalents while preserving the proportional distribution and enabling accurate map visualizations in Power BI using Azure Maps Visual.

## Requirements

1. **Portfolio presentation** - US hiring managers should recognize geography intuitively
2. **Map accuracy** - Coordinates must render correctly on Azure Maps Visual in Power BI
3. **Preserve distribution** - Mirror Brazil's economic concentration patterns (SP→CA dominance)
4. **Maintain referential integrity** - Zip codes must match across all 3 datasets
5. **Reproducible** - Re-running transformation produces identical output

## Approach

**Option C: New US files alongside originals**

Create new US-transformed CSV files while preserving the original Brazilian data for reference. Update dbt sources to point to the new files.

## Data Sources

### Input Files (Brazilian - Preserved)

| File | Rows | Key Columns |
|------|------|-------------|
| `olist_geolocation_dataset.csv` | 1,000,163 | zip_code, lat, lng, city, state |
| `olist_customers_dataset.csv` | 99,441 | customer_id, unique_id, zip_code, city, state |
| `olist_sellers_dataset.csv` | 3,095 | seller_id, zip_code, city, state |

### Reference Data (US)

**US Census ZCTA Gazetteer Files** - Official Census Bureau ZIP Code Tabulation Areas containing ~33,000 US zip codes with centroid coordinates, city names, and state codes.

- **Source URL**: https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_zcta_national.zip
- **Format**: Tab-delimited text file with GEOID (zip), INTPTLAT, INTPTLONG, plus area metrics
- **City/State mapping**: Supplement with USPS ZIP code database or derive from state FIPS codes

### Output Files (US - New)

| File | Schema |
|------|--------|
| `us_geolocation_dataset.csv` | geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state |
| `us_customers_dataset.csv` | customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state |
| `us_sellers_dataset.csv` | seller_id, seller_zip_code_prefix, seller_city, seller_state |

## Mapping Strategy

### State Mapping (27 Brazilian → 27 US States)

Mapped by economic role, population weight, and regional character:

| BR State | % Data | US State | Reasoning |
|----------|--------|----------|-----------|
| SP | 42% | CA | Economic powerhouse, tech hub |
| RJ | 13% | NY | Second city, finance, culture |
| MG | 12% | TX | Large interior, industrial |
| RS | 5.5% | FL | Southern, tourism |
| PR | 5% | IL | Industrial midwest |
| SC | 3.7% | WA | Tech-friendly, quality of life |
| BA | 3.4% | GA | Southern, growing economy |
| DF | 2.1% | DC | Capital district |
| ES | 2% | NJ | Small coastal near major metro |
| GO | 2% | AZ | Interior growth state |
| PE | 1.7% | NC | Regional hub, growing tech |
| CE | 1.3% | TN | Regional center |
| PA | 1% | OR | Natural resources |
| MT | 0.9% | CO | Interior, agriculture |
| MA | 0.8% | AL | Southern, developing |
| MS | 0.6% | NV | Interior, sparse |
| PB | 0.5% | SC | Small southern coastal |
| RN | 0.4% | LA | Coastal southern |
| PI | 0.3% | AR | Interior southern |
| AL | 0.3% | MS | Small southern |
| SE | 0.2% | OK | Small interior |
| TO | 0.1% | KS | Central interior |
| RO | 0.1% | NM | Western interior |
| AM | 0.1% | AK | Remote, natural resources |
| AC | <0.1% | MT | Remote, sparse |
| AP | <0.1% | WY | Sparse, remote |
| RR | <0.1% | VT | Small, remote |

### City Mapping (Top 10 Metros)

Major Brazilian cities map to comparable US metros to preserve urban clustering:

| BR City | BR State | US City | US State |
|---------|----------|---------|----------|
| São Paulo | SP | Los Angeles | CA |
| Rio de Janeiro | RJ | New York City | NY |
| Belo Horizonte | MG | Houston | TX |
| Brasília | DF | Washington | DC |
| Curitiba | PR | Chicago | IL |
| Porto Alegre | RS | Miami | FL |
| Salvador | BA | Atlanta | GA |
| Recife | PE | Charlotte | NC |
| Fortaleza | CE | Nashville | TN |
| Campinas | SP | San Diego | CA |

Cities not in the top-10 list receive random assignment within their mapped US state.

### Zip Code Mapping

For each unique Brazilian zip code:
1. Look up BR state → US state from state mapping
2. Check if city is in top-10 mapping
3. If yes: assign a zip code from that US metro (zip codes sharing the same city name in ZCTA data)
4. If no: assign a random zip code from the mapped US state
5. Use `hash(br_zip)` as random seed for deterministic, reproducible results

**Metro area definition**: For mapped cities (e.g., Los Angeles), select from all zip codes where the ZCTA city name matches exactly. This keeps customers/sellers from "São Paulo" clustered within "Los Angeles" zip codes rather than scattered across all of California.

## Architecture

### File Structure

```
ecommerce-retail-analytics/
├── data/raw/
│   ├── olist_geolocation_dataset.csv    # Original (preserved)
│   ├── olist_customers_dataset.csv      # Original (preserved)
│   ├── olist_sellers_dataset.csv        # Original (preserved)
│   ├── us_geolocation_dataset.csv       # NEW
│   ├── us_customers_dataset.csv         # NEW
│   └── us_sellers_dataset.csv           # NEW
├── scripts/
│   └── transform_to_us_geography.py     # Transformation script
└── dbt/models/staging/
    └── sources.yml                       # Updated to reference us_*.csv
```

### Transformation Pipeline

```
STEP 1: Download US Census ZCTA Data
        └── ~33,000 US zip codes with lat/lng/city/state

STEP 2: Build Mapping Tables
        ├── state_mapping: BR state → US state (27 mappings)
        ├── city_mapping: Top 10 BR cities → US metros
        └── us_zips_by_state: Group US zips by state

STEP 3: Create Deterministic Zip Mapping
        └── For each unique BR zip:
            ├── Map state
            ├── Check city mapping
            └── Assign US zip (seeded by hash(br_zip))

STEP 4: Transform Datasets
        ├── Geolocation: Replace all location fields
        ├── Customers: Replace location fields, keep IDs
        └── Sellers: Replace location fields, keep IDs

STEP 5: Write Output Files
        └── us_geolocation.csv, us_customers.csv, us_sellers.csv
```

## dbt Changes

Update `dbt/models/staging/sources.yml`:

```yaml
# FROM:
- name: geolocation
  path: olist_geolocation_dataset.csv
- name: customers
  path: olist_customers_dataset.csv
- name: sellers
  path: olist_sellers_dataset.csv

# TO:
- name: geolocation
  path: us_geolocation_dataset.csv
- name: customers
  path: us_customers_dataset.csv
- name: sellers
  path: us_sellers_dataset.csv
```

## Validation Criteria

| Check | Criteria |
|-------|----------|
| Row counts preserved | us_customers = 99,441, us_sellers = 3,095 |
| ID integrity | All customer_id and seller_id unchanged |
| Referential integrity | Every zip in customers/sellers exists in geolocation |
| State distribution | US state % matches BR state % |
| Coordinate validity | All lat/lng within continental US (24°-50°N, 66°-125°W) |
| No nulls | No null values in location columns |
| Azure Maps compatibility | Coordinates render correctly on map visual |

## Post-Transformation Verification

1. Run `dbt test` - Existing staging model tests should pass
2. Refresh Power BI semantic model - Verify no load errors
3. Add Azure Maps Visual - Confirm coordinates plot correctly

## Rollback Procedure

To revert to Brazilian data, update `sources.yml` to reference original filenames:

```yaml
path: olist_geolocation_dataset.csv  # Revert from us_geolocation_dataset.csv
```

## Out of Scope

- Modifying other datasets (orders, products, payments, reviews)
- Creating additional geographic analysis visuals
- Changing dbt model logic (staging models work with any country's data)
