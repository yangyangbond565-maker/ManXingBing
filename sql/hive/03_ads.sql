-- Hive ADS 层：Spark SQL 结果的外部表（TSV，首行表头跳过）
USE chronic_disease_db;

DROP TABLE IF EXISTS ads_patient_profile;
CREATE EXTERNAL TABLE ads_patient_profile (
  dimension_type STRING, dimension_value STRING, patient_count INT,
  percentage DOUBLE, avg_age DOUBLE, extra_value STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/patient_profile'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_disease_dist;
CREATE EXTERNAL TABLE ads_disease_dist (
  disease_type STRING, record_count INT, patient_count INT,
  percentage DOUBLE, severe_count INT, severe_rate DOUBLE
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/disease_dist'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_severity;
CREATE EXTERNAL TABLE ads_severity (
  disease_type STRING, severity STRING, record_count INT, percentage DOUBLE
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/severity'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_comorbidity;
CREATE EXTERNAL TABLE ads_comorbidity (
  disease_count INT, patient_count INT, percentage DOUBLE
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/comorbidity'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_drug_by_disease;
CREATE EXTERNAL TABLE ads_drug_by_disease (
  disease_type STRING, drug_name STRING, usage_count INT, rank_no INT
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/drug_by_disease'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_risk_factor;
CREATE EXTERNAL TABLE ads_risk_factor (
  factor_type STRING, factor_value STRING, disease_type STRING,
  patient_count INT, exposure_rate DOUBLE, avg_sbp DOUBLE,
  avg_glucose DOUBLE, avg_bmi DOUBLE
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/risk_factor'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_visit_analysis;
CREATE EXTERNAL TABLE ads_visit_analysis (
  analysis_type STRING, dimension_value STRING, visit_count INT, patient_count INT,
  avg_cost DOUBLE, total_cost DOUBLE, avg_reimbursement_rate DOUBLE, avg_stay_days DOUBLE
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/visit_analysis'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_medication_analysis;
CREATE EXTERNAL TABLE ads_medication_analysis (
  analysis_type STRING, dimension_value STRING, usage_count INT, patient_count INT,
  avg_cost DOUBLE, effective_rate DOUBLE, rank_no INT
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/medication_analysis'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_trend;
CREATE EXTERNAL TABLE ads_trend (
  grain STRING, period STRING, disease_type STRING, cases INT,
  predicted_cases DOUBLE, slope DOUBLE, intercept DOUBLE, r2 DOUBLE,
  trend STRING, is_forecast INT
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/trend'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_health_score;
CREATE EXTERNAL TABLE ads_health_score (
  patient_id INT, gender STRING, age INT, age_group STRING, province STRING,
  bp_score INT, glucose_score INT, bmi_score INT, lipid_score INT, hr_score INT,
  smoking_score INT, drinking_score INT, exercise_score INT,
  health_score DOUBLE, health_level STRING, scored_at STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/health_score'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_health_level;
CREATE EXTERNAL TABLE ads_health_level (
  level STRING, patient_count INT, avg_score DOUBLE, percentage DOUBLE, sort_no INT
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/health_level'
TBLPROPERTIES ('skip.header.line.count'='1');

DROP TABLE IF EXISTS ads_overview;
CREATE EXTERNAL TABLE ads_overview (
  total_patients INT, total_disease_records BIGINT, total_visits BIGINT,
  total_medications BIGINT, total_followups BIGINT, avg_health_score DOUBLE,
  high_risk_count INT, high_risk_rate DOUBLE, total_cost DOUBLE,
  avg_cost DOUBLE, data_start_year INT, data_end_year INT, updated_at STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/warehouse/chronic_disease/ads/overview'
TBLPROPERTIES ('skip.header.line.count'='1');