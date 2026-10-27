-- 模块7：疾病趋势与线性回归预测（年度粒度，2018-2025 训练，2026-2029 预测）
-- 算法：最小二乘一元线性回归 y = slope * year + intercept；R² 为决定系数。
USE chronic_disease_db;

CREATE OR REPLACE TEMPORARY VIEW m7_yearly AS
SELECT YEAR(TO_DATE(diagnose_date)) AS year, COUNT(*) AS cases
FROM dwd_disease_clean
GROUP BY YEAR(TO_DATE(diagnose_date));

CREATE OR REPLACE TEMPORARY VIEW m7_stats AS
SELECT COUNT(*) AS n,
       SUM(CAST(year AS DOUBLE)) AS sx,
       SUM(CAST(cases AS DOUBLE)) AS sy,
       SUM(CAST(year AS DOUBLE) * CAST(cases AS DOUBLE)) AS sxy,
       SUM(CAST(year AS DOUBLE) * CAST(year AS DOUBLE)) AS sx2,
       AVG(CAST(cases AS DOUBLE)) AS ymean
FROM m7_yearly;

CREATE OR REPLACE TEMPORARY VIEW m7_fit AS
SELECT n, sx, sy, sxy, sx2, ymean,
       (n * sxy - sx * sy) / (n * sx2 - sx * sx) AS slope,
       (sy - ((n * sxy - sx * sy) / (n * sx2 - sx * sx)) * sx) / n AS intercept
FROM m7_stats;

CREATE OR REPLACE TEMPORARY VIEW m7_r2 AS
SELECT 1 - SUM(POWER(CAST(y.cases AS DOUBLE) - (f.slope * y.year + f.intercept), 2)) /
           SUM(POWER(CAST(y.cases AS DOUBLE) - f.ymean, 2)) AS r2
FROM m7_yearly y CROSS JOIN m7_fit f
GROUP BY f.slope, f.intercept, f.ymean;

CREATE OR REPLACE TEMPORARY VIEW m7_month AS
SELECT DATE_FORMAT(TO_DATE(diagnose_date), 'yyyy-MM') AS year_month, COUNT(*) AS cases
FROM dwd_disease_clean
GROUP BY DATE_FORMAT(TO_DATE(diagnose_date), 'yyyy-MM');

CREATE OR REPLACE TEMPORARY VIEW m7_year_disease AS
SELECT YEAR(TO_DATE(diagnose_date)) AS year, disease_type, COUNT(*) AS cases
FROM dwd_disease_clean
GROUP BY YEAR(TO_DATE(diagnose_date)), disease_type;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m7/trend'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT 'year' AS grain, CAST(y.year AS STRING) AS period, '全部' AS disease_type,
       CAST(y.cases AS INT) AS cases,
       ROUND(f.slope * y.year + f.intercept, 1) AS predicted_cases,
       ROUND(f.slope, 4) AS slope, ROUND(f.intercept, 4) AS intercept, ROUND(r.r2, 4) AS r2,
       CASE WHEN f.slope > 0 THEN '上升' ELSE '下降' END AS trend, 0 AS is_forecast
FROM m7_yearly y CROSS JOIN m7_fit f CROSS JOIN m7_r2 r
UNION ALL
SELECT 'year', CAST(x.yr AS STRING), '全部', 0,
       ROUND(f.slope * x.yr + f.intercept, 1),
       ROUND(f.slope, 4), ROUND(f.intercept, 4), ROUND(r.r2, 4),
       CASE WHEN f.slope > 0 THEN '上升' ELSE '下降' END, 1
FROM (SELECT 2026 AS yr UNION ALL SELECT 2027 UNION ALL SELECT 2028 UNION ALL SELECT 2029) x
CROSS JOIN m7_fit f CROSS JOIN m7_r2 r
UNION ALL
SELECT 'month', year_month, '全部', CAST(cases AS INT),
       CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE),
       CAST(NULL AS STRING), 0
FROM m7_month
UNION ALL
SELECT 'year_disease', CAST(year AS STRING), disease_type, CAST(cases AS INT),
       CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE),
       CAST(NULL AS STRING), 0
FROM m7_year_disease;
