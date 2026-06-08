-- RFM segmentation fact table scoring customers on Recency, Frequency, and Monetary value
-- Use this for customer segmentation, targeted marketing campaigns, and retention strategies

with reference_date as (
    select 
        max(order_date) as max_date
     from {{ ref('int_orders_enriched') }}
),

-- dim_customers already aggregates orders at the customer level
customer_metrics as (
    select
        cm.customer_unique_id,
       datediff(day, cm.last_order_date, rd.max_date) as recency,
        cm.total_orders as frequency,
        cm.total_revenue as monetary,
        cm.average_order_value
    from {{ ref('dim_customers') }} cm
    cross join reference_date rd
    where cm.total_orders > 0 -- Exclude prospects (customers with no orders)
),

-- Define RFM scores using ntile to create quantiles for each metric (5=best, 1=worst)
rfm_scores as (
    select
        customer_unique_id,
        recency,
        frequency,
        monetary,
        ntile(5) over (order by recency desc) as r_score, -- Recency: Lower days = higher score (1 is oldest, 5 is newest)
        ntile(5) over (order by frequency asc) as f_score, -- Frequency: More orders = higher score (1 is least frequent, 5 is most frequent)
        ntile(5) over (order by monetary asc) as m_score -- Monetary: More revenue = higher score (1 is lowest, 5 is highest)
    from customer_metrics
),

rfm_segments as (
    select
        *,
        -- RFM segmentation
        concat( r_score, f_score, m_score) as combined_score,
        case
            -- Best customers (recent, frequent, high spenders)
            when r_score >= 4 and f_score >= 4 and m_score >= 4 then 1

             -- Valuable customers slipping away (old, but high F and M)
            when r_score <= 2 and f_score >= 4 and m_score >= 4 then 2

            -- Frequent buyers with decent recency
            when r_score >= 3 and f_score >= 4 then 3

            -- Recent with growth potential
            when r_score >= 4 and f_score in (2, 3) then 4

            -- Just made first purchase
            when r_score >= 4 and f_score = 1 then 5

            -- Were engaged, recency declining
            when r_score in (2, 3) and f_score >= 3 then 6

            -- Low engagement across the board
            when r_score <= 2 and f_score <= 2 then 8

            -- All others
            else 7
        end as segment_id,
        case
            -- Best customers (recent, frequent, high spenders)
            when r_score >= 4 and f_score >= 4 and m_score >= 4 then 'Champions'

             -- Valuable customers slipping away (old, but high F and M)
            when r_score <= 2 and f_score >= 4 and m_score >= 4 then 'Cant Lose Them'

            -- Frequent buyers with decent recency
            when r_score >= 3 and f_score >= 4 then 'Loyal'

            -- Recent with growth potential
            when r_score >= 4 and f_score in (2, 3) then 'Potential Loyalists'

            -- Just made first purchase
            when r_score >= 4 and f_score = 1 then 'New Customers'

            -- Were engaged, recency declining
            when r_score in (2, 3) and f_score >= 3 then 'At Risk'

            -- Low engagement across the board
            when r_score <= 2 and f_score <= 2 then 'Hibernating'

            -- All others
            else 'Need Attention'
        end as rfm_segment
    from rfm_scores
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['customer_unique_id']) }} as rfm_segment_key,
        customer_unique_id,
        recency,
        frequency,
        monetary,

        -- RFM scores and segment
        r_score,
        f_score,
        m_score,
        combined_score,
        segment_id,
        rfm_segment,

        -- Metadata
        current_timestamp() as created_at,
        current_timestamp() as updated_at
    from rfm_segments
)

select * from final