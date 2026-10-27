-- Hive DWD 层：清洗后的明细宽表（Parquet）
USE chronic_disease_db;

DROP TABLE IF EXISTS dwd_patient_clean;
CREATE TABLE dwd_patient_clean (
  patient_id INT, gender STRING, age INT, province STRING, city STRING,
  create_time STRING, age_group STRING
) STORED AS PARQUET;

DROP TABLE IF EXISTS dwd_checkup_clean;
CREATE TABLE dwd_checkup_clean (
  checkup_id INT, patient_id INT, checkup_date STRING, sbp INT, dbp INT,
  fasting_glucose DOUBLE, hba1c DOUBLE, tc DOUBLE, tg DOUBLE, hdl DOUBLE,
  ldl DOUBLE, bmi DOUBLE, heart_rate INT, creatinine DOUBLE, uric_acid DOUBLE,
  bp_level STRING, glucose_level STRING, bmi_level STRING
) STORED AS PARQUET;

DROP TABLE IF EXISTS dwd_disease_clean;
CREATE TABLE dwd_disease_clean (
  record_id INT, patient_id INT, disease_type STRING, disease_name STRING,
  diagnose_date STRING, severity STRING, doctor_id INT, hospital STRING
) STORED AS PARQUET;

DROP TABLE IF EXISTS dwd_lifestyle_clean;
CREATE TABLE dwd_lifestyle_clean (
  lifestyle_id INT, patient_id INT, smoking_status STRING, smoking_amount INT,
  drinking_status STRING, exercise_freq STRING, sleep_hours DOUBLE, diet_pattern STRING
) STORED AS PARQUET;

DROP TABLE IF EXISTS dwd_visit_clean;
CREATE TABLE dwd_visit_clean (
  visit_id INT, patient_id INT, visit_date STRING, visit_type STRING,
  hospital STRING, department STRING, diagnosis STRING, cost DOUBLE,
  insurance_pay DOUBLE, self_pay DOUBLE, stay_days INT
) STORED AS PARQUET;

DROP TABLE IF EXISTS dwd_medication_clean;
CREATE TABLE dwd_medication_clean (
  med_id INT, patient_id INT, drug_name STRING, drug_type STRING, dosage STRING,
  start_date STRING, end_date STRING, cost DOUBLE, is_effective STRING
) STORED AS PARQUET;

DROP TABLE IF EXISTS dwd_follow_up_clean;
CREATE TABLE dwd_follow_up_clean (
  follow_id INT, patient_id INT, follow_date STRING, follow_type STRING,
  symptom_status STRING, medication_adherence STRING, doctor_advice STRING,
  next_follow_date STRING
) STORED AS PARQUET;
