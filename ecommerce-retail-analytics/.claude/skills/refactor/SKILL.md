---
name: refactor
description: Optimize existing dbt models for performance or readability
allowed-tools: Read Write Edit Bash Glob Grep
---

# /refactor - Optimize Existing Models

## Purpose
Improve performance, readability, and maintainability of existing models without changing business logic.

## Prerequisites
- Load `references/sql-conventions.md`
- Load `references/dbt-conventions.md`
- Identify target model(s) for refactoring

## Procedure

### Step 1: Analyze Current State

Read the model and check its configuration:
```bash
cd dbt
cat models/<path>/<model>.sql
```

### Step 2: Identify Refactoring Opportunities

#### Performance Issues

| Pattern | Problem | Solution |
|---------|---------|----------|
| `SELECT *` | Scans unnecessary columns | List specific columns |
| Multiple `NTILE()` in CASE | Window computed multiple times | Compute once in CTE |
| Repeated subqueries | Redundant computation | Extract to CTE |
| Missing `NULLIF()` | Division by zero errors | Add `NULLIF(x, 0)` |

#### Code Quality Issues

| Pattern | Problem | Solution |
|---------|---------|----------|
| Deep nesting | Hard to read | Flatten with CTEs |
| Magic numbers | Unclear logic | Use dbt vars |
| Inconsistent naming | Confusing | Follow conventions |
| Long SQL files | Hard to maintain | Split into intermediate models |

### Step 3: Common Refactoring Patterns

#### Extract Repeated Window Functions
Compute window function once in a CTE, reference in subsequent logic.

#### Replace Magic Numbers with Variables
Use `{{ var('threshold_name') }}` instead of hardcoded values.

#### Add Defensive NULL Handling
Use `NULLIF(denominator, 0)` for division operations.

#### Flatten Deep Subqueries
Convert nested subqueries to named CTEs.

#### Optimize Materialization

| Scenario | Recommended |
|----------|-------------|
| Small lookup table | table |
| Large fact table, full refresh | incremental |
| Intermediate transform | view or ephemeral |
| Aggregation used once | ephemeral |

### Step 4: Validate Refactoring

**Critical:** Refactoring must NOT change output.

```bash
# Run tests to ensure logic unchanged
uv run dbt build --select <model_name>
```

### Step 5: Invoke Code Reviewer

Review the refactored SQL for:
- [ ] Logic equivalence (no behavior change)
- [ ] Performance improvement
- [ ] Readability improvement
- [ ] Convention adherence
- [ ] Edge case handling

### Step 6: Update Documentation

If refactoring changes column names or adds columns:
1. Update YAML descriptions
2. Update any dependent documentation
3. Notify downstream consumers if breaking

### Step 7: Run Full Test Suite

```bash
uv run dbt build --select <model_name>+
```

## Refactoring Checklist

- [ ] Current state analyzed
- [ ] Improvement opportunities identified
- [ ] Changes preserve business logic
- [ ] Output validated
- [ ] Code review completed
- [ ] Tests pass
- [ ] Documentation updated

## Anti-Patterns to Avoid

| Don't Do This | Do This Instead |
|---------------|-----------------|
| Change logic while refactoring | Separate PRs |
| Skip validation | Always compare outputs |
| Refactor without tests | Add tests first |
| Rename columns | Deprecate gracefully |
| Over-optimize early | Profile first |

## Next Steps
Run `/test` then `/deploy` to ship the refactored model.
