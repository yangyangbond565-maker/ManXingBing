-- Hive 数仓 ODS 层：7 张业务表对应的外部表
-- 数据由 scripts/sync_mysql_to_hive.py 以 TSV 上传到 HDFS。
CREATE DATABASE IF NOT EXISTS chronic_disease_db;
USE chronic_disease_db;

DROP TABLE IF EXISTS ods_patient_info;
CREATE EXTERNAL TABLE ods_patient_info (
  patient_id INT, gender STRING, age INT, province STRING, city STRING,
  id_number STRING, phone STRING, create_time STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ods/patient_info';

DROP TABLE IF EXISTS ods_disease_record;
CREATE EXTERNAL TABLE ods_disease_record (
  record_id INT, patient_id INT, disease_type STRING, disease_name STRING,
  diagnose_date STRING, severity STRING, doctor_id INT, hospital STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ods/disease_record';

DROP TABLE IF EXISTS ods_health_checkup;
CREATE EXTERNAL TABLE ods_health_checkup (
  checkup_id INT, patient_id INT, checkup_date STRING, sbp INT, dbp INT,
  fasting_glucose DOUBLE, hba1c DOUBLE, tc DOUBLE, tg DOUBLE, hdl DOUBLE,
  ldl DOUBLE, bmi DOUBLE, heart_rate INT, creatinine DOUBLE, uric_acid DOUBLE
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ods/health_checkup';

DROP TABLE IF EXISTS ods_lifestyle;
CREATE EXTERNAL TABLE ods_lifestyle (
  lifestyle_id INT, patient_id INT, smoking_status STRING, smoking_amount INT,
  drinking_status STRING, exercise_freq STRING, sleep_hours DOUBLE, diet_pattern STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ods/lifestyle';

DROP TABLE IF EXISTS ods_visit_record;
CREATE EXTERNAL TABLE ods_visit_record (
  visit_id INT, patient_id INT, visit_date STRING, visit_type STRING,
  hospital STRING, department STRING, diagnosis STRING, cost DOUBLE,
  insurance_pay DOUBLE, self_pay DOUBLE, stay_days INT
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ods/visit_record';

DROP TABLE IF EXISTS ods_medication_record;
CREATE EXTERNAL TABLE ods_medication_record (
  med_id INT, patient_id INT, drug_name STRING, drug_type STRING, dosage STRING,
  start_date STRING, end_date STRING, cost DOUBLE, is_effective STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ods/medication_record';

DROP TABLE IF EXISTS ods_follow_up;
CREATE EXTERNAL TABLE ods_follow_up (
  follow_id INT, patient_id INT, follow_date STRING, follow_type STRING,
  symptom_status STRING, medication_adherence STRING, doctor_advice STRING,
  next_follow_date STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ods/follow_up';
