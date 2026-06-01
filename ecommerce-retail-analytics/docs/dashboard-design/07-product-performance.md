# Product Performance (Pareto) — Narrative Brief

---

## Page Identity

| Attribute | Value |
|-----------|-------|
| **Page Name** | Product Performance |
| **Page Number** | 7 of 10 |
| **Canvas Size** | 1920 x 1080 |
| **Primary Color** | Deep Blue with category accents |

---

## Objective

**What decision does this page help make?**

This page answers: *"Which products and categories drive our business, and where should we focus inventory and marketing?"*

Pareto analysis reveals:
1. The vital few products that generate most revenue (80/20 rule)
2. Category performance rankings
3. Long-tail product opportunities
4. Inventory and marketing prioritization

---

## Target Audience

| Audience | Context | Time Spent |
|----------|---------|------------|
| **Category Manager** | Assortment planning | 5-10 minutes |
| **Merchandising** | Promotion planning | 3-5 minutes |
| **Supply Chain** | Inventory prioritization | 2-3 minutes |

---

## Key Questions Answered

| # | Question | Why It Matters |
|---|----------|----------------|
| 1 | Which 20% of products generate 80% of revenue? | Focus allocation |
| 2 | What are the top-performing categories? | Category strategy |
| 3 | How concentrated is our revenue? | Risk assessment |
| 4 | Which products are in the long tail? | Rationalization candidates |
| 5 | What is the average revenue per product? | Benchmarking |
| 6 | How does category performance trend? | Growth opportunities |

---

## Visual Layout (Wireframe)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  HEADER: "Product Performance (Pareto Analysis)"         [Category Slicer]     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  TOTAL      │  │  PRODUCTS   │  │  TOP 20%    │  │  AVG REV    │            │
│  │  PRODUCTS   │  │  FOR 80%    │  │  REVENUE    │  │  PER PRODUCT│            │
│  │   32.9K     │  │    2.1K     │  │   R$ 12.3M  │  │   R$ 470    │            │
│  │             │  │    (6.4%)   │  │   (80%)     │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    PARETO CURVE (COMBO CHART)                            │   │
│  │                                                                          │   │
│  │  Revenue │                                            ____████ 100%     │   │
│  │          │                              _____████████                   │   │
│  │          │                    _____█████                                │   │
│  │          │          _____█████                    ← Cumulative %        │   │
│  │          │    ██████                                                    │   │
│  │          │ ████  ← Individual Revenue                                   │   │
│  │          └────────────────────────────────────────────────────────────  │   │
│  │             Products (ranked by revenue)                                │   │
│  │                                                                          │   │
│  │  [80% line marked | 20% of products marked]                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────┐  ┌─────────────────────────────┐  │
│  │   CATEGORY REVENUE (BAR CHART)          │  │   PARETO SEGMENT BREAKDOWN  │  │
│  │                                         │  │        (DONUT)              │  │
│  │  Health & Beauty  ████████████  R$ 1.2M │  │                             │  │
│  │  Watches          █████████    R$ 980K  │  │   Top 5%:    35% revenue    │  │
│  │  Bed & Bath       ████████     R$ 870K  │  │   Next 15%:  45% revenue    │  │
│  │  Sports           ███████      R$ 720K  │  │   Bottom 80%: 20% revenue   │  │
│  │  Furniture        ██████       R$ 650K  │  │                             │  │
│  │  [Top 10 categories]                    │  │                             │  │
│  └─────────────────────────────────────────┘  └─────────────────────────────┘  │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │  TOP PRODUCTS TABLE                                                      │   │
│  │  Rank | Product ID | Category | Revenue | Orders | Cum Rev % | Segment   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Mapping

### KPI Cards

| Visual | Measure Name | Source | Calculation |
|--------|--------------|--------|-------------|
| Total Products | `Product Count` | FCT_PARETO_PRODUCTS | `COUNTROWS(FCT_PARETO_PRODUCTS)` |
| Products for 80% | `Products to 80%` | FCT_PARETO_PRODUCTS | `COUNT where CUMULATIVE_REVENUE_PCT <= 0.80` |
| Top 20% Revenue | `Top 20% Revenue` | FCT_PARETO_PRODUCTS | `SUM where CUMULATIVE_PRODUCT_PCT <= 0.20` |
| Avg Rev per Product | `Avg Product Revenue` | FCT_PARETO_PRODUCTS | `AVERAGE(TOTAL_REVENUE)` |

### Pareto Curve (Combo Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Combo Chart (Bar + Line) |
| **X-Axis** | Product Rank (or binned) |
| **Y-Axis (Bars)** | TOTAL_REVENUE (individual) |
| **Y-Axis (Line)** | CUMULATIVE_REVENUE_PCT |
| **Reference Lines** | 80% horizontal, 20% vertical |

### Category Revenue (Bar Chart)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Horizontal Bar Chart |
| **Y-Axis** | PRODUCT_CATEGORY |
| **X-Axis** | SUM(TOTAL_REVENUE) |
| **Top N** | 10 |
| **Sort** | Revenue descending |

### Pareto Segment Breakdown (Donut)

| Attribute | Value |
|-----------|-------|
| **Visual Type** | Donut Chart |
| **Legend** | PARETO_SEGMENT |
| **Values** | SUM(TOTAL_REVENUE) per segment |
| **Labels** | Segment name + percentage |

### Top Products Table

| Column | Source |
|--------|--------|
| Rank | REVENUE_RANK |
| Product ID | PRODUCT_ID |
| Category | PRODUCT_CATEGORY |
| Revenue | TOTAL_REVENUE |
| Orders | TOTAL_ORDERS |
| Cumulative % | CUMULATIVE_REVENUE_PCT |
| Pareto Segment | PARETO_SEGMENT |

---

## Filter Context

| Filter | Type | Default | Applies To |
|--------|------|---------|------------|
| Category | Slicer (multi-select) | All | All visuals |
| Pareto Segment | Slicer | All | Focus on segments |

---

## Interactions & Drill-Through

| User Action | Result |
|-------------|--------|
| Click category bar | Filter Pareto curve to that category |
| Click Pareto segment | Filter table to that segment |
| Hover on Pareto curve | Show product details |
| Click product in table | Drill-through to product detail |

---

## Design Specifications

### Pareto Segment Colors

| Segment | Hex | Description |
|---------|-----|-------------|
| Top 5% | `#1E3A5F` | Vital few |
| Top 20% | `#4A7AB0` | Important |
| Middle 30% | `#90A4AE` | Moderate |
| Bottom 50% | `#CFD8DC` | Long tail |

### Reference Line Colors

| Line | Hex | Style |
|------|-----|-------|
| 80% Revenue | `#D84315` | Dashed |
| 20% Products | `#2E7D32` | Dashed |

---

## DAX Measures Required

```
Folder: _Base
├── Total Products
├── Total Product Revenue
├── Avg Revenue per Product

Folder: _Analytical
├── Products for 80% Revenue
├── Top 20% Product Revenue
├── Top 20% Product Revenue %
├── Revenue Concentration Ratio
├── Long Tail Product Count

Folder: _Segments
├── Top 5% Revenue
├── Top 20% Revenue
├── Middle 30% Revenue
├── Bottom 50% Revenue

Folder: _Data Visualization
├── Pareto Segment Color
├── Cumulative % Label
├── Rank Display
```

---

## Success Criteria

| Criteria | Measurement |
|----------|-------------|
| **80/20 visible** | Clear visualization of Pareto principle |
| **Category clarity** | Top categories immediately identifiable |
| **Segment actionability** | Each Pareto segment has business implication |
| **Long tail awareness** | Bottom products visible for rationalization |

---

## Implementation Checklist

- [ ] Build Pareto combo chart with reference lines
- [ ] Create category revenue bar chart with Top N
- [ ] Configure Pareto segment donut
- [ ] Build top products table with ranking
- [ ] Add cumulative percentage calculations
- [ ] Configure 80/20 reference lines
- [ ] Test category filtering on Pareto curve
