# Market Basket Analysis — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Market Basket Analysis |
| **Page Number** | 8 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with association accents |

---

## Objective

**What decision does this page help make?**

This page answers: *"Which products are frequently purchased together, and how can we optimize cross-selling?"*

Market basket analysis reveals:
1. Product co-purchase patterns
2. Cross-sell and upsell opportunities
3. Bundle creation candidates
4. Category affinity insights

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **Merchandising** | Bundle creation, promotions | 5-10 minutes |
| **E-commerce Manager** | Recommendation engine input | 3-5 minutes |
| **Marketing** | Cross-sell campaign targeting | 2-3 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | Which products are most frequently bought together? | Bundle opportunities |
| 2 | What is the lift for top product pairs? | Association strength |
| 3 | Which categories have affinity? | Cross-category promotion |
| 4 | What is the confidence for recommendations? | Recommendation quality |
| 5 | How common are multi-item orders? | Basket size opportunity |
| 6 | Which pairs have highest support? | Volume-based decisions |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Market Basket Analysis"                        [Category Filter]     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  PRODUCT    │  │  AVG LIFT   │  │  TOP PAIR   │  │  AVG        │            │
│  │  PAIRS      │  │             │  │  SUPPORT    │  │  CONFIDENCE │            │
│  │    1.2K     │  │    2.4x     │  │    0.8%     │  │    35%      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    TOP PRODUCT PAIRS (NETWORK GRAPH or TABLE)            │   │
│  │                                                                          │   │
│  │    [Product A] ──────────── [Product B]                                  │   │
│  │         │                        │                                       │   │
│  │         │      Lift: 3.2x        │                                       │   │
│  │         │      Support: 0.5%     │                                       │   │
│  │         │      Confidence: 42%   │                                       │   │
│  │         │                        │                                       │   │
│  │    [Product C] ──────────── [Product D]                                  │   │
│  │                                                                          │   │
│  │  [Alternative: Horizontal bar showing pair strength]                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   CATEGORY AFFINITY (HEATMAP/MATRIX)    │  │   LIFT vs SUPPORT (SCATTER) │  │
│  │                                         │  │                             │  │
│  │        Cat A  Cat B  Cat C  Cat D       │  │   Lift │    ○               │  │
│  │  Cat A  ---   0.8%   0.3%   0.1%        │  │        │  ○   ○             │  │
│  │  Cat B  0.8%  ---    0.5%   0.2%        │  │        │    ○    ○          │  │
│  │  Cat C  0.3%  0.5%   ---    0.4%        │  │        │ ○          ○       │  │
│  │  Cat D  0.1%  0.2%   0.4%   ---         │  │        └──────────────────  │  │
│  │                                         │  │           Support           │  │
│  │  [Color: Dark = high affinity]          │  │   [Size = Pair Count]       │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  PRODUCT PAIR DETAIL TABLE                                               │   │
│  │  Product A | Product B | Pair Count | Support % | Conf A→B | Lift        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Calculation |
|--------|--------------|--------|-------------|
| Product Pairs | `Total Pairs` | FCT_MARKET_BASKET | `COUNTROWS(FCT_MARKET_BASKET)` |
| Avg Lift | `Avg Lift` | FCT_MARKET_BASKET | `AVERAGE(LIFT)` |
| Top Support | `Max Support` | FCT_MARKET_BASKET | `MAX(SUPPORT_PCT)` |
| Avg Confidence | `Avg Confidence` | FCT_MARKET_BASKET | `AVERAGE(CONFIDENCE_A_TO_B_PCT)` |

### Top Product Pairs (Table/Visual)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Table or Custom Visual (Network) |
| **Rows** | Top 20 pairs by LIFT or PAIR_COUNT |
| **Columns** | PRODUCT_A, PRODUCT_B, LIFT, SUPPORT_PCT, CONFIDENCE_A_TO_B_PCT |
| **Sort** | By Lift descending (or user-selectable) |

### Category Affinity (Matrix/Heatmap)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Matrix with conditional formatting |
| **Rows** | CATEGORY_A |
| **Columns** | CATEGORY_B |
| **Values** | SUM(PAIR_COUNT) or AVG(SUPPORT_PCT) |
| **Color Scale** | Light (low) → Dark (high affinity) |

### Lift vs Support (Scatter)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Scatter Chart |
| **X-Axis** | SUPPORT_PCT |
| **Y-Axis** | LIFT |
| **Size** | PAIR_COUNT |
| **Details** | PRODUCT_A, PRODUCT_B |

### Product Pair Detail Table

| Column | Source |
|--------|--------|
| Product A | PRODUCT_A |
| Product B | PRODUCT_B |
| Category A | CATEGORY_A |
| Category B | CATEGORY_B |
| Pair Count | PAIR_COUNT |
| Support % | SUPPORT_PCT |
| Confidence A→B | CONFIDENCE_A_TO_B_PCT |
| Confidence B→A | CONFIDENCE_B_TO_A_PCT |
| Lift | LIFT |

---

## Association Rule Metrics Explained

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| **Support** | P(A ∩ B) | How often the pair appears together |
| **Confidence A→B** | P(B\|A) | If A is bought, probability of B |
| **Lift** | P(A ∩ B) / P(A) × P(B) | Strength of association (>1 = positive) |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| Category | Slicer (multi-select) | All | All visuals |
| Min Support | Slider | 0.1% | Filter low-volume pairs |
| Min Lift | Slider | 1.0 | Filter weak associations |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click category in heatmap | Filter pairs to that category combo |
| Click scatter point | Show pair details in tooltip |
| Click product pair | Drill-through to product comparison |
| Hover on heatmap cell | Show exact support and pair count |

---

## Design Specifications

### Lift Color Scale

| Lift Value | Hex | Interpretation |
|------------|-----|----------------|
| < 1.0 | `#90A4AE` | Negative/neutral association |
| 1.0 - 1.5 | `#FFC107` | Weak positive |
| 1.5 - 2.5 | `#FF9800` | Moderate positive |
| 2.5 - 4.0 | `#FF7043` | Strong positive |
| > 4.0 | `#D84315` | Very strong positive |

### Affinity Heatmap Colors

| Affinity | Hex |
|----------|-----|
| Low | `#E3F2FD` |
| Medium | `#64B5F6` |
| High | `#1E3A5F` |

---

## DAX Measures Required

```
Folder: _Base
├── Total Product Pairs
├── Total Pair Occurrences
├── Avg Pair Count

Folder: _Analytical
├── Avg Lift
├── Avg Support %
├── Avg Confidence %
├── Max Lift
├── High Lift Pair Count (Lift > 2)

Folder: _Segments
├── Strong Association Count
├── Cross-Category Pair Count
├── Same-Category Pair Count

Folder: _Data Visualization
├── Lift Color
├── Support Label
├── Pair Display Name
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **Top pairs visible** | Strongest associations immediately clear |
| **Category patterns** | Cross-category opportunities identifiable |
| **Actionable insights** | Pairs have clear bundle/promo implications |
| **Metric understanding** | Users understand lift vs support vs confidence |

---

## Implementation Checklist

- [ ] Build product pairs table with sorting options
- [ ] Create category affinity heatmap
- [ ] Build lift vs support scatter plot
- [ ] Add support/lift threshold filters
- [ ] Include metric explanations in tooltips
- [ ] Configure cross-filtering between visuals
- [ ] Add Top N filter for manageable display
