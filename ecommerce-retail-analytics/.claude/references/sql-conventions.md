# SQL Conventions

## General Style

- **Lowercase** for SQL keywords (select, from, where)
- **snake_case** for column and table names
- **4 spaces** for indentation (no tabs)
- **Trailing commas** in SELECT lists
- **One column per line** in SELECT

## CTE Pattern

Always use CTEs, never nested subqueries:

```sql
with source as (
    select * from {{ ref('upstream_model') }}
),

transformed as (
    select
        column_a,
        column_b,
        column_a + column_b as column_c
    from source
),

final as (
    select
        column_a,
        column_b,
        column_c
    from transformed
)

select * from final
```

## SELECT Formatting

```sql
select
    -- Keys first
    order_id,
    customer_id,

    -- Dimensions
    order_date,
    status,

    -- Measures
    total_amount,
    item_count,

    -- Calculations
    total_amount / nullif(item_count, 0) as avg_item_price,

    -- Metadata last
    current_timestamp() as created_at,
    current_timestamp() as updated_at

from source
```

## JOIN Formatting

```sql
from orders o
left join customers c
    on o.customer_id = c.customer_id
    and o.order_date >= c.effective_date
inner join products p
    on o.product_id = p.product_id
```

- Explicit join type (never just `JOIN`)
- Table aliases for readability
- Join conditions on separate lines if multiple

## CASE Statements

```sql
case
    when status = 'delivered' then 'Complete'
    when status = 'shipped' then 'In Transit'
    when status in ('pending', 'processing') then 'Pending'
    else 'Unknown'
end as status_category
```

## Window Functions

```sql
-- Simple window
row_number() over (partition by customer_id order by order_date desc) as order_rank

-- Named window (when reused)
sum(amount) over customer_window as customer_total,
avg(amount) over customer_window as customer_avg

-- Window definition
window customer_window as (partition by customer_id)
```

## NULL Handling

```sql
-- Division safety
total / nullif(count, 0) as average

-- Default values
coalesce(category, 'Unknown') as category

-- NULL checks
case when value is null then 'Missing' else 'Present' end as value_status
```

## Type Casting

```sql
-- Explicit casting
column_name::date as order_date
column_name::timestamp as created_at
column_name::numeric(10,2) as amount
column_name::varchar as code
column_name::int as quantity
```

## String Cleaning (Staging)

```sql
-- Standard cleaning pattern
trim(column_name) as column_name,
initcap(trim(city)) as city,
upper(trim(state)) as state,
lpad(zip_code::varchar, 5, '0') as zip_code
```

## Date Functions

```sql
-- Truncation
date_trunc('month', order_date) as order_month

-- Differences
datediff('day', start_date, end_date) as days_between

-- Extraction
extract(year from order_date) as order_year

-- Current
current_date() as today,
current_timestamp() as now
```

## Aggregations

```sql
select
    customer_id,
    count(*) as order_count,
    count(distinct product_id) as unique_products,
    sum(amount) as total_amount,
    avg(amount) as avg_amount,
    min(order_date) as first_order,
    max(order_date) as last_order
from orders
group by customer_id
```

## Deduplication

```sql
-- Using QUALIFY (Snowflake)
select *
from source
qualify row_number() over (
    partition by id
    order by updated_at desc
) = 1

-- Using CTE
with ranked as (
    select
        *,
        row_number() over (
            partition by id
            order by updated_at desc
        ) as rn
    from source
)
select * from ranked where rn = 1
```

## Commenting

```sql
-- Model header
-- Customer Lifetime Value fact table
-- Grain: one row per customer
-- Updates: daily full refresh

-- Section comments
-- === Metrics Calculation ===

-- Inline explanations (sparingly)
total * 1.1 as total_with_tax  -- 10% tax rate
```

## Anti-Patterns to Avoid

| Don't | Do |
|-------|-----|
| `SELECT *` in final select | List columns explicitly |
| Nested subqueries | Use CTEs |
| `USING` in joins | Use explicit `ON` |
| Implicit type conversion | Cast explicitly |
| `BETWEEN` for dates | Use `>=` and `<` |
| `!=` for NULL checks | Use `IS NOT NULL` |
