USE AdventureWorksDW2022
GO

-- SALES PERFORMANCE & RANKING 
/* 
1.	Top Products by Revenue per Year - Identify the top 5 products by revenue 
for each calendar year, showing their rank and revenue contribution percentage.
*/
WITH ProductRevenue AS (	
	-- Step 1: Calculate total revenue for each product and year
	SELECT 
		fis.ProductKey,
		dd.CalendarYear,
		SUM(fis.SalesAmount) AS TotalRevenue
	FROM dbo.FactInternetSales fis
	INNER JOIN dbo.DimDate dd ON fis.OrderDateKey = dd.DateKey
	GROUP BY fis.ProductKey, dd.CalendarYear
),
RankedProducts AS (
	-- Step 2: Rank products by revenue within each year and calculate yearly revenue
	-- Use DENSE_RANK to prevent arbitrary exclusion of equally-performing products
	SELECT 
		ProductKey,
		CalendarYear,
		TotalRevenue,
		SUM(TotalRevenue) OVER (PARTITION BY CalendarYear) AS YearlyRevenue,
		DENSE_RANK() OVER (PARTITION BY CalendarYear ORDER BY TotalRevenue DESC) AS RevenueRank
	FROM ProductRevenue
)
-- Step 3: Select top 5 products per year and calculate revenue contribution percentage
SELECT
	CalendarYear,
	p.EnglishProductName,
	FORMAT(TotalRevenue, 'C0') AS TotalRevenue,
	FORMAT(YearlyRevenue, 'C0') AS YearlyRevenue,
	RevenueRank,
	FORMAT(TotalRevenue / NULLIF(YearlyRevenue, 0), 'P') AS RevenueContributionPct
FROM RankedProducts rp
INNER JOIN dbo.DimProduct p ON rp.ProductKey = p.ProductKey
WHERE RevenueRank <= 5
ORDER BY CalendarYear, RevenueRank;



/* 
2.	Sales Rep Performance Ranking - Rank sales representatives by quarterly revenue, 
showing their rank change compared to the previous quarter.
*/
WITH SalesRepRevenue AS (
	-- Step 1: Calculate total revenue by quarter for each sales rep
	SELECT 
		rs.EmployeeKey,
		e.FirstName,
		e.LastName,
		dd.CalendarYear,
		dd.CalendarQuarter,
		SUM(SalesAmount) AS QuarterlySales
	FROM dbo.FactResellerSales rs
	INNER JOIN dbo.DimEmployee e ON rs.EmployeeKey = e.EmployeeKey
	INNER JOIN dbo.DimDate dd ON rs.OrderDateKey = dd.DateKey
	WHERE e.SalesPersonFlag = 1
	GROUP BY rs.EmployeeKey, e.FirstName, e.LastName, dd.CalendarYear, dd.CalendarQuarter
),
SalesRepCurrentRanking AS (
	-- Step 2: Calculate sales reps previous quarter's sales and sales change, and rank them by current quarter's sales
	SELECT 
		EmployeeKey,
		CONCAT_WS(' ', FirstName, LastName) AS SalesRepName,
		CalendarYear,
		CalendarQuarter,
		QuarterlySales,
		LAG(QuarterlySales) OVER (PARTITION BY EmployeeKey ORDER BY CalendarYear, CalendarQuarter) AS PreviousQuarterSales,
		DENSE_RANK() OVER (PARTITION BY CalendarYear, CalendarQuarter ORDER BY QuarterlySales DESC) AS CurrentRank
	FROM SalesRepRevenue
),
SalesRepPreviousRanking AS (
	-- Step 3: Calculate previous quarter's rank for each sales rep
	SELECT 
		EmployeeKey,
		SalesRepName,
		CalendarYear,
		CalendarQuarter,
		QuarterlySales,
		PreviousQuarterSales,
		QuarterlySales - PreviousQuarterSales AS QuarterlySalesChange,
		CurrentRank,
		LAG(CurrentRank) OVER (PARTITION BY EmployeeKey ORDER BY CalendarYear, CalendarQuarter) AS PreviousRank
	FROM SalesRepCurrentRanking
)
SELECT 
	CalendarYear,
	CONCAT('Q', CalendarQuarter) AS Quarter,
	SalesRepName,
	FORMAT(QuarterlySales, 'N2') AS QuarterlySales, 
	FORMAT(PreviousQuarterSales, 'N2') AS PreviousQuarterSales,
	FORMAT(QuarterlySalesChange, 'N2') AS QuarterlySalesChange,
	CurrentRank,
	PreviousRank,
	CASE 
		WHEN PreviousRank IS NULL THEN 'New entry' 
		WHEN PreviousRank - CurrentRank > 0 THEN 'Up by ' + CAST(ABS(PreviousRank - CurrentRank) AS NVARCHAR) + ' ranks' 
		WHEN PreviousRank - CurrentRank < 0 THEN 'Down by ' + CAST(ABS(PreviousRank - CurrentRank) AS NVARCHAR) + ' ranks' 
		ELSE 'No change'
	END AS RankChange
FROM SalesRepPreviousRanking
ORDER BY CalendarYear, CalendarQuarter, QuarterlySales DESC;



/* 
3.	Product Category Revenue Distribution - Calculate what percentile each product 
falls into based on total revenue (use NTILE or PERCENT_RANK for quartile/decile analysis).
*/
WITH ProductRevenue AS (
	-- Step 1: Aggregate revenue at the grain of product ID
	SELECT 
		ProductKey,
		SUM(SalesAmount) AS TotalRevenue
	FROM dbo.FactInternetSales
	GROUP BY ProductKey
),
ProductDistribution AS (
	-- Step 2: Bring in product names and categories and calculate revenue statistical distribution
SELECT 
	cat.EnglishProductCategoryName AS Category,
	p.EnglishProductName AS Product,
	TotalRevenue,
	PERCENT_RANK() OVER (
		PARTITION BY cat.EnglishProductCategoryName
		ORDER BY TotalRevenue
	) AS RevenuePercentile
FROM ProductRevenue pr
INNER JOIN dbo.DimProduct p ON pr.ProductKey = p.ProductKey
INNER JOIN dbo.DimProductSubcategory sub ON p.ProductSubcategoryKey = sub.ProductSubcategoryKey
INNER JOIN dbo.DimProductCategory cat ON sub.ProductCategoryKey = cat.ProductCategoryKey
)
SELECT 
	Category,
	Product,
	FORMAT(TotalRevenue, 'C0') AS Revenue,
	FORMAT(RevenuePercentile, 'P') AS RevenuePercentile,
	CASE 
		WHEN RevenuePercentile >= 0.90 THEN 'Tier 1: Top 10% Performer'
		WHEN RevenuePercentile >= 0.75 THEN 'Tier 2: Top 25% Performer'
		WHEN RevenuePercentile >= 0.50 THEN 'Tier 3: Above Average'
		ELSE 'Tier 4: Below Average'
	END AS PerformanceTier
FROM ProductDistribution
ORDER BY Category, TotalRevenue DESC;



/* 
4.	Best and Worst Performing Territories - Rank territories by revenue growth rate 
year-over-year, identifying top 3 and bottom 3 performers.
*/
WITH TerritoryRevenue AS (
	-- Step 1: Calculate yearly revenue for each territory
	SELECT 
		dd.CalendarYear,
		st.SalesTerritoryCountry,
		SUM(fis.SalesAmount) AS YearlyRevenue
	FROM dbo.FactInternetSales fis
	INNER JOIN dbo.DimDate dd ON fis.OrderDateKey = dd.DateKey
	INNER JOIN dbo.DimSalesTerritory st ON fis.SalesTerritoryKey = st.SalesTerritoryKey
	WHERE SalesTerritoryCountry IS NOT NULL AND SalesTerritoryCountry <> 'NA'
	GROUP BY dd.CalendarYear, st.SalesTerritoryCountry
),
YoYGrowthStats AS (
	-- Step 2: Calculate year-over-year growth rate for each territory
	SELECT 
		CalendarYear,
		SalesTerritoryCountry,
		YearlyRevenue,
		LAG(YearlyRevenue) OVER (PARTITION BY SalesTerritoryCountry ORDER BY CalendarYear) AS PreviousYearRevenue,
		LAG(CalendarYear) OVER (PARTITION BY SalesTerritoryCountry ORDER BY CalendarYear) AS PreviousYear
	FROM TerritoryRevenue
),
YoYGrowthRanked AS (
	-- Step 3: Rank territories by top/bottom YoY growth rate
	SELECT 
		CalendarYear,
		PreviousYear,
		SalesTerritoryCountry,
		YearlyRevenue,
		PreviousYearRevenue,
		YearlyRevenue - PreviousYearRevenue AS YoYChange,
		(YearlyRevenue - PreviousYearRevenue) / NULLIF(PreviousYearRevenue, 0) AS YoYGrowthRate,
		DENSE_RANK() OVER (PARTITION BY CalendarYear ORDER BY (YearlyRevenue - PreviousYearRevenue) / NULLIF(PreviousYearRevenue, 0) DESC) AS TopRank,
		DENSE_RANK() OVER (PARTITION BY CalendarYear ORDER BY (YearlyRevenue - PreviousYearRevenue) / NULLIF(PreviousYearRevenue, 0) ASC) AS BottomRank
	FROM YoYGrowthStats
	WHERE PreviousYear = CalendarYear - 1 AND PreviousYearRevenue IS NOT NULL
)
SELECT 
	CalendarYear,
	SalesTerritoryCountry,
	FORMAT(YearlyRevenue, 'C0') AS YearlyRevenue,
	FORMAT(PreviousYearRevenue, 'C0') AS PreviousYearRevenue,
	FORMAT(YoYChange, 'C0') AS YoYChange,
	FORMAT(YoYGrowthRate, 'P') AS YoYGrowthRate,
	CASE 
		WHEN TopRank <= 3 THEN 'Top ' + CAST(TopRank AS NVARCHAR) + ' Performer'
		WHEN BottomRank <= 3 THEN 'Bottom ' + CAST(BottomRank AS NVARCHAR) + ' Performer'
	END AS PerformanceCategory
FROM YoYGrowthRanked
WHERE TopRank <= 3 OR BottomRank <= 3
ORDER BY CalendarYear, TopRank;
