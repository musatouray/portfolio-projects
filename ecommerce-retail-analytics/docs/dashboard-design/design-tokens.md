# Design Tokens

Human-readable reference for the Power BI theme. See `ecommerce-analytics-theme.json` for the actual theme file.

---

## Colors

### Primary Palette

| Role | Hex | Usage |
|------|-----|-------|
| Primary | `#1E3A5F` | Headers, KPIs, primary data |
| Primary Light | `#4A6FA5` | Secondary elements, totals |
| Positive | `#2E7D32` | Growth, success, ▲ |
| Negative | `#D84315` | Decline, risk, ▼ |
| Neutral | `#607D8B` | Supporting text, labels |
| Background | `#FAFAFA` | Page canvas |
| Card | `#FFFFFF` | Visual containers |
| Border | `#E0E0E0` | Gridlines, dividers |

### Data Series

| # | Hex | Name |
|---|-----|------|
| 1 | `#1E3A5F` | Deep Blue |
| 2 | `#00897B` | Teal |
| 3 | `#FFA000` | Amber |
| 4 | `#7B1FA2` | Purple |
| 5 | `#C2185B` | Pink |
| 6 | `#0097A7` | Cyan |

### Segment Colors

| Segment Type | Values |
|--------------|--------|
| RFM Segments | Champions: `#1E3A5F`, Loyal: `#00897B`, At Risk: `#FF7043`, Hibernating: `#90A4AE` |
| Churn Status | Active: `#2E7D32`, Cooling: `#FFA000`, At Risk: `#FF7043`, Churned: `#D84315` |
| CLV Tiers | High: `#1E3A5F`, Medium: `#00897B`, Low: `#90A4AE` |

---

## Typography

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Page Title | Segoe UI | 24px | Semibold |
| KPI Value | Segoe UI | 32px | Bold |
| KPI Label | Segoe UI | 12px | Regular |
| Chart Title | Segoe UI | 14px | Semibold |
| Axis Labels | Segoe UI | 10px | Regular |
| Table Header | Segoe UI | 11px | Semibold |
| Table Values | Segoe UI | 11px | Regular |

---

## Spacing

8px grid system:

| Element | Padding | Margin |
|---------|---------|--------|
| Card | 16px | 8px |
| Section | 24px | 16px |

| Property | Value |
|----------|-------|
| Border Radius | 8px |
| Shadow | 0 2px 4px rgba(0,0,0,0.08) |

---

## Indicators

| Direction | Symbol | Color |
|-----------|--------|-------|
| Up | ▲ | `#2E7D32` |
| Down | ▼ | `#D84315` |
| Flat | ─ | `#607D8B` |

---

## Number Formats

| Type | Format | Example |
|------|--------|---------|
| Currency (large) | R$ #,##0.0,,"M" | R$ 15.4M |
| Currency (medium) | R$ #,##0.0,"K" | R$ 980K |
| Currency (small) | R$ #,##0 | R$ 160 |
| Percentage | 0.0% | 12.3% |
| Count (large) | #,##0.0,"K" | 96.4K |
| Count (small) | #,##0 | 3,245 |
