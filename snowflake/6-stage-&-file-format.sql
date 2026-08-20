-- =================================================
-- E-COMMERCE RETAIL ANALYTICS
-- Stage & File Format Config
-- =================================================

USE ROLE LEAD_DATA_ENGINEER_ROLE;
USE DATABASE ECOMMERCE_RETAIL_DB_DEV;
USE SCHEMA RAW;

-- =================================================
-- FILE FORMAT
-- =================================================
CREATE OR REPLACE FILE FORMAT csv_format
    TYPE =                          'CSV'
    FIELD_DELIMITER =               ','
    SKIP_HEADER =                   1
    NULL_IF =                       ('NULL', 'null', '')
    EMPTY_FIELD_AS_NULL =           TRUE
    FIELD_OPTIONALLY_ENCLOSED_BY =  '"'; -- handles quoted strings from Faker/pandas

-- =================================================
-- STAGE
-- =================================================  
CREATE OR REPLACE STAGE raw_ecommerce_s3_stage
    STORAGE_INTEGRATION =   s3_ecommerce_integration
    URL =                   's3://ecommerce-retail-analytics-raw/'
    FILE_FORMAT =           csv_format;

-- Verify stage configuration
DESC STAGE raw_ecommerce_s3_stage;
LIST @raw_ecommerce_s3_stage;
