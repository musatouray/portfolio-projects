-- =================================================
-- E-COMMERCE RETAIL ANALYTICS
-- 1. Roles and Users Setup
-- =================================================
-- Run as: ACCOUNTADMIN
-- Purpose: Create roles and service users 
-- =================================================

USE ROLE ACCOUNTADMIN;

-- =================================================
-- ROLES
-- =================================================

-- Lead Data Engineer: Full access to build and manage the warehouse
CREATE ROLE IF NOT EXISTS LEAD_DATA_ENGINEER_ROLE
    COMMENT = 'Full access role for data engineers managing the E-Commerce data warehouse';

-- BI Read-Only: Analysts and dashboards (SELECT on marts only)
CREATE ROLE IF NOT EXISTS BI_READONLY_ROLE
    COMMENT = 'Read-only access to mart tables for BI tools and analysts';

-- =================================================
-- ROLE HIERARCHY
-- =================================================
-- BI_READONLY_ROLE -> LEAD_DATA_ENGINEER_ROLE -> SYSADMIN
-- This allows data engineers to test BI access and follows least-privilege

GRANT ROLE BI_READONLY_ROLE TO ROLE LEAD_DATA_ENGINEER_ROLE;
GRANT ROLE LEAD_DATA_ENGINEER_ROLE TO ROLE SYSADMIN;

-- =================================================
-- SERVICE USER (for dbt / automation)
-- =================================================
-- Note: Use key-pair authentication, not passwords
-- See INSTALLATION.md for RSA key setup instructions

CREATE USER IF NOT EXISTS DBT_SERVICE_USER
    DEFAULT_ROLE         = LEAD_DATA_ENGINEER_ROLE
    DEFAULT_WAREHOUSE    = ECOMMERCE_RETAIL_WH
    DEFAULT_NAMESPACE    = ECOMMERCE_RETAIL_DB.RAW
    COMMENT              = 'Service account for dbt and automated pipelines';

GRANT ROLE LEAD_DATA_ENGINEER_ROLE TO USER DBT_SERVICE_USER;


