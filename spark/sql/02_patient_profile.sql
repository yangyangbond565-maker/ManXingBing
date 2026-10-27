-- 模块2：患者人群画像（性别、年龄、省份、年龄×性别）
USE chronic_disease_db;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m2/patient_profile'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT 'gender' AS dimension_type, gender AS dimension_value,
       COUNT(*) AS patient_count,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage,
       CAST(ROUND(AVG(age), 1) AS DOUBLE) AS avg_age,
       CAST(NULL AS STRING) AS extra_value
FROM dwd_patient_clean GROUP BY gender
UNION ALL
SELECT 'age', age_group, COUNT(*),
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2),
       CAST(ROUND(AVG(age), 1) AS DOUBLE), CAST(NULL AS STRING)
FROM dwd_patient_clean GROUP BY age_group
UNION ALL
SELECT 'province', province, COUNT(*),
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2),
       CAST(ROUND(AVG(age), 1) AS DOUBLE), CAST(NULL AS STRING)
FROM dwd_patient_clean GROUP BY province
UNION ALL
SELECT 'age_gender', age_group, COUNT(*),
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2),
       CAST(ROUND(AVG(age), 1) AS DOUBLE), gender
FROM dwd_patient_clean GROUP BY age_group, gender;
