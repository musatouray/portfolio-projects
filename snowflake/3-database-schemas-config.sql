-- ============================================================================
-- MEDALLION ARCHITECTURE WITH ENVIRONMENT SEPARATION
-- ============================================================================
--
-- Architecture:
--   ECOMMERCE_RETAIL_DB_DEV  → Bronze + Silver + Gold (Dev)
--   ECOMMERCE_RETAIL_DB_PROD → Gold only (reads from DEV.Silver)
--
-- Medallion Layers:
--   Bronze (RAW)        → Immutable source data
--   Silver (STAGING)    → Cleaned, validated, typed
--   Gold (INT + MARTS)  → Business aggregates, analytics-ready
--
-- Key Design Decisions:
--   1. Bronze + Silver in DEV only (no duplication, cost-efficient)
--   2. Gold layer separated by environment (Dev vs Prod)
--   3. PROD reads from DEV.STAGING via cross-database reference
--   4. Only business logic (Gold) needs environment isolation
--
-- ============================================================================

USE ROLE SYSADMIN;

-- ============================================================================
-- STEP 1: CREATE DEV DATABASE (Bronze + Silver + Gold)
-- ============================================================================
-- This is the landing zone for raw data and the development environment

CREATE DATABASE IF NOT EXISTS ECOMMERCE_RETAIL_DB_DEV
    COMMENT = 'Development: Bronze (RAW) + Silver (STAGING) + Gold (INT/MARTS)';

-- Bronze Layer (Raw, immutable source data)
CREATE SCHEMA IF NOT EXISTS ECOMMERCE_RETAIL_DB_DEV.RAW
    COMMENT = 'Bronze Layer - Raw source data from Kaggle CSV';

-- Silver Layer (Cleaned, validated)
CREATE SCHEMA IF NOT EXISTS ECOMMERCE_RETAIL_DB_DEV.STAGING
    COMMENT = 'Silver Layer - Cleaned and typed data';

-- Gold Layer (Business aggregates - Dev)
CREATE SCHEMA IF NOT EXISTS ECOMMERCE_RETAIL_DB_DEV.INTERMEDIATE
    COMMENT = 'Gold Layer - Joined and enriched models (Dev)';

CREATE SCHEMA IF NOT EXISTS ECOMMERCE_RETAIL_DB_DEV.MARTS
    COMMENT = 'Gold Layer - Fact and dimension tables (Dev)';


-- ============================================================================
-- STEP 2: CREATE PROD DATABASE (Gold Only)
-- ============================================================================
-- Production only contains business-critical analytics tables
-- Reads from DEV.STAGING (Silver layer) via cross-database reference

CREATE DATABASE IF NOT EXISTS ECOMMERCE_RETAIL_DB_PROD
    COMMENT = 'Production: Gold layer only (INT/MARTS) - Dashboards connect here';

-- Gold Layer (Business aggregates - Prod)
CREATE SCHEMA IF NOT EXISTS ECOMMERCE_RETAIL_DB_PROD.INTERMEDIATE
    COMMENT = 'Gold Layer - Joined and enriched models (Prod)';

CREATE SCHEMA IF NOT EXISTS ECOMMERCE_RETAIL_DB_PROD.MARTS
    COMMENT = 'Gold Layer - Fact and dimension tables (Prod) - BI tools connect here';


-- ============================================================================
-- ARCHITECTURE DIAGRAM
-- ============================================================================
--
--  ┌─────────────────────────────────────────────────────────────────────────┐
--  │                    MEDALLION + ENVIRONMENT ARCHITECTURE                 │
--  ├─────────────────────────────────────────────────────────────────────────┤
--  │                                                                          │
--  │   ECOMMERCE_RETAIL_DB_DEV                                               │
--  │   ┌─────────────────────────────────────────────────────────────────┐   │
--  │   │ BRONZE (RAW)          │ Source data lands here                  │   │
--  │   ├───────────────────────┼─────────────────────────────────────────┤   │
--  │   │ SILVER (STAGING)      │ Cleaned views ──────────────────────┐   │   │
--  │   ├───────────────────────┼─────────────────────────────────────│───┤   │
--  │   │ GOLD (INT + MARTS)    │ Dev analytics                       │   │   │
--  │   └───────────────────────┴─────────────────────────────────────│───┘   │
--  │                                                                  │       │
--  │   ECOMMERCE_RETAIL_DB_PROD                                       │       │
--  │   ┌───────────────────────┬─────────────────────────────────────│───┐   │
--  │   │ GOLD (INT + MARTS)    │ Prod analytics  ◄────────────────────┘   │   │
--  │   │                       │ (reads from DEV.STAGING)                 │   │
--  │   └───────────────────────┴──────────────────────────────────────────┘   │
--  │                                                                          │
--  │   ✅ Medallion: Bronze → Silver → Gold                                  │
--  │   ✅ Cost Efficient: No Bronze/Silver duplication                       │
--  │   ✅ Environment Isolation: Dev and Prod separated                      │
--  │                                                                          │
--  └─────────────────────────────────────────────────────────────────────────┘