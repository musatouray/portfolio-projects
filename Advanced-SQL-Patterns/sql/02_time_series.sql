USE AdventureWorksDW2022
GO

-- TIME SERIES & TREND ANALYSIS 
/* 
5.	Running Total of Sales by Month - Calculate a running total of internet sales 
revenue by month, partitioned by product category.
*/
WITH MonthlySales AS (
	-- Step 1: Calculate total sales by month and product category
	SELECT 
		dd.CalendarYear,
		dd.MonthNumberOfYear,
		dd.EnglishMonthName AS Month,
		cat.ProductCategoryKey AS CategoryID,
		cat.EnglishProductCategoryName AS Category,
		SUM(fis.SalesAmount) AS MonthlySales
	FROM dbo.FactInternetSales fis
	INNER JOIN dbo.DimDate dd ON fis.OrderDateKey = dd.DateKey
	INNER JOIN dbo.DimProduct p ON fis.ProductKey = p.ProductKey
	INNER JOIN dbo.DimProductSubcategory sub ON p.ProductSubcategoryKey = sub.ProductSubcategoryKey
	INNER JOIN dbo.DimProductCategory cat ON sub.ProductCategoryKey = cat.ProductCategoryKey
	GROUP BY dd.CalendarYear, dd.MonthNumberOfYear, dd.EnglishMonthName, cat.ProductCategoryKey, cat.EnglishProductCategoryName
),

CategoryRunningTotal AS (
	-- Step 2: Calculate running total of sales by month for each product category
	SELECT 
		CalendarYear,
		MonthNumberOfYear,
		Month,
		CategoryID,
		Category,
		MonthlySales,
		SUM(MonthlySales) OVER (PARTITION BY CategoryID ORDER BY CalendarYear, MonthNumberOfYear) AS RunningTotal
	FROM MonthlySales
)
SELECT 
	CalendarYear,
	Month,
	Category,
	FORMAT(MonthlySales, 'C0') AS MonthlySales,
	FORMAT(RunningTotal, 'C0') AS RunningTotal
FROM CategoryRunningTotal
ORDER BY CalendarYear, MonthNumberOfYear, CategoryID;



/* 
6.	Month-over-Month Sales Growth - Calculate the percentage change in sales revenue 
compared to the previous month for each territory.
*/
WITH DateSpine AS (
	-- Step 1: Create a date spine. All distinct year-month combinations
	SELECT DISTINCT 
		CalendarYear,
		MonthNumberOfYear AS MonthID,
		EnglishMonthName AS Month
	FROM dbo.DimDate
	WHERE DateKey BETWEEN 
		(SELECT MIN(OrderDateKey) FROM dbo.FactInternetSales) AND
		(SELECT MAX(OrderDateKey) FROM dbo.FactInternetSales)	
),
TerritoryMonthJoin AS (
	-- Step 2: Cross join the dimensions. Create all Territory x Month combinations
	SELECT 
		ds.CalendarYear,
		ds.MonthID,
		ds.Month,
		st.SalesTerritoryCountry AS Country
	FROM DateSpine ds
	CROSS JOIN (
		SELECT DISTINCT SalesTerritoryCountry
		FROM dbo.DimSalesTerritory
		WHERE SalesTerritoryCountry IS NOT NULL AND SalesTerritoryCountry <> 'NA'
		) st
),
TerritoryMonthlySales AS (
	-- Step 3: Left Join sales data to preserve all months, including those with $0 sales.
	SELECT
		tmj.CalendarYear,
		tmj.MonthID,
		tmj.Month,
		tmj.Country,
		COALESCE(sales.MonthlySales, 0) AS MonthlySales
	FROM TerritoryMonthJoin tmj
	LEFT JOIN ( 
		-- Pre-aggregate sales by country, year, month
		SELECT 
			st.SalesTerritoryCountry AS Country,
			dd.CalendarYear,
			dd.MonthNumberOfYear AS MonthID,
			SUM(fis.SalesAmount) AS MonthlySales
		FROM dbo.FactInternetSales fis
		INNER JOIN dbo.DimDate dd ON fis.OrderDateKey = dd.DateKey
		INNER JOIN dbo.DimSalesTerritory st ON fis.SalesTerritoryKey = st.SalesTerritoryKey
		GROUP BY st.SalesTerritoryCountry, dd.CalendarYear, dd.MonthNumberOfYear
	) sales
		ON tmj.Country = sales.Country
		AND tmj.CalendarYear = sales.CalendarYear
		AND tmj.MonthID = sales.MonthID
),
MoMGrowth AS (
	-- Step 4: Calculate month-over-month growth percentage for each territory
	SELECT 
		CalendarYear,
		MonthID,
		Month,
		Country,
		MonthlySales,
		LAG(MonthlySales) OVER (PARTITION BY Country ORDER BY CalendarYear, MonthID) AS PreviousMonthSales,
		MonthlySales - LAG(MonthlySales) OVER (PARTITION BY Country ORDER BY CalendarYear, MonthID) AS MoMChange
	FROM TerritoryMonthlySales
)
--Final MoM Growth Output with formatted value
SELECT 
	CalendarYear,
	Month,
	Country,
	FORMAT(MonthlySales, 'C0') AS MonthlySales,
	FORMAT(PreviousMonthSales, 'C0') AS PreviousMonthSales,
	FORMAT(MoMChange, 'C0') AS MoMChange,
	FORMAT(MoMChange / NULLIF(PreviousMonthSales, 0) , 'P') AS MoMGrowthRate
FROM MoMGrowth
ORDER BY CalendarYear, MonthID, Country;



/* 
7.	3-Month Moving Average - Compute a 3-month moving average of sales 
to smooth out seasonal fluctuations.
*/
WITH MonthlySales AS (
	-- Step 1: Calculate total sales by month
	SELECT 
		dd.CalendarYear,
		dd.MonthNumberOfYear AS MonthID,
		dd.EnglishMonthName AS Month,
		SUM(fis.SalesAmount) AS MonthlySales
	FROM dbo.FactInternetSales fis
	INNER JOIN dbo.DimDate dd ON fis.OrderDateKey = dd.DateKey
	GROUP BY dd.CalendarYear, dd.MonthNumberOfYear, dd.EnglishMonthName
),
MovingAverage AS (
	-- Step 2: Calculate 3-month moving average of sales
	SELECT
		CalendarYear,
		MonthID,
		Month,
		MonthlySales,
		AVG(MonthlySales) OVER (ORDER BY CalendarYear, MonthID ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS MovingAvg3Month,
		COUNT(MonthID) OVER (ORDER BY CalendarYear, MonthID ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS NumOfMonths
	FROM MonthlySales
)
SELECT
	CalendarYear,
	Month,
	FORMAT(MonthlySales, 'C0') AS MonthlySales,
	FORMAT(MovingAvg3Month, 'C0') AS MovingAvg3Month,
	NumOfMonths
FROM MovingAverage
ORDER BY CalendarYear, MonthID;



/* 
8.	Year-to-Date (YTD) Sales - Calculate YTD sales for each product, 
resetting at the start of each calendar year.
*/
WITH MonthlySales AS (
	-- Step 1: Calculate total sales by calendar year, month, and product
	SELECT 
		dd.CalendarYear,
		dd.MonthNumberOfYear AS MonthID,
		dd.EnglishMonthName AS Month,
		p.ProductKey,
		SUM(fis.SalesAmount) AS MonthlySales
	FROM dbo.FactInternetSales fis
	INNER JOIN dbo.DimDate dd ON fis.OrderDateKey = dd.DateKey
	INNER JOIN dbo.DimProduct p ON fis.ProductKey = p.ProductKey
	GROUP BY dd.CalendarYear, dd.MonthNumberOfYear, dd.EnglishMonthName, p.ProductKey
),
YTDSales AS (
	-- Step 2: Calculate YTD sales for each product, resetting at the start of each calendar year
	SELECT 
		CalendarYear,
		MonthID,
		Month,
		ProductKey,
		MonthlySales,
		SUM(MonthlySales) OVER (PARTITION BY CalendarYear, ProductKey ORDER BY MonthID) AS YTDSales
	FROM MonthlySales
)
SELECT
	CalendarYear,
	Month,
	p.EnglishProductName AS Product,
	FORMAT(MonthlySales, 'C0') AS MonthlySales,
	FORMAT(YTDSales, 'C0') AS YTDSales
FROM YTDSales s
INNER JOIN dbo.DimProduct p ON s.ProductKey = p.ProductKey
ORDER BY CalendarYear, Product, MonthID;

