-- =================================================
-- E-COMMERCE RETAIL ANALYTICS
-- 2. Warehouse Setup
-- =================================================
-- Run as: SYSADMIN
-- Purpose: Create compute warehouse 
-- =================================================

USE ROLE SYSADMIN;

-- =================================================
-- WAREHOUSE
-- =================================================

CREATE WAREHOUSE IF NOT EXISTS ECOMMERCE_RETAIL_WH
    WAREHOUSE_SIZE          = 'X-SMALL'
    AUTO_SUSPEND            = 60          -- Suspend after 1 min idle (cost optimization)
    AUTO_RESUME             = TRUE        -- Auto-resume on query
    INITIALLY_SUSPENDED     = TRUE        -- Don't start until first query
    SCALING_POLICY          = 'STANDARD'  -- For multi-cluster (if upgraded)
    COMMENT                 = 'Compute warehouse for E-Commerce Retail dbt transformations';

-- =================================================
-- WAREHOUSE SIZING GUIDE
-- =================================================
-- X-SMALL : Development and testing
-- SMALL   : Light production workloads
-- MEDIUM  : Moderate production workloads
-- LARGE+  : Heavy production / large datasets
--
-- Adjust AUTO_SUSPEND based on workload patterns:
-- 60s  : Interactive development (frequent queries)
-- 300s : Production batch jobs (less frequent)
