-- =================================================
-- E-COMMERCE RETAIL ANALYTICS
-- Storage Integration Config
-- =================================================

USE ROLE ACCOUNTADMIN;

-- =================================================
-- STORAGE INTEGRATION
-- =================================================
CREATE OR REPLACE STORAGE INTEGRATION s3_ecommerce_integration
    TYPE =                      EXTERNAL_STAGE
    STORAGE_PROVIDER =          'S3'
    ENABLED =                   TRUE
    STORAGE_AWS_ROLE_ARN =      'arn:aws:iam::492751140572:role/snowflake-ecommerce-s3-role'
    STORAGE_ALLOWED_LOCATIONS = ('s3://ecommerce-retail-analytics-raw/');

-- Query S3_INTEGRATION
DESC INTEGRATION s3_ecommerce_integration;

-- Copy the property_values to be used to configure AWS Roles for the Integration:
STORAGE_AWS_IAM_USER_ARN 
STORAGE_AWS_EXTERNAL_ID
