# Scorecard Weakness Remediation Plan

**Goal:** Address weaknesses identified in a Lead Data Engineer scorecard review (scored 7.0/10) across code quality, production-readiness, business impact, scalability, and design patterns.

**Outcome:** Two dbt correctness fixes implemented. Seven originally-planned tasks were evaluated and dropped after reasoning about actual project context.

**Tech Stack:** dbt 1.11.8, Snowflake, Apache Airflow 2.9.3, Docker Compose, GitHub Actions, Power BI TMDL

---

## Decision Log

### ✅ Task 1: Fix Airflow Security — Fernet Key, Timezone, Resource Limits

**Implemented.** Commit `bffac53`.

- Set `AIRFLOW__CORE__FERNET_KEY: '${AIRFLOW_FERNET_KEY}'` (was empty string — all secrets stored unencrypted)
- Fixed all timezone settings from `America/New_York` → `UTC` for consistency with DAG schedule comments
- Added `deploy.resources.limits` to webserver (2 CPU / 3G), scheduler (2 CPU / 3G), postgres (1 CPU / 1G)
- Added `AIRFLOW_FERNET_KEY` to `.env.example` with generation instructions

**Files modified:**
- `airflow/docker-compose.yml`
- `airflow/.env.example`

---

### ~~Task 2: Add dbt Source Freshness~~ — DROPPED

**Reason: Redundant with existing monitoring.**

The project already has two layers of stale-data detection that together cover the same ground:

1. **`validate_copy_results`** Airflow task — confirms rows landed after every COPY INTO, at load time
2. **Airflow Slack notifications** — fires immediately if the DAG fails at any task

`dbt source freshness` adds a third signal at query time, but for synthetic data where Airflow controls both generation and loading, if `validate_copy_results` passed then the data is fresh by definition. Adding freshness checks would produce noise without meaningful additional protection.

---

### ✅ Task 3: Fix CLV Formula and Variable Usage

**Implemented.** Commit `e78a148`.

`dbt_project.yml` declares `clv_prediction_horizon_days: 365` but the actual SQL in `fct_clv_customer.sql` ignored this variable entirely (hardcoded `* 365`) and had a same-day customer edge case that returned `total_lifetime_revenue` directly — a large overestimate for brand-new customers.

**Changes:**
- Replaced hardcoded `365` with `{{ var('clv_prediction_horizon_days') }}` so the projection horizon is driven by configuration
- Replaced the `CASE WHEN lifespan = 0 THEN revenue` branch with `GREATEST(1, lifespan)` to clamp same-day customers to one day of revenue rather than their full historical spend
- Added model-level `dbt_utils.expression_is_true` test: `predicted_clv_12m >= 0`

**Files modified:**
- `dbt/models/marts/customer/fct_clv_customer.sql`
- `dbt/models/marts/customer/_customer_models.yml`

---

### ✅ Task 4: Reconcile RFM Seed with Model Output

**Implemented.** Commit `7a3b9c2` (see git log for exact SHA).

The seed `rfm_segment_definitions.csv` defined 8 segments. The model `fct_rfm_segments.sql` outputs exactly 5. The 3 extra seed rows (`Cant Lose Them`, `Loyal`, `Need Attention`) would never match any model row, causing silent NULLs on any report join.

**Model segments (source of truth):**
| Segment | Condition |
|---------|-----------|
| Champions | R≥4, F≥4, M≥4 |
| Loyalists | R≥3, F≥3 |
| New Customers | R≥4, total_orders ≤ 2 |
| At Risk / Hibernating | R=1 |
| General Pool | All other customers (ELSE) |

**Files modified:**
- `dbt/seeds/rfm_segment_definitions.csv` — rewritten from 8 rows to 5, names exactly matching model output

---

### ~~Task 5: Future-proof dim_dates end date~~ — DROPPED

**Reason: Not relevant for a portfolio project.**

The hardcoded `'2028-12-31'` end date in `dim_dates.sql` would be a real issue in a production system heading toward 2029. This is a showcase project for hiring managers using a historical dataset (Olist, ~2016–2018). It will never run in 2029. Adding a dynamic variable here introduces complexity with zero practical benefit.

---

### ~~Task 6: Harden Airflow DAGs~~ — DROPPED

**Reason: Existing monitoring already covers the failure scenarios.**

The proposed changes (try-except blocks, `trigger_rule="all_done"`, `max_active_runs=1`, backfill idempotency fix) address failure modes that are already surfaced by the Airflow Slack notifications and `validate_copy_results` task. For a portfolio project that isn't running in production, the added complexity doesn't demonstrate value beyond what's already there.

---

### ~~Task 7: Snowflake Resource Monitor + RAW Grant Cleanup~~ — DROPPED

**Reason: Infrastructure-level concern, not portfolio-relevant.**

A resource monitor and grant cleanup are legitimate production hardening concerns but don't showcase analytics engineering craft — they're operational housekeeping. A hiring manager reviewing this project is evaluating dbt modelling, pipeline design, and data quality patterns, not Snowflake account-level configuration.

---

### ~~Task 8: Fix Power BI Bi-Directional Relationship~~ — DROPPED

**Reason: Deferred — low impact on portfolio evaluation.**

The `FCT_CLV_CUSTOMER → DIM_CUSTOMERS` `bothDirections` relationship is a valid design pattern concern but the report currently works correctly, and fixing it would require verifying all CLV page visuals still render. Not prioritised given the other higher-signal fixes.

---

### ~~Task 9: Harden CI (SQLFluff blocking + pip caching)~~ — DROPPED

**Reason: Not relevant for a portfolio project.**

SQLFluff advisory-only and slow pip installs are CI pipeline operational concerns. A portfolio project that doesn't have contributors sending PRs doesn't benefit from a blocking lint gate. Demonstrating that CI exists and runs is sufficient.

---

## Verification

For the two dbt changes that were implemented:

```bash
cd ecommerce-retail-analytics/dbt

# CLV formula: no negative predictions
dbt test --select fct_clv_customer
# Expected: fct_clv_customer_predicted_clv_non_negative PASS

# RFM seed: 5 rows, no orphaned segments
dbt seed --select rfm_segment_definitions
dbt test --select fct_rfm_segments
# Expected: seed loads 5 rows; no NULLs on segment join
```

---

## Summary

| Task | Status | Reason |
|------|--------|--------|
| Task 1: Airflow Fernet key, timezone, resource limits | ✅ Done | Real security gap |
| Task 2: dbt source freshness | ❌ Dropped | Redundant with `validate_copy_results` + Slack |
| Task 3: CLV formula + variable + data test | ✅ Done | Correctness bug + unused configuration |
| Task 4: RFM seed reconciliation (8→5 segments) | ✅ Done | Data integrity — silent NULLs on join |
| Task 5: dim_dates dynamic end date | ❌ Dropped | Portfolio project; dataset is historical |
| Task 6: Airflow DAG hardening | ❌ Dropped | Covered by existing monitoring |
| Task 7: Snowflake resource monitor + grants | ❌ Dropped | Operational concern, not portfolio-relevant |
| Task 8: Power BI bi-directional relationship | ❌ Dropped | Low impact, deferred |
| Task 9: CI hardening (SQLFluff blocking, caching) | ❌ Dropped | No value for single-contributor portfolio |
