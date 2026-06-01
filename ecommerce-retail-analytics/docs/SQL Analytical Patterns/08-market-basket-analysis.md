# Market Basket Analysis - Interview Study Guide

## What is Market Basket Analysis?

Market Basket Analysis identifies products frequently purchased together. It answers:

- "What products are often bought together?"
- "If a customer buys X, what else should we recommend?"
- "Which product bundles should we create?"

```
Order 1: [A, B, C]     →  Pairs: (A,B), (A,C), (B,C)
Order 2: [A, B]        →  Pairs: (A,B)
Order 3: [B, C, D]     →  Pairs: (B,C), (B,D), (C,D)

Result: (A,B) appears in 2 orders → Strong association
```

---

## Key Terms and Definitions

| Term | Definition | Formula |
|------|------------|---------|
| **Support** | How often a pair appears in all orders | `pair_count / total_orders` |
| **Confidence** | Probability of B given A was purchased | `pair_count / orders_with_A` |
| **Lift** | How much more likely vs random chance | `confidence / (orders_with_B / total_orders)` |
| **Antecedent** | The "if" product (A in "if A then B") | Product triggering the rule |
| **Consequent** | The "then" product (B in "if A then B") | Product being recommended |

### Interpreting Metrics

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Support** | 0.01 (1%) | This pair appears in 1% of all orders |
| **Confidence** | 0.25 (25%) | 25% of orders with A also have B |
| **Lift** | 1.0 | No association (random chance) |
| **Lift** | > 1 | Positive association (bought together more than expected) |
| **Lift** | < 1 | Negative association (bought together less than expected) |

---

## Why FAANG Cares

### 1. Revenue Generation
- Cross-sell recommendations: "Customers who bought X also bought Y"
- Product bundling: Create packages with high-lift pairs
- Cart suggestions: Real-time recommendations at checkout

### 2. Inventory & Operations
- Stock products together that sell together
- Plan promotions for complementary products
- Optimize warehouse placement

### 3. Tests SQL Skills
- **Self-Joins**: Pairing products within the same order
- **Aggregation**: Counting co-occurrences
- **Division Safety**: `NULLIF()` for percentages
- **Filtering**: Minimum thresholds to reduce noise

### 4. Common Interview Questions
- "How would you find products frequently bought together?"
- "Design a recommendation system based on purchase history"
- "What's the difference between confidence and lift?"
- "How would you avoid recommending obvious pairs (e.g., phone + phone case)?"

---

## CTE Structure

```
┌─────────────────────┐
│    order_items      │  ← Get order_id, product_id, category
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  item_popularity    │  ← Count orders per product (for confidence/lift)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   overall_orders    │  ← Total orders (for support)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│   product_pairs     │  ← Self-join to find co-purchases
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│       final         │  ← Calculate support, confidence, lift
└─────────────────────┘
```

---

## SQL Patterns

### Pattern 1: Self-Join for Product Pairs

```sql
-- Find products purchased together
SELECT
    a.product_id AS product_a,
    b.product_id AS product_b,
    COUNT(DISTINCT a.order_id) AS pair_count
FROM order_items a
JOIN order_items b
    ON a.order_id = b.order_id
    AND a.product_id < b.product_id  -- Avoid duplicates!
GROUP BY 1, 2
```

**Why `product_id < product_id`?**
- Without it: (A,B) and (B,A) are counted as separate pairs
- With it: Only (A,B) is counted (where A < B alphabetically/numerically)
- Prevents duplicate pairs and self-pairs (A,A)

### Pattern 2: Support Calculation

```sql
-- Support = pair_count / total_orders
ROUND(pair_count * 100.0 / total_orders, 4) AS support_pct
```

Support is typically very small (0.01% - 1%) because most products don't appear together.

### Pattern 3: Confidence Calculation (Bidirectional)

```sql
-- Confidence A→B: Given A, probability of B
ROUND(pair_count * 100.0 / NULLIF(product_a_orders, 0), 2) AS confidence_a_to_b_pct

-- Confidence B→A: Given B, probability of A
ROUND(pair_count * 100.0 / NULLIF(product_b_orders, 0), 2) AS confidence_b_to_a_pct
```

**Why bidirectional?**
- Confidence A→B ≠ Confidence B→A
- If phone cases are bought with phones 80% of the time (A→B = 80%)
- But phones aren't always bought with cases (B→A = 10%)
- Helps determine recommendation direction

### Pattern 4: Lift Calculation

```sql
-- Lift = observed frequency / expected frequency
-- Simplified: (pair_count * total_orders) / (product_a_orders * product_b_orders)
ROUND(
    (pair_count * total_orders)::FLOAT /
    NULLIF(product_a_orders * product_b_orders, 0),
    2
) AS lift
```

**Lift interpretation:**
- Lift = 1: Products are independent (no association)
- Lift > 1: Products are bought together more than expected
- Lift < 1: Products are bought together less than expected
- Lift = 2: Pair is 2x more likely than random chance

### Pattern 5: Minimum Threshold Filter

```sql
-- Filter noise with minimum pair count
HAVING COUNT(DISTINCT a.order_id) >= {{ var('min_pair_count', 5) }}
```

Using a dbt variable makes the threshold configurable without code changes.

---

## Complete SQL Example

```sql
WITH order_items AS (
    SELECT
        order_id,
        product_id,
        product_category
    FROM {{ ref('int_order_items_enriched') }}
),

-- Product popularity for confidence/lift calculations
item_popularity AS (
    SELECT
        product_id,
        product_category,
        COUNT(DISTINCT order_id) AS total_orders_per_product
    FROM order_items
    GROUP BY 1, 2
),

-- Global denominator for support
overall_orders AS (
    SELECT COUNT(DISTINCT order_id) AS overall_total_orders
    FROM order_items
),

-- Self-join to find product pairs
product_pairs AS (
    SELECT
        a.product_id AS product_a,
        b.product_id AS product_b,
        a.product_category AS category_a,
        b.product_category AS category_b,
        COUNT(DISTINCT a.order_id) AS pair_count
    FROM order_items a
    JOIN order_items b
        ON a.order_id = b.order_id
        AND a.product_id < b.product_id
    GROUP BY 1, 2, 3, 4
    HAVING COUNT(DISTINCT a.order_id) >= {{ var('min_pair_count', 5) }}
),

final AS (
    SELECT
        pp.product_a,
        pp.product_b,
        pp.category_a,
        pp.category_b,
        pp.pair_count,
        ia.total_orders_per_product AS product_a_order_count,
        ib.total_orders_per_product AS product_b_order_count,

        -- Support
        ROUND(pp.pair_count * 100.0 / oo.overall_total_orders, 4) AS support_pct,

        -- Confidence (both directions)
        ROUND(pp.pair_count * 100.0 / NULLIF(ia.total_orders_per_product, 0), 2) AS confidence_a_to_b_pct,
        ROUND(pp.pair_count * 100.0 / NULLIF(ib.total_orders_per_product, 0), 2) AS confidence_b_to_a_pct,

        -- Lift
        ROUND(
            (pp.pair_count * oo.overall_total_orders)::FLOAT /
            NULLIF(ia.total_orders_per_product * ib.total_orders_per_product, 0),
            2
        ) AS lift
    FROM product_pairs pp
    JOIN item_popularity ia ON pp.product_a = ia.product_id
    JOIN item_popularity ib ON pp.product_b = ib.product_id
    CROSS JOIN overall_orders oo
)

SELECT * FROM final
```

---

## Key SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `SELF-JOIN` | Pair rows from same table | `a JOIN b ON a.order_id = b.order_id` |
| `a.id < b.id` | Avoid duplicate pairs | Ensures (A,B) not (B,A) |
| `COUNT(DISTINCT)` | Unique order count | `COUNT(DISTINCT order_id)` |
| `NULLIF(x, 0)` | Prevent division by zero | `pair_count / NULLIF(orders, 0)` |
| `CROSS JOIN` | Add scalar to all rows | `CROSS JOIN overall_orders` |
| `HAVING` | Filter aggregated results | `HAVING pair_count >= 5` |

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Missing `a.id < b.id` | Duplicate pairs (A,B) and (B,A) | Add inequality condition |
| Using `a.id != b.id` | Still creates duplicates | Use `<` not `!=` |
| No minimum threshold | Millions of noise pairs | Add `HAVING pair_count >= N` |
| Only one confidence | Misses recommendation direction | Calculate both A→B and B→A |
| Integer division | Support/confidence = 0 | Multiply by `100.0` first |
| Counting rows not orders | Inflated pair counts | Use `COUNT(DISTINCT order_id)` |

---

## Business Applications

### 1. Product Recommendations
```sql
-- Top recommendations for a specific product
SELECT
    product_b AS recommended_product,
    category_b AS recommended_category,
    confidence_a_to_b_pct,
    lift
FROM fct_market_basket
WHERE product_a = 'target_product_id'
ORDER BY lift DESC
LIMIT 5
```

### 2. Bundle Creation
```sql
-- High-lift pairs for bundle candidates
SELECT
    category_a,
    category_b,
    AVG(lift) AS avg_lift,
    SUM(pair_count) AS total_co_purchases
FROM fct_market_basket
WHERE lift > 2  -- Strong positive association
GROUP BY 1, 2
ORDER BY avg_lift DESC
```

### 3. Cross-Category Insights
```sql
-- Which categories are bought together?
SELECT
    category_a,
    category_b,
    COUNT(*) AS pair_count,
    AVG(lift) AS avg_lift
FROM fct_market_basket
WHERE category_a != category_b  -- Cross-category only
GROUP BY 1, 2
ORDER BY avg_lift DESC
```

### 4. Same-Category Upsells
```sql
-- Products in same category bought together (upsell opportunities)
SELECT *
FROM fct_market_basket
WHERE category_a = category_b
  AND lift > 1
ORDER BY pair_count DESC
```

---

## Interview Tips

1. **Start with business context**: "Market basket analysis helps identify products frequently bought together, enabling cross-sell recommendations and bundle creation."

2. **Explain the self-join**: "I join the order_items table to itself on order_id to find products that appear in the same order. The `product_a < product_b` condition prevents counting (A,B) and (B,A) as separate pairs."

3. **Distinguish the metrics**: "Support tells us how common the pair is overall. Confidence tells us the probability of one product given the other. Lift tells us if the association is stronger than random chance."

4. **Mention thresholds**: "I filter pairs with fewer than 5 co-occurrences to reduce noise from random coincidences."

5. **Connect to action**: "A lift of 5 means customers buy these together 5x more often than expected — a strong signal for bundling or recommendation."

---

## Practice Questions

1. Why do we use `product_a < product_b` instead of `product_a != product_b`?

2. Product A appears in 100 orders, Product B in 50 orders, and they appear together in 25 orders out of 10,000 total. Calculate support, confidence A→B, confidence B→A, and lift.

3. A pair has 80% confidence A→B but only 5% confidence B→A. What does this tell you about the relationship?

4. How would you modify this analysis to find products bought within the same session but in different orders?

5. The PM asks "why is lift so high for some pairs?" — what would you investigate?

6. How would you incorporate time (seasonality) into market basket analysis?

---

## Related Patterns

| Pattern | Relationship to Market Basket |
|---------|------------------------------|
| **Cohort Analysis** | Basket composition by customer cohort |
| **Pareto Analysis** | Focus on top products, then analyze their baskets |
| **RFM Segmentation** | Basket patterns by customer segment |
| **Funnel Analysis** | Add-to-cart to purchase conversion by product pair |

---

## Extensions

### Sequence Analysis (Order Matters)
```sql
-- What do customers buy AFTER product A?
SELECT
    a.product_id AS first_product,
    b.product_id AS next_product,
    COUNT(*) AS sequence_count
FROM orders o1
JOIN orders o2
    ON o1.customer_id = o2.customer_id
    AND o2.order_date > o1.order_date
JOIN order_items a ON o1.order_id = a.order_id
JOIN order_items b ON o2.order_id = b.order_id
GROUP BY 1, 2
```

### Time-Bounded Baskets
```sql
-- Products bought within 7 days of each other
WHERE DATEDIFF(day, o1.order_date, o2.order_date) <= 7
```

### Category-Level Basket
```sql
-- Analyze at category level instead of product level
SELECT
    a.category AS category_a,
    b.category AS category_b,
    COUNT(DISTINCT a.order_id) AS pair_count
FROM order_items a
JOIN order_items b
    ON a.order_id = b.order_id
    AND a.category < b.category
GROUP BY 1, 2
```
