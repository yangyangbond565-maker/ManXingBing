-- 模块4：吸烟、饮酒、BMI、运动、饮食与疾病/指标的关联
USE chronic_disease_db;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m4/risk_factor'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT 'smoking' AS factor_type, factor_value, disease_type, patient_count,
       ROUND(patient_count * 100.0 / SUM(patient_count) OVER (PARTITION BY disease_type), 2) AS exposure_rate,
       CAST(NULL AS DOUBLE) AS avg_sbp, CAST(NULL AS DOUBLE) AS avg_glucose, CAST(NULL AS DOUBLE) AS avg_bmi
FROM (
  SELECT l.smoking_status AS factor_value, d.disease_type,
         COUNT(DISTINCT l.patient_id) AS patient_count
  FROM dwd_lifestyle l JOIN dwd_disease_clean d ON l.patient_id = d.patient_id
  GROUP BY l.smoking_status, d.disease_type
) smoking
UNION ALL
SELECT 'drinking', factor_value, disease_type, patient_count,
       ROUND(patient_count * 100.0 / SUM(patient_count) OVER (PARTITION BY disease_type), 2),
       CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE), CAST(NULL AS DOUBLE)
FROM (
  SELECT l.drinking_status AS factor_value, d.disease_type,
         COUNT(DISTINCT l.patient_id) AS patient_count
  FROM dwd_lifestyle l JOIN dwd_disease_clean d ON l.patient_id = d.patient_id
  GROUP BY l.drinking_status, d.disease_type
) x
UNION ALL
SELECT 'bmi', c.bmi_level, '全部', COUNT(*),
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2),
       ROUND(AVG(c.sbp), 1), ROUND(AVG(c.fasting_glucose), 2), ROUND(AVG(c.bmi), 2)
FROM dwd_checkup_clean c GROUP BY c.bmi_level
UNION ALL
SELECT 'exercise', l.exercise_freq, '全部', COUNT(*),
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2),
       ROUND(AVG(c.sbp), 1), ROUND(AVG(c.fasting_glucose), 2), ROUND(AVG(c.bmi), 2)
FROM dwd_lifestyle l JOIN dwd_checkup_clean c ON l.patient_id = c.patient_id
GROUP BY l.exercise_freq
UNION ALL
SELECT 'diet', l.diet_pattern, '全部', COUNT(*),
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2),
       ROUND(AVG(c.sbp), 1), ROUND(AVG(c.fasting_glucose), 2), ROUND(AVG(c.bmi), 2)
FROM dwd_lifestyle l JOIN dwd_checkup_clean c ON l.patient_id = c.patient_id
GROUP BY l.diet_pattern;
