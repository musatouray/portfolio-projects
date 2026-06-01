# YAML Conventions

## File Organization

| File | Location | Purpose |
|------|----------|---------|
| `_sources.yml` | `models/staging/` | Source definitions |
| `_stg_ecommerce_models.yml` | `models/staging/` | Staging model docs |
| `_int_models.yml` | `models/intermediate/` | Intermediate model docs |
| `_<domain>_models.yml` | `models/marts/<domain>/` | Mart model docs |

## Model Documentation

### Basic Structure

```yaml
version: 2

models:
  - name: model_name
    description: >
      Business-friendly description of what this model represents.
      Include the grain (what is one row?) and primary use cases.
    columns:
      - name: column_name
        description: What this column represents
        data_tests:
          - test_name
```

### Description Guidelines

**Model descriptions should include:**
1. What the model represents (business context)
2. The grain (what is one row?)
3. Primary use cases
4. Any important caveats

**Good example:**
```yaml
description: >
  Customer dimension table containing customer attributes, location,
  and behavioral segmentation. Grain is one row per unique customer
  (customer_unique_id). Use this for customer-level analytics and
  joining to fact tables. Includes customers who have never ordered.
```

**Bad example:**
```yaml
description: Customer data from the customers table
```

### Column Descriptions

**Include:**
- What the column represents
- Units (if numeric)
- Valid values (if categorical)
- NULL meaning

**Good examples:**
```yaml
- name: total_revenue
  description: >
    Total payment value across all customer orders in BRL.
    0 for customers with no orders.

- name: churn_status
  description: >
    Customer status based on days since last order:
    Active (0-30 days), Cooling (31-60), At Risk (61-90), Churned (90+).
```

## Test Syntax (dbt-fusion 2.0)

### Column-Level Tests

```yaml
columns:
  - name: order_id
    data_tests:
      - unique
      - not_null

  - name: status
    data_tests:
      - accepted_values:
          arguments:
            values: ['pending', 'shipped', 'delivered', 'canceled']

  - name: customer_id
    data_tests:
      - relationships:
          arguments:
            to: ref('dim_customers')
            field: customer_id
```

### Model-Level Tests

```yaml
models:
  - name: fct_order_items
    data_tests:
      - dbt_utils.unique_combination_of_columns:
          arguments:
            combination_of_columns:
              - order_id
              - order_item_id
```

### Expression Tests

```yaml
data_tests:
  - dbt_utils.expression_is_true:
      arguments:
        expression: "total_amount >= 0"
```

### Configuring Test Severity

```yaml
data_tests:
  - dbt_utils.expression_is_true:
      arguments:
        expression: "delivery_date >= order_date"
      config:
        severity: warn
        warn_if: ">= 1"
        error_if: "> 100"
```

## Source Definitions

```yaml
version: 2

sources:
  - name: raw
    database: ECOMMERCE_RETAIL_DB_DEV
    schema: RAW
    tables:
      - name: orders
        description: Raw orders from Olist e-commerce platform
        columns:
          - name: order_id
            description: Unique order identifier
            data_tests:
              - unique
              - not_null

      - name: customers
        description: Raw customer data
        loaded_at_field: _loaded_at
        freshness:
          warn_after: {count: 24, period: hour}
          error_after: {count: 48, period: hour}
```

## Seeds

```yaml
seeds:
  - name: rfm_segment_definitions
    description: >
      Reference table defining RFM segments with descriptions
      and recommended marketing actions.
    columns:
      - name: rfm_segment
        description: Segment name
        data_tests:
          - unique
          - not_null

      - name: segment_description
        description: Human-readable segment description

      - name: recommended_action
        description: Suggested marketing action
```

## Formatting Rules

1. **2 spaces** for indentation
2. **Lowercase** for all keys
3. **Multi-line descriptions** use `>` for folding
4. **Lists** use `-` with consistent spacing
5. **No trailing spaces**

## Common Mistakes

| Mistake | Correct |
|---------|---------|
| Tests under wrong level | Column tests under column, model tests under model |
| Missing `arguments:` wrapper | Always use `arguments:` for test parameters |
| Incomplete descriptions | Include grain, business context, caveats |
| Hardcoded database names | Use `{{ target.database }}` or sources |
| Missing tests on keys | Always test unique + not_null on PKs |
