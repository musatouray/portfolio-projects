# dbt Conventions

## Project Structure

```
models/
├── staging/           # 1:1 with source tables, cleaning only
├── intermediate/      # Business logic, joins, enrichment
└── marts/             # Final dimensional models
    ├── core/          # Shared dimensions and facts
    ├── customer/      # Customer analytics
    ├── finance/       # Financial analytics
    └── marketing/     # Marketing analytics
```

## Naming Conventions

| Layer | Prefix | Example |
|-------|--------|---------|
| Staging | `stg_<source>__` | `stg_ecommerce__orders` |
| Intermediate | `int_` | `int_orders_enriched` |
| Dimension | `dim_` | `dim_customers` |
| Fact | `fct_` | `fct_orders` |

## Model Organization

### Staging Models
- One model per source table
- Only cleaning transformations (trim, cast, rename)
- No joins, no business logic
- Materialized as views

### Intermediate Models
- Join multiple staging models
- Apply business logic
- Filter invalid records
- Materialized as views or tables

### Mart Models
- Final dimensional models
- Include surrogate keys
- Include audit columns (created_at, updated_at)
- Materialized as tables

## Materialization Guidelines

| Type | Use When |
|------|----------|
| `view` | Lightweight transforms, staging |
| `table` | Final marts, frequently queried |
| `incremental` | Large fact tables, append-only |
| `ephemeral` | One-time intermediate calculations |

## Testing Requirements

| Layer | Required Tests |
|-------|----------------|
| Staging | unique + not_null on PK |
| Intermediate | unique + not_null on grain |
| Marts | unique + not_null on PK, relationships, accepted_values |

## dbt-fusion 2.0 Test Syntax

```yaml
columns:
  - name: order_id
    data_tests:
      - unique
      - not_null
      - relationships:
          arguments:
            to: ref('stg_ecommerce__orders')
            field: order_id
```

**Important:** Model-level tests (like `unique_combination_of_columns`) go under the model, not a column:

```yaml
models:
  - name: my_model
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          arguments:
            combination_of_columns:
              - col1
              - col2
```

## Variables

Define thresholds and parameters in `dbt_project.yml`:

```yaml
vars:
  churn_churned_days: 90
  customer_high_value_threshold: 500
```

Use in models:
```sql
WHERE days_since_order > {{ var('churn_churned_days') }}
```

## Packages Used

| Package | Purpose |
|---------|---------|
| `dbt_utils` | Surrogate keys, date spine, tests |
| `audit_helper` | Data auditing |
| `codegen` | Code generation |

## Schema Naming

This project uses custom `generate_schema_name` macro:
- Models use schema names directly (not appended to target)
- `+schema: staging` → `STAGING` schema
- `+schema: marts` → `MARTS` schema

## Medallion Architecture

| Layer | Database | Schemas |
|-------|----------|---------|
| Bronze + Silver | `_DEV` | RAW, STAGING |
| Gold (Dev) | `_DEV` | INTERMEDIATE, MARTS |
| Gold (Prod) | `_PROD` | INTERMEDIATE, MARTS |
