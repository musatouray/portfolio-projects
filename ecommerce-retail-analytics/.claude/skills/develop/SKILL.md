---
name: develop
description: Scaffold new dbt models (staging, intermediate, or marts) with SQL and YAML following project conventions
allowed-tools: Read Write Edit Bash Glob Grep
---

# /develop - Scaffold New Models

## Purpose
Create new dbt models following project conventions, including SQL logic and YAML documentation.

## Prerequisites
- Load `references/dbt-conventions.md`
- Load `references/sql-conventions.md`
- Load `references/yaml-conventions.md`

## Procedure

### Step 1: Gather Requirements
Ask the user:
1. **Model type**: staging | intermediate | mart (dim/fct)
2. **Model name**: What should it be called?
3. **Business purpose**: What question does this answer?
4. **Source/upstream**: What models or sources does it depend on?
5. **Grain**: What is one row in this table?

### Step 2: Determine File Locations

| Type | SQL Location | YAML Location |
|------|--------------|---------------|
| Staging | `models/staging/stg_ecommerce__<name>.sql` | `models/staging/_stg_ecommerce_models.yml` |
| Intermediate | `models/intermediate/int_<name>.sql` | `models/intermediate/_int_models.yml` |
| Dimension | `models/marts/core/dim_<name>.sql` | `models/marts/core/_core_models.yml` |
| Fact | `models/marts/<domain>/fct_<name>.sql` | `models/marts/<domain>/_<domain>_models.yml` |

### Step 3: Scaffold SQL

Follow the CTE pattern:

```sql
-- <Model description in one line>
-- <Additional context if needed>

with source as (
    select * from {{ ref('upstream_model') }}
),

<transformation_ctes> as (
    -- Business logic here
),

final as (
    select
        -- Surrogate key (if fact/dim)
        {{ dbt_utils.generate_surrogate_key(['natural_key']) }} as <model>_key,

        -- Dimension/fact columns
        column_1,
        column_2,

        -- Metadata
        current_timestamp() as created_at,
        current_timestamp() as updated_at
    from <last_cte>
)

select * from final
```

### Step 4: Scaffold YAML

Add to the appropriate `_*_models.yml` file:

```yaml
  - name: <model_name>
    description: >
      <Business description of what this model represents.>
      <What grain is it? What questions does it answer?>
    columns:
      - name: <primary_key>
        description: <What this column represents>
        data_tests:
          - unique
          - not_null

      - name: <column_name>
        description: <What this column represents>
        data_tests:
          - not_null  # if required
          - accepted_values:  # if categorical
              arguments:
                values: [val1, val2, val3]
```

### Step 5: Invoke Code Reviewer (Sub-Agent)

**Code Reviewer Task:**
Review the SQL for:
- [ ] CTE naming clarity
- [ ] Proper use of `ref()` and `source()`
- [ ] Data type consistency
- [ ] Window function correctness
- [ ] Join logic (LEFT vs INNER appropriateness)
- [ ] NULL handling with COALESCE
- [ ] Performance considerations (avoid SELECT *)

### Step 6: Invoke Doc Reviewer (Sub-Agent)

**Doc Reviewer Task:**
Review the YAML for:
- [ ] Model description is business-friendly (not technical jargon)
- [ ] Grain is clearly stated
- [ ] All columns have descriptions
- [ ] Appropriate tests are defined
- [ ] Descriptions are complete sentences

### Step 7: Compile & Validate

```bash
cd dbt
uv run dbt compile --select <model_name>
```

If compilation succeeds, proceed to `/test`.

## Output Checklist

- [ ] SQL file created at correct location
- [ ] YAML documentation added
- [ ] Code review completed
- [ ] Doc review completed
- [ ] Model compiles successfully

## Next Steps
Run `/test` to validate the model builds and passes tests.
