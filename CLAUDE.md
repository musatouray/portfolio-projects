# CLAUDE.md

Context for Claude Code when working on this project.

## Agentic Workflow

For structured workflows, see **[.claude/AGENTS.md](.claude/AGENTS.md)**.

### Skills

| Command | Purpose |
|---------|---------|
| `/develop` | Scaffold new models (SQL + YAML) |
| `/test` | Run tests & validate changes |
| `/deploy` | Commit & open PR |
| `/check-test-failures` | Diagnose production failures |
| `/refactor` | Optimize existing models |

> **Note:** These are project-specific skills in `.claude/skills/<skill-name>/SKILL.md`. Read the SKILL.md file directly and follow its instructions.

### References (Load When Needed)

| Reference | Use For |
|-----------|---------|
| `.claude/references/dbt-conventions.md` | dbt best practices |
| `.claude/references/sql-conventions.md` | SQL style guide |
| `.claude/references/yaml-conventions.md` | YAML documentation |
| `.claude/references/data-warehouse.md` | Snowflake queries |

---

## Architecture

### Medallion Pattern

```
ECOMMERCE_RETAIL_DB_DEV              ECOMMERCE_RETAIL_DB_PROD
├── RAW (Bronze)                     ├── INTERMEDIATE (Gold)
├── STAGING (Silver)            →    └── MARTS (Gold) ← Power BI
├── INTERMEDIATE (Gold)
└── MARTS (Gold)
```

- **Staging** always deploys to DEV (shared Silver layer)
- **PROD** reads from DEV.STAGING via cross-database reference
- **CI** runs in isolated `CI_PR_xxx` schema

### Pipeline Flow

```
Airflow (11 AM UTC)                    GitHub Actions (12 PM UTC)
Generate → S3 → Snowflake RAW    →    dbt build PROD → Power BI
         → dbt build DEV
```

### CI/CD

- **CI**: PR triggers `dbt build --select state:modified+` in isolated schema
- **CD**: Merge to main triggers `dbt build` to PROD (also runs daily at 12 PM UTC)
- **Fabric**: `fabric-prod` branch syncs `report/` folder to production workspace

---

## Surrogate Key Strategy

Using `MD5_NUMBER_LOWER64` for 64-bit integer surrogate keys (not `dbt_utils.generate_surrogate_key`):

```sql
{{ generate_int_surrogate_key(['order_id', 'product_id']) }}
-- Compiles to: MD5_NUMBER_LOWER64(concat(coalesce(cast(order_id as varchar), ''), '-', ...))
```

**Why:** ~70% memory reduction in Power BI vs 32-char hex strings. MD5 is version-stable (unlike Snowflake's `HASH()`).

---

## Git Workflow

```bash
# Feature development
git checkout -b feature/name
git add . && git commit -m "feat: description"
git push -u origin feature/name
gh pr create && gh pr merge --squash

# Promote to Fabric production
git checkout fabric-prod && git merge main && git push
```

---

## Testing Strategy

| Layer | Tests |
|-------|-------|
| Sources | not_null, unique on PKs |
| Staging | not_null, unique, relationships, accepted_values |
| Intermediate | not_null, unique on grain |
| Marts | not_null, unique on grain |

---

## Known Issues & Fixes

| Issue | Solution |
|-------|----------|
| order_reviews duplicates | ROW_NUMBER dedup in staging |
| geolocation multiple coords per zip | GROUP BY + AVG |
| customer_id vs customer_unique_id | Generator uses customer_id for FK integrity |
| Snowflake private key auth | Use `private_key_path` in profiles.yml |

---

## Configuration

| Setting | Value |
|---------|-------|
| Warehouse | `ECOMMERCE_RETAIL_WH` |
| Role | `LEAD_DATA_ENGINEER_ROLE` |
| S3 Stage | `raw_ecommerce_s3_stage` |
| S3 Bucket | `ecommerce-retail-analytics-raw` |

For setup details, see **[INSTALLATION.md](INSTALLATION.md)**.
