---
name: test
description: Run dbt tests, validate changes, and diagnose failures
allowed-tools: Read Bash Glob Grep
---

# /test - Run Tests & Validate

## Purpose
Validate model changes through dbt tests, spot-checks, and lineage impact analysis.

## Prerequisites
- Model has been created via `/develop` or modified
- Load `references/data-warehouse.md` (for spot-check queries)

## Procedure

### Step 1: Run dbt Build

Build the specific model and its tests:

```bash
cd dbt
source ../.env 2>/dev/null || export $(grep -v '^#' ../.env | xargs)
uv run dbt build --select <model_name>
```

**Expected output:**
- Model creates successfully
- All tests pass

**If tests fail:**
1. Read the error message carefully
2. Check compiled SQL in `target/compiled/`
3. Fix the issue in the model or test
4. Re-run until passing

### Step 2: Run Downstream Impact Analysis

Check what models depend on your changes:

```bash
uv run dbt ls --select <model_name>+
```

Build downstream models to ensure no breakage:

```bash
uv run dbt build --select <model_name>+
```

### Step 3: Spot-Check Data Quality

Run validation queries directly against Snowflake using dbt show:

#### Row Count Sanity Check
```bash
uv run dbt show --inline "SELECT COUNT(*) as row_count FROM {{ ref('<model_name>') }}"
```

#### Duplicate Check
```bash
uv run dbt show --inline "SELECT <grain_columns>, COUNT(*) as cnt FROM {{ ref('<model_name>') }} GROUP BY <grain_columns> HAVING COUNT(*) > 1 LIMIT 10"
```

### Step 4: Compare with Expectations

| Check | Expected | Action if Failed |
|-------|----------|------------------|
| Row count | Within expected range | Investigate filter logic |
| Null keys | 0 for primary keys | Add COALESCE or filter |
| Duplicates | 0 for grain | Fix grain or add dedup |
| Value distribution | Reasonable spread | Check for data issues |

### Step 5: Document Test Results

Create a summary:

```
## Test Results: <model_name>

### dbt Tests
- Total: X
- Passed: X
- Failed: X
- Warnings: X

### Spot Checks
- Row count: X (expected: ~Y)
- Null keys: X (expected: 0)
- Duplicates: X (expected: 0)

### Downstream Impact
- Models affected: X
- All downstream builds: Passed / Failed

### Ready for Deploy: Yes / No
```

## Troubleshooting Common Failures

### `unique` test fails
**Fix:** Add `QUALIFY ROW_NUMBER() = 1` or fix upstream data.

### `not_null` test fails
**Fix:** Add `COALESCE()` or fix upstream data.

### `relationships` test fails
**Fix:** Add LEFT JOIN handling or fix data integrity.

### `accepted_values` test fails
**Fix:** Update accepted_values list or fix data transformation.

## Output Checklist

- [ ] dbt build passes
- [ ] Downstream models unaffected
- [ ] Spot checks pass
- [ ] Test results documented

## Next Steps
If all tests pass, run `/deploy` to commit and open PR.
