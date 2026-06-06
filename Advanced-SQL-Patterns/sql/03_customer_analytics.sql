USE AdventureWorksDW2022
GO

-- CUSTOMER ANALYTICS
/*
9.	Customer Segmentation by Purchase Frequency - Segment customers into quintiles 
based on their order frequency and calculate average order value per segment.
*/
WITH CustomerMetrics AS (
	-- Step 1: Calculate order frequency and total revenue for each customer
	SELECT 
		CustomerKey, 
		COUNT(DISTINCT SalesOrderNumber) AS Frequency,
		SUM(SalesAmount) AS Monetary
	FROM dbo.FactInternetSales 
	GROUP BY CustomerKey
),
FrequencyScore AS (
	-- Step 2: Use PERCENT_RANK to score customers based on their order frequency
    -- NTILE will bucket customers arbitrarily which will skew the data
	SELECT 
		CustomerKey,
		Frequency,
		Monetary,
		Monetary / NULLIF(Frequency, 0) AS AvgOrderValue,
		PERCENT_RANK() OVER (ORDER BY Frequency ASC) AS F_Score
	FROM CustomerMetrics
)
-- Final output with customer segmentation based on frequency score
SELECT 
	CustomerKey AS CustomerID,
	Frequency AS OrderFrequency,
	FORMAT(Monetary, 'C0') AS TotalRevenue,
	FORMAT(AvgOrderValue, 'C0') AS AvgOrderValue,
	FORMAT(F_Score, 'P') AS FrequencyPercent,
	CASE 
		WHEN F_Score >= 0.8 THEN 'Top 20% - Most Frequent Buyers'
		WHEN F_Score >= 0.6 THEN 'Next 20% - Frequent Buyers'
		WHEN F_Score >= 0.4 THEN 'Middle 20% - Average Buyers'
		WHEN F_Score >= 0.2 THEN 'Next 20% - Infrequent Buyers'
		ELSE 'Bottom 20% - Least Frequent Buyers'
	END AS Segment
FROM FrequencyScore
ORDER BY OrderFrequency DESC;



/*
10.	Customer Lifetime Value Ranking - Rank customers by total lifetime value 
within each geographic region.
*/
DECLARE @MaxOrderDate DATE = (SELECT MAX(OrderDate) FROM dbo.FactInternetSales);
DECLARE @ChurnThresholdDays INT = 180; -- Define churn threshold (e.g., 180 days of inactivity)

WITH CustomerMetrics AS (
	-- Step 1: Calculate total revenue for each customer and their geographic region
	SELECT 
		st.SalesTerritoryRegion AS Region,
		c.CustomerKey,
		c.FirstName, 
		c.MiddleName, 
		c.LastName,
		SUM(fis.SalesAmount) AS TotalRevenue,
		SUM(fis.SalesAmount - fis.TotalProductCost) AS TotalProfit,
		COUNT(DISTINCT fis.SalesOrderNumber) AS TotalOrders,
		DATEDIFF(DAY, MIN(fis.ORDERDATE), @MaxOrderDate) /365.25 AS CustomerTenureYears,
		DATEDIFF(DAY, MAX(fis.ORDERDATE), @MaxOrderDate) AS DaysSinceLastOrder
	FROM dbo.FactInternetSales fis
	INNER JOIN dbo.DimSalesTerritory st ON fis.SalesTerritoryKey = st.SalesTerritoryKey
	INNER JOIN dbo.DimCustomer c ON fis.CustomerKey = c.CustomerKey
	GROUP BY  
		st.SalesTerritoryRegion, 
		c.CustomerKey,
		c.FirstName,
		c.MiddleName,
		c.LastName
),
RegionalBenchmarks AS (
	-- Step 2: Calculate regional churn rates and expected lifespan (multiplier) for each region
    SELECT
        Region,
        CustomerKey,
		CONCAT_WS(' ', FirstName, MiddleName, LastName) AS CustomerName,
        TotalRevenue,
		TotalProfit,
        TotalOrders,
		CustomerTenureYears,
		DaysSinceLastOrder,
		-- Identify churn rate based on inactivity (e.g., > 180 days since last order)
		CASE WHEN DaysSinceLastOrder > @ChurnThresholdDays THEN 1 ELSE 0 END AS IsChurned,
		-- Calculate unique customers in each region for APV and APF calculations
        COUNT(*) OVER (PARTITION BY Region) AS RegionCustomerCount
    FROM CustomerMetrics
),
RegionalChurn AS (
	-- Step 3: Calculate regional churn rates to get the expected lifespan constant for each region
    SELECT
        Region,
        CustomerName,
        TotalRevenue,
		TotalProfit,
        TotalOrders,
		CustomerTenureYears,
		DaysSinceLastOrder,
        IsChurned,
        RegionCustomerCount,
		-- Regional churn rate = Total churned customers in region / Total customers in region 
		CAST(SUM(IsChurned) OVER (PARTITION BY Region) AS FLOAT) / RegionCustomerCount AS RegionalChurnRate
    FROM RegionalBenchmarks
), 
PredictiveCLV AS (
	-- Step 4: Calculate predictive CLV using the formula: CLV = (APV * APF) * Lifespan
	SELECT
		Region,
		CustomerName,
		TotalRevenue,
		TotalProfit,
		TotalOrders,
		CustomerTenureYears,
		DaysSinceLastOrder,
		RegionalChurnRate,
		-- APV: Average Profit Value (using profit is more accurate than revenue for CLV)
		TotalProfit / NULLIF(TotalOrders, 0) AS AvgPurchaseValue,
		-- APF: Annual Purchase Frequency (orders per year of tenure)
		TotalOrders / NULLIF(NULLIF(CustomerTenureYears, 0), NULL) AS AvgPurchaseFrequency,
		-- Lifespan: 1 / Churn Rate (e.g., 20% churn = 5 year expected lifespan)
		ROUND(1.0 / NULLIF(RegionalChurnRate, 0), 2) AS ExpectedLifespanYears
	FROM RegionalChurn
)
-- Step 5: Final CLV calculation and ranking within each region
SELECT
	Region,
	CustomerName,
	FORMAT(TotalRevenue, 'C0') AS TotalRevenue,
	FORMAT(TotalProfit, 'C0') AS TotalProfit,
	TotalOrders,
	CustomerTenureYears,
	DaysSinceLastOrder,
	CAST(RegionalChurnRate AS DECIMAL(10,2)) AS RegionalChurnRate,
	FORMAT(AvgPurchaseValue, 'C0') AS AvgPurchaseValue,
	CAST(AvgPurchaseFrequency AS DECIMAL(10,2)) AS AvgPurchaseFrequency,
	ExpectedLifespanYears,
	-- Predictive CLV = APV * APF * Lifespan
	FORMAT(ROUND(AvgPurchaseValue * AvgPurchaseFrequency * ExpectedLifespanYears, 2), 'C0') AS PredictedCLV,
	RANK() OVER (PARTITION BY Region ORDER BY (AvgPurchaseValue * AvgPurchaseFrequency * ExpectedLifespanYears) DESC) AS CLVRank
FROM PredictiveCLV
ORDER BY Region, CLVRank;



/*
11.	First vs. Most Recent Purchase Analysis - For each customer, compare their first 
purchase amount with their most recent purchase (use FIRST_VALUE and LAST_VALUE).
*/
WITH CustomerPurchases AS (
    SELECT 
        CustomerKey,
        OrderDate,
        SalesOrderLineNumber,
        SalesAmount,
        -- Get the first purchase amount
        FIRST_VALUE(SalesAmount) OVER (
            PARTITION BY CustomerKey 
            ORDER BY OrderDate, SalesOrderLineNumber
        ) AS FirstPurchaseAmount,
        
        -- Get the most recent purchase amount using the full window frame
        LAST_VALUE(SalesAmount) OVER (
            PARTITION BY CustomerKey 
            ORDER BY OrderDate, SalesOrderLineNumber
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        ) AS MostRecentPurchaseAmount
    FROM dbo.FactInternetSales
)
SELECT DISTINCT
    CustomerKey,
    FirstPurchaseAmount,
    MostRecentPurchaseAmount,
    MostRecentPurchaseAmount - FirstPurchaseAmount AS PurchaseAmountChange
FROM CustomerPurchases
ORDER BY CustomerKey;



/*
12.	Customer Retention Cohort Analysis - Calculate customer retention rates by cohort month.
*/
WITH CustomerFirstPurchase AS (
	-- Step 1: Identify the first purchase date ('Birth') for each customer
	SELECT 
		CustomerKey,
		MIN(OrderDate) AS FirstPurchaseDate
	FROM dbo.FactInternetSales
	GROUP BY CustomerKey
),
CustomerCohorts AS (
	-- Step 2:Assign cohort month-year for each customer
	SELECT 
		CustomerKey,
		FirstPurchaseDate,
		DATETRUNC(MONTH, FirstPurchaseDate) AS CohortMonth,
		FORMAT(FirstPurchaseDate, 'MMM-yyyy') AS CohortMonthName
	FROM CustomerFirstPurchase
),
RetentionActivity AS (
	-- Step 3: The 'Aging' Layer: Calculate months since first purchase
	-- Aggregate unique customers per cohort period
	SELECT
		cc.CohortMonth,
		cc.CohortMonthName,
		DATEDIFF(MONTH, cc.CohortMonth, fis.OrderDate) AS MonthNumber,
		COUNT(DISTINCT cc.CustomerKey) AS ActiveCustomers
	FROM CustomerCohorts cc
	INNER JOIN dbo.FactInternetSales fis ON cc.CustomerKey = fis.CustomerKey
	GROUP BY cc.CohortMonth, cc.CohortMonthName, DATEDIFF(MONTH, cc.CohortMonth, fis.OrderDate)
)
-- Step 4: Final Retention Output showing 'Retention Triangle' of active customers by cohort and month number
SELECT 
	CohortMonthName,
	[0] AS Mon0, [1] AS Mon1, [2] AS Mon2, [3] AS Mon3, [4] AS Mon4,
	[5] AS Mon5, [6] AS Mon6, [7] AS Mon7, [8] AS Mon8, [9] AS Mon9,
	[10] AS Mon10, [11] AS Mon11, [12] AS Mon12, [13] AS Mon13, [14] AS Mon14, 
	[15] AS Mon15, [16] AS Mon16, [17] AS Mon17, [18] AS Mon18, [19] AS Mon19, 
	[20] AS Mon20, [21] AS Mon21, [22] AS Mon22, [23] AS Mon23, [24] AS Mon24
FROM (
	-- Subquery to calculate retention rate by cohort and month number
	SELECT 
		CohortMonth,
		CohortMonthName,
		MonthNumber,
		FORMAT(CAST(ActiveCustomers AS FLOAT) / 
		FIRST_VALUE(ActiveCustomers) OVER (PARTITION BY CohortMonth ORDER BY MonthNumber), 'P') AS RetentionRate
	FROM RetentionActivity
) AS RetentionTable
PIVOT (
	MAX(RetentionRate) 
	FOR MonthNumber IN ([0], [1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12], 
	[13], [14], [15], [16], [17], [18], [19], [20], [21], [22], [23], [24])
) AS PivotRetention
ORDER BY CohortMonth;
