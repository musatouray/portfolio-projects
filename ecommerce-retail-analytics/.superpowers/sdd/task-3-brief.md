# Task 3: Synthetic Data Generator - Order Generation

**Files:**
- Modify: `scripts/synthetic_data_generator.py`
- Modify: `tests/test_synthetic_data_generator.py`

**Interfaces:**
- Consumes: `SyntheticDataGenerator` from Task 2
- Produces:
  - `SyntheticDataGenerator.calculate_daily_orders(date: datetime) -> int`
  - `SyntheticDataGenerator.generate_order_id(date: datetime, sequence: int) -> str`
  - `SyntheticDataGenerator.generate_orders_for_date(date: datetime) -> pd.DataFrame`

## Requirements

### calculate_daily_orders(date)
Growth curve formula: `135 + (max_orders - base) * days_elapsed / max_days`
- Oct 2018: ~135 orders/day
- Jun 2023: ~380 orders/day  
- Jun 2026: ~500 orders/day

### generate_order_id(date, sequence)
Format: `syn_{YYYYMMDD}_{sequence:06d}_{hash:8}`
Example: `syn_20240115_000042_a3f8c921`
- Use MD5 hash of `{seed}_{date_str}_{sequence}` for the 8-char hash

### generate_orders_for_date(date) -> DataFrame
Returns DataFrame with columns:
- order_id, customer_id, order_status
- order_purchase_timestamp, order_approved_at
- order_delivered_carrier_date, order_delivered_customer_date
- order_estimated_delivery_date

Status distribution:
- delivered: 97%
- shipped: 1%
- canceled: 1%
- unavailable: 0.5%
- processing: 0.5%

Timestamp flow:
- purchase: random hour of the day
- approved: 0-24 hours after purchase
- carrier: 1-5 days after approval
- delivered: 3-20 days after carrier
- estimated: actual delivery + random variance (-3 to +5 days)

For non-delivered orders, clear appropriate timestamps (canceled = no carrier/delivery, shipped = no delivery)

## Tests to write FIRST (TDD):
1. `test_daily_order_volume_growth` - Verify 135→500 growth curve
2. `test_order_id_format` - Verify syn_YYYYMMDD_NNNNNN_HHHHHHHH format, length 28
3. `test_order_id_deterministic` - Same inputs = same ID
4. `test_generate_orders_returns_dataframe` - Correct columns, non-empty
5. `test_order_status_distribution` - ~97% delivered

## Global Constraints
- Seed = 42 for reproducibility
- Reset RNG per date using: `date_seed = self.seed + int(date.strftime("%Y%m%d"))`
