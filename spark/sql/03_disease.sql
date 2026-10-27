-- 模块3：慢性病类型、严重程度、共病与年度确诊趋势
USE chronic_disease_db;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m3/disease_dist'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT d.disease_type,
       COUNT(*) AS record_count,
       COUNT(DISTINCT d.patient_id) AS patient_count,
       ROUND(COUNT(DISTINCT d.patient_id) * 100.0 /
             (SELECT COUNT(DISTINCT patient_id) FROM dwd_disease_clean), 2) AS percentage,
       SUM(CASE WHEN d.severity = '重度' THEN 1 ELSE 0 END) AS severe_count,
       ROUND(SUM(CASE WHEN d.severity = '重度' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS severe_rate
FROM dwd_disease_clean d
JOIN dwd_patient_clean p ON d.patient_id = p.patient_id
GROUP BY d.disease_type
ORDER BY patient_count DESC;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m3/severity'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT disease_type, severity, COUNT(*) AS record_count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY disease_type), 2) AS percentage
FROM dwd_disease_clean
GROUP BY disease_type, severity
ORDER BY disease_type, severity;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m3/comorbidity'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT disease_count, patient_count,
       ROUND(patient_count * 100.0 / SUM(patient_count) OVER (), 2) AS percentage
FROM (
  SELECT patient_id, COUNT(DISTINCT disease_type) AS disease_count
  FROM dwd_disease_clean GROUP BY patient_id
) t
GROUP BY disease_count
ORDER BY disease_count;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m3/disease_year'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT YEAR(TO_DATE(diagnose_date)) AS year, disease_type, COUNT(*) AS cases
FROM dwd_disease_clean
GROUP BY YEAR(TO_DATE(diagnose_date)), disease_type
ORDER BY year, cases DESC;
