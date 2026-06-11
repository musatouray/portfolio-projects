-- Date dimension table with one row per calendar day
-- Use this for time-based analysis: trends, seasonality, and period comparisons

with generated_dates as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2016-01-01' as date)",
        end_date="cast('2028-12-31' as date)"
    ) }}
),

final as (
    select
        -- Integer surrogate key in YYYYMMDD format (e.g., 20231225)
        to_number(to_char(date_day, 'YYYYMMDD')) as date_key,
        date_day as date,
        year(date_day) as year,
        yearofweekiso(date_day) as iso_year,
        yearofweekiso(date_day) || '-W' || lpad(weekiso(date_day), 2, '0') as iso_year_week,
        year(date_day) || '-Q' || quarter(date_day) as year_quarter,
        date_trunc('year', date_day) as year_start_date,
        to_char(date_day, 'YYYY-MM') as year_month,
        quarter(date_day) as quarter_number,
        'Q' || quarter(date_day) as quarter_name,
        date_trunc('quarter', date_day) as quarter_start_date,
        month(date_day) as month,
        monthname( date_day) as month_name,
        to_char( date_day, 'Mon-YYYY') as month_year,
        date_trunc('month', date_day) as month_start_date,
        week(date_day) as week,
        week(date_day) || '-' || year(date_day) as year_week,
        date_trunc('week', date_day) as week_start_date,
        day(date_day) as day,
        dayofweekiso(date_day) as iso_day_of_week,
        dayname(date_day) as day_name,
        dayofweek(date_day) as day_of_week,

        -- Boolean flags for weekend (true if Saturday or Sunday, false otherwise)
        case when dayname(date_day) in ('Sat', 'Sun') then true else false end as is_weekend,
        (dayofweekiso(date_day) in (6, 7)) as is_iso_weekend,
       
        -- Zero-Width Character Hack for visual sorting of single-value month names correctly (e.g., J, F, M, ...)
        concat(left(monthname(date_day), 1), repeat(chr(8203), month(date_day))) as month_initial,
        
         -- Metadata
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    from generated_dates
)

select * from final