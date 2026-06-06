# Data Dictionary — AdventureWorksDW2022

This document describes the tables and columns used in the Advanced SQL Patterns project.

## Schema Overview

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   DimProductCategory│◄────│ DimProductSubcategory│◄────│     DimProduct      │
└─────────────────────┘     └─────────────────────┘     └──────────┬──────────┘
                                                                   │
┌─────────────────────┐     ┌─────────────────────┐                │
│      DimCustomer    │◄────│  FactInternetSales  │────────────────┤
└─────────────────────┘     └──────────┬──────────┘                │
                                       │                           │
┌─────────────────────┐                │              ┌────────────┴──────────┐
│  DimSalesTerritory  │◄───────────────┼──────────────│   FactResellerSales   │
└─────────────────────┘                │              └───────────────────────┘
                                       │                           │
┌─────────────────────┐                │              ┌────────────┴──────────┐
│       DimDate       │◄───────────────┴──────────────│      DimEmployee      │
└─────────────────────┘                               └───────────────────────┘
```

## Fact Tables

### FactInternetSales

Online sales transactions (B2C). Primary fact table for customer analytics.

| Column | Type | Description |
|--------|------|-------------|
| `ProductKey` | int | FK to DimProduct |
| `OrderDateKey` | int | FK to DimDate |
| `CustomerKey` | int | FK to DimCustomer |
| `SalesTerritoryKey` | int | FK to DimSalesTerritory |
| `SalesOrderNumber` | nvarchar | Unique order identifier |
| `SalesOrderLineNumber` | tinyint | Line item within order |
| `OrderDate` | datetime | Transaction date |
| `SalesAmount` | money | Revenue (price x quantity) |
| `TotalProductCost` | money | Cost of goods sold |

**Used in:** Q1, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12

---

### FactResellerSales

Reseller/distributor sales transactions (B2B). Used for sales rep analysis.

| Column | Type | Description |
|--------|------|-------------|
| `EmployeeKey` | int | FK to DimEmployee (sales rep) |
| `OrderDateKey` | int | FK to DimDate |
| `SalesAmount` | money | Revenue |

**Used in:** Q2

---

## Dimension Tables

### DimDate

Calendar dimension for time-based analysis.

| Column | Type | Description |
|--------|------|-------------|
| `DateKey` | int | PK (YYYYMMDD format) |
| `CalendarYear` | smallint | e.g., 2022 |
| `CalendarQuarter` | tinyint | 1-4 |
| `MonthNumberOfYear` | tinyint | 1-12 |
| `EnglishMonthName` | nvarchar | e.g., "January" |

**Used in:** Q1, Q2, Q4, Q5, Q6, Q7, Q8

---

### DimProduct

Product master data.

| Column | Type | Description |
|--------|------|-------------|
| `ProductKey` | int | PK |
| `EnglishProductName` | nvarchar | Product display name |
| `ProductSubcategoryKey` | int | FK to DimProductSubcategory |

**Used in:** Q1, Q3, Q5, Q8

---

### DimProductSubcategory

Product subcategory hierarchy (bridges Product to Category).

| Column | Type | Description |
|--------|------|-------------|
| `ProductSubcategoryKey` | int | PK |
| `ProductCategoryKey` | int | FK to DimProductCategory |

**Used in:** Q3, Q5

---

### DimProductCategory

Top-level product categorization.

| Column | Type | Description |
|--------|------|-------------|
| `ProductCategoryKey` | int | PK |
| `EnglishProductCategoryName` | nvarchar | e.g., "Bikes", "Accessories" |

**Used in:** Q3, Q5

---

### DimSalesTerritory

Geographic sales regions.

| Column | Type | Description |
|--------|------|-------------|
| `SalesTerritoryKey` | int | PK |
| `SalesTerritoryCountry` | nvarchar | e.g., "United States", "Germany" |
| `SalesTerritoryRegion` | nvarchar | e.g., "Northwest", "Central" |

**Used in:** Q4, Q6, Q10

---

### DimCustomer

Customer master data for B2C sales.

| Column | Type | Description |
|--------|------|-------------|
| `CustomerKey` | int | PK |
| `FirstName` | nvarchar | Customer first name |
| `MiddleName` | nvarchar | Customer middle name (nullable) |
| `LastName` | nvarchar | Customer last name |

**Used in:** Q10

---

### DimEmployee

Employee data including sales representatives.

| Column | Type | Description |
|--------|------|-------------|
| `EmployeeKey` | int | PK |
| `FirstName` | nvarchar | Employee first name |
| `LastName` | nvarchar | Employee last name |
| `SalesPersonFlag` | bit | 1 = sales rep, 0 = other |

**Used in:** Q2

---

## Table Usage by Question

| Question | Fact Table | Dimensions |
|----------|------------|------------|
| Q1: Top Products by Revenue | FactInternetSales | DimDate, DimProduct |
| Q2: Sales Rep Ranking | FactResellerSales | DimDate, DimEmployee |
| Q3: Product Distribution | FactInternetSales | DimProduct, DimProductSubcategory, DimProductCategory |
| Q4: Territory YoY Growth | FactInternetSales | DimDate, DimSalesTerritory |
| Q5: Running Total by Month | FactInternetSales | DimDate, DimProduct, DimProductSubcategory, DimProductCategory |
| Q6: MoM Growth | FactInternetSales | DimDate, DimSalesTerritory |
| Q7: Moving Average | FactInternetSales | DimDate |
| Q8: YTD Sales | FactInternetSales | DimDate, DimProduct |
| Q9: Customer Segmentation | FactInternetSales | - |
| Q10: Predictive CLV | FactInternetSales | DimSalesTerritory, DimCustomer |
| Q11: First vs Last Purchase | FactInternetSales | - |
| Q12: Cohort Retention | FactInternetSales | - |

## Source

Microsoft AdventureWorksDW2022 sample database:
https://learn.microsoft.com/en-us/sql/samples/adventureworks-install-configure
