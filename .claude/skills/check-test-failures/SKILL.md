---
name: check-test-failures
description: Diagnose production test failures by querying Snowflake
allowed-tools: Read Bash Glob Grep
---

# /check-test-failures - Diagnose Production Failures

## Purpose
Investigate and diagnose test failures in production, identify root causes, and suggest fixes.

## Prerequisites
- Load `references/data-warehouse.md`
- Access to production database (`ECOMMERCE_RETAIL_DB_PROD`)

## Procedure

### Step 1: Identify Failed Tests

Check recent CI/CD runs:

```bash
# View recent workflow runs
gh run list --workflow=dbt-cd.yml --limit=5

# View details of a specific run
gh run view <run-id>

# View failed job logs
gh run view <run-id> --log-failed
```

Or check dbt artifacts:

```bash
cd dbt
source ../.env 2>/dev/null || export $(grep -v '^#' ../.env | xargs)
uv run dbt test --target prod --store-failures
```

### Step 2: Categorize the Failure

| Failure Type | Symptoms | Common Causes |
|--------------|----------|---------------|
| `unique` | Duplicate keys | Source data changed, join fanout |
| `not_null` | NULL values | Missing data, failed transformation |
| `relationships` | Orphaned FKs | Timing issues, deleted parents |
| `accepted_values` | Unexpected values | New categories, data entry errors |
| `expression_is_true` | Business rule violation | Logic error, edge cases |

### Step 3: Investigate Root Cause

Use dbt show to query and investigate:

```bash
# For unique failures - find duplicates
uv run dbt show --inline "SELECT <key_column>, COUNT(*) as cnt FROM {{ ref('<model>') }} GROUP BY 1 HAVING COUNT(*) > 1 ORDER BY cnt DESC LIMIT 20"

# For not_null failures - find nulls
uv run dbt show --inline "SELECT * FROM {{ ref('<model>') }} WHERE <column> IS NULL LIMIT 20"

# For relationships failures - find orphans
uv run dbt show --inline "SELECT DISTINCT child.<fk> FROM {{ ref('<child>') }} child LEFT JOIN {{ ref('<parent>') }} parent ON child.<fk> = parent.<pk> WHERE parent.<pk> IS NULL LIMIT 20"
```

### Step 4: Determine Fix Strategy

| Root Cause | Fix Strategy |
|------------|--------------|
| **Source data issue** | Add data quality test on source, notify upstream |
| **Missing edge case** | Add COALESCE, handle NULL, add CASE WHEN |
| **Join fanout** | Add DISTINCT or aggregate before join |
| **New category values** | Update accepted_values list or transform |
| **Timing/race condition** | Add incremental logic, check run order |
| **Logic error** | Fix transformation logic, add regression test |

### Step 5: Implement Fix

1. **Create fix branch:**
   ```bash
   git checkout -b fix/<issue-description>
   ```

2. **Make minimal changes** - Fix only what's broken

3. **Add regression test** - Prevent recurrence

4. **Test locally:**
   ```bash
   uv run dbt build --select <model_name>
   ```

5. **Deploy via `/deploy`**

### Step 6: Document Incident

Create incident report with timeline, impact, root cause, resolution, and prevention steps.

## Output Checklist

- [ ] Failed test identified
- [ ] Root cause determined
- [ ] Fix implemented
- [ ] Regression test added
- [ ] Incident documented
- [ ] Deployed via PR
