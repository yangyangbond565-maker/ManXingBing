-- 模块8：健康评分（0-100）与分级
-- 权重：血压20% + 血糖20% + BMI15% + 血脂15% + 心率10% + 吸烟8% + 饮酒7% + 运动5%
-- 分级：优秀>=85，良好>=70，一般>=55，较差>=40，危险<40；高危定义：health_score<50。
USE chronic_disease_db;

CREATE OR REPLACE TEMPORARY VIEW m8_latest AS
SELECT * FROM (
  SELECT c.*, ROW_NUMBER() OVER (PARTITION BY c.patient_id ORDER BY c.checkup_date DESC) rn
  FROM dwd_checkup_clean c
) t WHERE rn = 1;

CREATE OR REPLACE TEMPORARY VIEW m8_scores AS
SELECT
  pl.patient_id, pc.gender, pc.age, pc.age_group, pc.province,
  CASE WHEN pl.bp_level='正常' THEN 100 WHEN pl.bp_level='正常高值' THEN 75
       WHEN pl.bp_level='1级高血压' THEN 50 WHEN pl.bp_level='2级高血压' THEN 30 ELSE 10 END AS bp_score,
  CASE WHEN pl.glucose_level='正常' THEN 100 WHEN pl.glucose_level='空腹血糖受损' THEN 60 ELSE 25 END AS glucose_score,
  CASE WHEN pl.bmi_level='正常' THEN 100 WHEN pl.bmi_level='偏瘦' THEN 70
       WHEN pl.bmi_level='超重' THEN 60 ELSE 30 END AS bmi_score,
  CASE WHEN pl.tc < 5.2 THEN 100 WHEN pl.tc < 6.2 THEN 70 WHEN pl.tc < 7.2 THEN 40 ELSE 20 END AS lipid_score,
  CASE WHEN pl.heart_rate BETWEEN 60 AND 80 THEN 100
       WHEN pl.heart_rate BETWEEN 50 AND 100 THEN 75 ELSE 40 END AS hr_score,
  CASE WHEN ls.smoking_status='从不' THEN 100 WHEN ls.smoking_status='已戒' THEN 80 ELSE 30 END AS smoking_score,
  CASE WHEN ls.drinking_status='从不' THEN 100 WHEN ls.drinking_status='已戒' THEN 80 ELSE 40 END AS drinking_score,
  CASE WHEN ls.exercise_freq='经常' THEN 100 WHEN ls.exercise_freq='偶尔' THEN 70 ELSE 40 END AS exercise_score,
  ROUND(
    (CASE WHEN pl.bp_level='正常' THEN 100 WHEN pl.bp_level='正常高值' THEN 75
          WHEN pl.bp_level='1级高血压' THEN 50 WHEN pl.bp_level='2级高血压' THEN 30 ELSE 10 END) * 0.20 +
    (CASE WHEN pl.glucose_level='正常' THEN 100 WHEN pl.glucose_level='空腹血糖受损' THEN 60 ELSE 25 END) * 0.20 +
    (CASE WHEN pl.bmi_level='正常' THEN 100 WHEN pl.bmi_level='偏瘦' THEN 70
          WHEN pl.bmi_level='超重' THEN 60 ELSE 30 END) * 0.15 +
    (CASE WHEN pl.tc < 5.2 THEN 100 WHEN pl.tc < 6.2 THEN 70 WHEN pl.tc < 7.2 THEN 40 ELSE 20 END) * 0.15 +
    (CASE WHEN pl.heart_rate BETWEEN 60 AND 80 THEN 100
          WHEN pl.heart_rate BETWEEN 50 AND 100 THEN 75 ELSE 40 END) * 0.10 +
    (CASE WHEN ls.smoking_status='从不' THEN 100 WHEN ls.smoking_status='已戒' THEN 80 ELSE 30 END) * 0.08 +
    (CASE WHEN ls.drinking_status='从不' THEN 100 WHEN ls.drinking_status='已戒' THEN 80 ELSE 40 END) * 0.07 +
    (CASE WHEN ls.exercise_freq='经常' THEN 100 WHEN ls.exercise_freq='偶尔' THEN 70 ELSE 40 END) * 0.05
  , 1) AS health_score
FROM m8_latest pl
JOIN dwd_patient_clean pc ON pl.patient_id = pc.patient_id
JOIN dwd_lifestyle_clean ls ON pl.patient_id = ls.patient_id;

CREATE OR REPLACE TEMPORARY VIEW m8_level AS
SELECT CASE WHEN health_score >= 85 THEN '优秀'
            WHEN health_score >= 70 THEN '良好'
            WHEN health_score >= 55 THEN '一般'
            WHEN health_score >= 40 THEN '较差'
            ELSE '危险' END AS health_level,
       COUNT(*) AS patient_count, ROUND(AVG(health_score), 1) AS avg_score
FROM m8_scores GROUP BY CASE WHEN health_score >= 85 THEN '优秀'
                             WHEN health_score >= 70 THEN '良好'
                             WHEN health_score >= 55 THEN '一般'
                             WHEN health_score >= 40 THEN '较差'
                             ELSE '危险' END;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m8/health_score'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT patient_id, gender, age, age_group, province,
       bp_score, glucose_score, bmi_score, lipid_score, hr_score,
       smoking_score, drinking_score, exercise_score, health_score,
       CASE WHEN health_score >= 85 THEN '优秀'
            WHEN health_score >= 70 THEN '良好'
            WHEN health_score >= 55 THEN '一般'
            WHEN health_score >= 40 THEN '较差'
            ELSE '危险' END AS health_level
FROM m8_scores;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m8/health_level'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT health_level, patient_count, avg_score,
       ROUND(patient_count * 100.0 / SUM(patient_count) OVER (), 2) AS percentage,
       CASE health_level WHEN '优秀' THEN 1 WHEN '良好' THEN 2 WHEN '一般' THEN 3
                         WHEN '较差' THEN 4 ELSE 5 END AS sort_no
FROM m8_level;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m8/overview'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT
  (SELECT COUNT(*) FROM dwd_patient_clean) AS total_patients,
  (SELECT COUNT(*) FROM dwd_disease_clean) AS total_disease_records,
  (SELECT COUNT(*) FROM dwd_visit_clean) AS total_visits,
  (SELECT COUNT(*) FROM dwd_medication_clean) AS total_medications,
  (SELECT COUNT(*) FROM dwd_follow_up_clean) AS total_followups,
  (SELECT ROUND(AVG(health_score), 1) FROM m8_scores) AS avg_health_score,
  (SELECT COUNT(*) FROM m8_scores WHERE health_score < 50) AS high_risk_count,
  (SELECT ROUND(COUNT(CASE WHEN health_score < 50 THEN 1 END) * 100.0 / COUNT(*), 2) FROM m8_scores) AS high_risk_rate,
  (SELECT ROUND(SUM(cost), 2) FROM dwd_visit_clean) AS total_cost,
  (SELECT ROUND(AVG(cost), 2) FROM dwd_visit_clean) AS avg_cost,
  (SELECT MIN(YEAR(TO_DATE(diagnose_date))) FROM dwd_disease_clean) AS data_start_year,
  (SELECT MAX(YEAR(TO_DATE(diagnose_date))) FROM dwd_disease_clean) AS data_end_year
FROM (SELECT 1) x;
