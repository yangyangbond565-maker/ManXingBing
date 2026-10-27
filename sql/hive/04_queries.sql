-- Hive 查询验证示例（Linux 集群）
USE chronic_disease_db;

-- 1. ODS 行数
SELECT 'ods_patient_info' AS table_name, COUNT(*) AS rows FROM ods_patient_info
UNION ALL SELECT 'ods_disease_record', COUNT(*) FROM ods_disease_record
UNION ALL SELECT 'ods_health_checkup', COUNT(*) FROM ods_health_checkup
UNION ALL SELECT 'ods_lifestyle', COUNT(*) FROM ods_lifestyle
UNION ALL SELECT 'ods_visit_record', COUNT(*) FROM ods_visit_record
UNION ALL SELECT 'ods_medication_record', COUNT(*) FROM ods_medication_record
UNION ALL SELECT 'ods_follow_up', COUNT(*) FROM ods_follow_up;

-- 2. 疾病 TOP
SELECT disease_type, COUNT(*) AS records, COUNT(DISTINCT patient_id) AS patients
FROM ods_disease_record
GROUP BY disease_type
ORDER BY patients DESC;

-- 3. 年度确诊
SELECT YEAR(TO_DATE(diagnose_date)) AS year, COUNT(*) AS cases
FROM ods_disease_record
GROUP BY YEAR(TO_DATE(diagnose_date))
ORDER BY year;

-- 4. 健康评分等级（ADS）
SELECT health_level, COUNT(*) AS patients, ROUND(AVG(health_score),1) AS avg_score
FROM ads_health_score
GROUP BY health_level
ORDER BY avg_score DESC;

-- 5. 趋势预测（ADS）
SELECT period, disease_type, cases, predicted_cases, slope, intercept, r2, trend
FROM ads_trend
WHERE grain='year' AND disease_type='全部'
ORDER BY period;
