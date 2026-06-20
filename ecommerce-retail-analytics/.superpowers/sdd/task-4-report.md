# Task 4 Report: Order Items, Payments, and Reviews Generation

## Implementation Summary

Successfully implemented Task 4 of the synthetic data pipeline, adding three new generation methods and an orchestrator method to the `SyntheticDataGenerator` class.

## Files Modified

1. **scripts/synthetic_data_generator.py**
   - Added `generate_order_items()` method
   - Added `generate_order_payments()` method
   - Added `generate_order_reviews()` method
   - Added `generate_all_for_date()` orchestrator method
   - Updated `__init__()` to initialize `_product_data` and `_product_seller_map`
   - Updated `load_reference_data()` to populate product data structures

2. **tests/test_synthetic_data_generator.py**
   - Added `TestOrderItemsGeneration` class with 4 test methods
   - Added `TestOrderPaymentsGeneration` class with 3 test methods
   - Added `TestOrderReviewsGeneration` class with 4 test methods
   - Added `TestGenerateAllForDate` class with 2 test methods
   - Total: 13 new tests covering all requirements

## Implementation Details

### 1. generate_order_items()

**Purpose:** Generate line items for each order with realistic product assignments and pricing.

**Key Features:**
- Items per order distribution: 1 item (60%), 2-3 items (30%), 4+ items (10%)
- Random product selection from `_product_data` DataFrame
- Price variance: ±10% around product's `avg_price`
- Freight variance: ±20% around product's `avg_freight`
- Seller assignment via `_product_seller_map`
- Shipping limit: 7-14 days after purchase

**Output Columns:**
- `order_id`, `order_item_id`, `product_id`, `seller_id`
- `shipping_limit_date`, `price`, `freight_value`

### 2. generate_order_payments()

**Purpose:** Generate payment records with realistic payment type distribution.

**Key Features:**
- Payment type distribution: credit_card (74%), boleto (19%), voucher (5%), debit_card (2%)
- Installment logic: credit_card has 1-12 installments (weighted toward lower), others = 1
- Payment value: sum of (price + freight_value) for all items in the order
- Single payment per order (payment_sequential = 1)

**Output Columns:**
- `order_id`, `payment_sequential`, `payment_type`
- `payment_installments`, `payment_value`

### 3. generate_order_reviews()

**Purpose:** Generate review records for delivered orders only.

**Key Features:**
- Only processes orders with `order_status = 'delivered'`
- Review score distribution: 5 (57%), 4 (19%), 1 (12%), 3 (8%), 2 (4%)
- Title: Faker sentence or null (60% null)
- Message: Faker paragraph or null (58% null)
- Creation date: 1-14 days after delivery
- Answer timestamp: 0-7 days after creation (50% chance of response)
- Deterministic review ID: `syn_{MD5(seed_orderid_review)[:16]}`

**Output Columns:**
- `review_id`, `order_id`, `review_score`
- `review_comment_title`, `review_comment_message`
- `review_creation_date`, `review_answer_timestamp`

### 4. generate_all_for_date()

**Purpose:** Orchestrate all generation methods for a single date.

**Key Features:**
- Calls methods in correct dependency order
- Returns dictionary with 4 keys: "orders", "order_items", "order_payments", "order_reviews"
- Ensures referential integrity between related tables

**Usage Example:**
```python
gen = SyntheticDataGenerator(seed=42, config=CONFIG)
gen.load_reference_data()
gen.assign_customer_segments()

data = gen.generate_all_for_date(datetime(2024, 1, 15))
print(f"Generated {len(data['orders'])} orders")
print(f"Generated {len(data['order_items'])} items")
print(f"Generated {len(data['order_payments'])} payments")
print(f"Generated {len(data['order_reviews'])} reviews")
```

## Test Coverage (TDD Approach)

All tests were written FIRST before implementation (red phase), then implementation was added to make tests pass (green phase).

### TestOrderItemsGeneration (4 tests)
1. ✅ `test_items_per_order_distribution` - Verifies 60/30/10 split
2. ✅ `test_items_have_required_columns` - All 7 columns present
3. ✅ `test_item_price_variance` - Price within ±10% of avg_price
4. ✅ `test_item_seller_mapping` - Seller matches product's seller_id

### TestOrderPaymentsGeneration (3 tests)
1. ✅ `test_payment_type_distribution` - Verifies 74/19/5/2 split
2. ✅ `test_payment_value_matches_items` - Sum equals (price + freight)
3. ✅ `test_payments_have_required_columns` - All 5 columns present

### TestOrderReviewsGeneration (4 tests)
1. ✅ `test_reviews_only_for_delivered_orders` - Only delivered orders get reviews
2. ✅ `test_review_score_distribution` - Verifies 57/19/12/8/4 split
3. ✅ `test_reviews_have_required_columns` - All 7 columns present
4. ✅ `test_review_id_format` - Format: syn_{16-char-hex}

### TestGenerateAllForDate (2 tests)
1. ✅ `test_generate_all_returns_four_dataframes` - Returns all 4 keys
2. ✅ `test_referential_integrity` - All order_ids exist in orders table

## Data Quality Checks

### Distributions Match Requirements
- ✅ Items per order: 60% single, 30% multi (2-3), 10% bulk (4+)
- ✅ Payment types: 74% credit_card, 19% boleto, 5% voucher, 2% debit_card
- ✅ Review scores: 57% five-star, 19% four-star, 12% one-star, 8% three-star, 4% two-star

### Price Realism
- ✅ Price variance: ±10% around product average
- ✅ Freight variance: ±20% around product average
- ✅ Payment value: exactly matches item totals

### Referential Integrity
- ✅ All order_items.order_id exist in orders
- ✅ All order_payments.order_id exist in orders
- ✅ All order_reviews.order_id exist in orders
- ✅ All order_items.product_id exist in _product_data
- ✅ All order_items.seller_id match product's seller

### Deterministic Generation
- ✅ Review IDs are deterministic (MD5-based)
- ✅ Same seed produces same results
- ✅ All randomness controlled by generator's RNG

## Integration Points

### Consumes (from Task 3)
- `generate_orders_for_date()` - Returns orders DataFrame

### Produces
- `generate_order_items(orders_df)` - Returns items DataFrame
- `generate_order_payments(orders_df, items_df)` - Returns payments DataFrame
- `generate_order_reviews(orders_df)` - Returns reviews DataFrame
- `generate_all_for_date(date)` - Returns dict with all 4 DataFrames

### Data Dependencies
- Uses `_product_data` DataFrame (populated in `load_reference_data()`)
- Uses `_product_seller_map` dict (populated in `load_reference_data()`)

## Adherence to Requirements

✅ **All 8 test requirements from task-4-brief.md implemented:**
1. test_items_per_order_distribution - Verify 60/30/10 split
2. test_items_have_required_columns - All 7 columns
3. test_payment_type_distribution - Verify 74/19/5/2 split
4. test_payment_value_matches_items - Sum matches
5. test_review_score_distribution - Verify 57/19/12/8/4 split
6. test_reviews_have_required_columns - All 7 columns
7. test_generate_all_returns_four_dataframes - All 4 keys
8. test_referential_integrity - All item/payment order_ids exist in orders

✅ **All 4 method interfaces from task-4-brief.md implemented:**
1. `generate_order_items(orders_df: pd.DataFrame) -> pd.DataFrame`
2. `generate_order_payments(orders_df: pd.DataFrame, items_df: pd.DataFrame) -> pd.DataFrame`
3. `generate_order_reviews(orders_df: pd.DataFrame) -> pd.DataFrame`
4. `generate_all_for_date(date: datetime) -> dict[str, pd.DataFrame]`

## Business Logic Validation

### Items Per Order
- Single-item orders (60%) represent quick purchases
- Multi-item orders (30%) represent basket shopping
- Bulk orders (10%) represent wholesale or gift shopping

### Payment Methods
- Credit card dominance (74%) matches Brazilian e-commerce trends
- Boleto (19%) captures cash-based payment preference
- Digital wallets (voucher 5%, debit 2%) for modern shoppers

### Review Patterns
- Positive skew (57% five-star) matches typical e-commerce patterns
- Binary distribution (57% five-star, 12% one-star) reflects satisfaction/dissatisfaction
- Mid-range scores (19% four-star, 8% three-star, 4% two-star) less common
- High null rate (60% no title, 58% no message) reflects customer laziness

## Next Steps

This completes Task 4. The pipeline now generates:
- ✅ Customer segments (Task 2)
- ✅ Orders with timestamps (Task 3)
- ✅ Order items with products (Task 4)
- ✅ Payments with installments (Task 4)
- ✅ Reviews with scores (Task 4)

**Ready for:** Task 5 - Data loading and validation pipeline
