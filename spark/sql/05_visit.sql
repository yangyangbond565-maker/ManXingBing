-- 模块5：就诊类型、费用、医保、科室与年度就诊趋势
USE chronic_disease_db;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m5/visit_analysis'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT 'type' AS analysis_type, visit_type AS dimension_value,
       COUNT(*) AS visit_count, COUNT(DISTINCT patient_id) AS patient_count,
       ROUND(AVG(cost), 2) AS avg_cost, ROUND(SUM(cost), 2) AS total_cost,
       ROUND(AVG(CASE WHEN cost > 0 THEN insurance_pay * 100.0 / cost ELSE 0 END), 2) AS avg_reimbursement_rate,
       ROUND(AVG(stay_days), 1) AS avg_stay_days
FROM dwd_visit_clean GROUP BY visit_type
UNION ALL
SELECT 'department', department, COUNT(*), COUNT(DISTINCT patient_id),
       ROUND(AVG(cost), 2), ROUND(SUM(cost), 2),
       ROUND(AVG(CASE WHEN cost > 0 THEN insurance_pay * 100.0 / cost ELSE 0 END), 2),
       ROUND(AVG(stay_days), 1)
FROM dwd_visit_clean GROUP BY department
UNION ALL
SELECT 'year', CAST(YEAR(TO_DATE(visit_date)) AS STRING), COUNT(*), COUNT(DISTINCT patient_id),
       ROUND(AVG(cost), 2), ROUND(SUM(cost), 2),
       ROUND(AVG(CASE WHEN cost > 0 THEN insurance_pay * 100.0 / cost ELSE 0 END), 2),
       ROUND(AVG(stay_days), 1)
FROM dwd_visit_clean GROUP BY YEAR(TO_DATE(visit_date));
