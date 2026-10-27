-- 模块1：数据清洗与预处理
-- 输出：DWD 清洗明细 + 清洗前后记录数报告
USE chronic_disease_db;

INSERT OVERWRITE TABLE dwd_patient_clean
SELECT patient_id, gender, age, province, city, create_time,
       CASE WHEN age < 30 THEN '青年(<30)'
            WHEN age < 45 THEN '中青年(30-44)'
            WHEN age < 60 THEN '中年(45-59)'
            WHEN age < 75 THEN '中老年(60-74)'
            ELSE '老年(75+)' END AS age_group
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY create_time DESC) rn
  FROM ods_patient_info
  WHERE patient_id IS NOT NULL AND gender IS NOT NULL AND age BETWEEN 0 AND 120
) t WHERE rn = 1;

INSERT OVERWRITE TABLE dwd_checkup_clean
SELECT checkup_id, patient_id, checkup_date, sbp, dbp, fasting_glucose, hba1c,
       tc, tg, hdl, ldl, bmi, heart_rate, creatinine, uric_acid,
       CASE WHEN sbp < 120 AND dbp < 80 THEN '正常'
            WHEN sbp < 140 AND dbp < 90 THEN '正常高值'
            WHEN sbp < 160 OR dbp < 100 THEN '1级高血压'
            WHEN sbp < 180 OR dbp < 110 THEN '2级高血压'
            ELSE '3级高血压' END AS bp_level,
       CASE WHEN fasting_glucose < 6.1 THEN '正常'
            WHEN fasting_glucose < 7.0 THEN '空腹血糖受损'
            ELSE '糖尿病' END AS glucose_level,
       CASE WHEN bmi < 18.5 THEN '偏瘦'
            WHEN bmi < 24.0 THEN '正常'
            WHEN bmi < 28.0 THEN '超重'
            ELSE '肥胖' END AS bmi_level
FROM ods_health_checkup
WHERE patient_id IS NOT NULL
  AND sbp BETWEEN 60 AND 300 AND dbp BETWEEN 30 AND 200
  AND fasting_glucose BETWEEN 1.0 AND 40.0
  AND bmi BETWEEN 12.0 AND 50.0
  AND heart_rate BETWEEN 30 AND 220
  AND sbp > dbp;

INSERT OVERWRITE TABLE dwd_disease_clean
SELECT record_id, patient_id, disease_type, disease_name, diagnose_date,
       severity, doctor_id, hospital
FROM ods_disease_record
WHERE patient_id IS NOT NULL AND disease_type IS NOT NULL
  AND diagnose_date IS NOT NULL AND severity IN ('轻度','中度','重度');

INSERT OVERWRITE TABLE dwd_lifestyle_clean
SELECT lifestyle_id, patient_id, smoking_status, smoking_amount, drinking_status,
       exercise_freq, sleep_hours, diet_pattern
FROM ods_lifestyle
WHERE patient_id IS NOT NULL;

INSERT OVERWRITE TABLE dwd_visit_clean
SELECT visit_id, patient_id, visit_date, visit_type, hospital, department,
       diagnosis, cost, insurance_pay, self_pay, stay_days
FROM ods_visit_record
WHERE patient_id IS NOT NULL AND visit_type IN ('门诊','急诊','住院')
  AND cost >= 0 AND ABS(cost - insurance_pay - self_pay) < 0.01;

INSERT OVERWRITE TABLE dwd_medication_clean
SELECT med_id, patient_id, drug_name, drug_type, dosage, start_date, end_date,
       cost, is_effective
FROM ods_medication_record
WHERE patient_id IS NOT NULL AND end_date >= start_date;

INSERT OVERWRITE TABLE dwd_follow_up_clean
SELECT follow_id, patient_id, follow_date, follow_type, symptom_status,
       medication_adherence, doctor_advice, next_follow_date
FROM ods_follow_up
WHERE patient_id IS NOT NULL AND next_follow_date >= follow_date;

INSERT OVERWRITE DIRECTORY '${ADS_BASE}/m1/clean_report'
USING csv OPTIONS ('header'='true', 'sep'='\t')
SELECT 'patient_info' AS table_name,
       (SELECT COUNT(*) FROM ods_patient_info) AS before_count,
       (SELECT COUNT(*) FROM dwd_patient_clean) AS after_count,
       (SELECT COUNT(*) FROM ods_patient_info) - (SELECT COUNT(*) FROM dwd_patient_clean) AS removed_count
UNION ALL
SELECT 'health_checkup',
       (SELECT COUNT(*) FROM ods_health_checkup),
       (SELECT COUNT(*) FROM dwd_checkup_clean),
       (SELECT COUNT(*) FROM ods_health_checkup) - (SELECT COUNT(*) FROM dwd_checkup_clean);
