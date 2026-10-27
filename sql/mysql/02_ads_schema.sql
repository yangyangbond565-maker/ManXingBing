-- 社区慢性病大数据分析系统 - ADS 分析结果表
-- 由 Spark SQL 输出 CSV/Parquet，经 python/chronic_disease/load_ads.py 幂等导入。
USE chronic_disease;

DROP TABLE IF EXISTS ads_module_kpi;
DROP TABLE IF EXISTS ads_drug_by_disease;
DROP TABLE IF EXISTS ads_comorbidity;
DROP TABLE IF EXISTS ads_severity;
DROP TABLE IF EXISTS ads_data_quality;
DROP TABLE IF EXISTS ads_health_level;
DROP TABLE IF EXISTS ads_health_score;
DROP TABLE IF EXISTS ads_trend;
DROP TABLE IF EXISTS ads_medication_analysis;
DROP TABLE IF EXISTS ads_visit_analysis;
DROP TABLE IF EXISTS ads_risk_factor;
DROP TABLE IF EXISTS ads_disease_dist;
DROP TABLE IF EXISTS ads_patient_profile;
DROP TABLE IF EXISTS ads_overview;
DROP TABLE IF EXISTS ads_module_run;

CREATE TABLE ads_module_run (
  run_id       BIGINT       NOT NULL AUTO_INCREMENT,
  module_code  VARCHAR(20)  NOT NULL,
  module_name  VARCHAR(50)  NOT NULL,
  status       VARCHAR(20)  NOT NULL,
  row_count    BIGINT       NOT NULL DEFAULT 0,
  started_at   DATETIME     NULL,
  finished_at  DATETIME     NULL,
  detail       VARCHAR(500) NULL,
  PRIMARY KEY (run_id),
  KEY idx_run_module (module_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分析任务运行记录';

CREATE TABLE ads_overview (
  id                  TINYINT       NOT NULL DEFAULT 1,
  total_patients      INT           NOT NULL,
  total_disease_records BIGINT      NOT NULL,
  total_visits        BIGINT        NOT NULL,
  total_medications   BIGINT        NOT NULL,
  total_followups     BIGINT        NOT NULL,
  avg_health_score    DECIMAL(5,1)  NOT NULL,
  high_risk_count     INT           NOT NULL,
  high_risk_rate      DECIMAL(5,2)  NOT NULL,
  total_cost          DECIMAL(14,2) NOT NULL,
  avg_cost            DECIMAL(10,2) NOT NULL,
  data_start_year     INT           NOT NULL,
  data_end_year       INT           NOT NULL,
  updated_at          DATETIME      NOT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='大屏总体指标';

CREATE TABLE ads_patient_profile (
  id              BIGINT       NOT NULL AUTO_INCREMENT,
  dimension_type  VARCHAR(30)  NOT NULL COMMENT 'gender/age/province/age_gender',
  dimension_value VARCHAR(50)  NOT NULL,
  patient_count   INT          NOT NULL,
  percentage      DECIMAL(5,2) NOT NULL,
  avg_age         DECIMAL(5,1) NULL,
  extra_value     VARCHAR(50)  NULL,
  PRIMARY KEY (id),
  KEY idx_profile_dim (dimension_type, dimension_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者画像结果';

CREATE TABLE ads_disease_dist (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  disease_type  VARCHAR(30)  NOT NULL,
  record_count  INT          NOT NULL,
  patient_count INT          NOT NULL,
  percentage    DECIMAL(5,2) NOT NULL,
  severe_count  INT          NOT NULL DEFAULT 0,
  severe_rate   DECIMAL(5,2) NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_disease_type (disease_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病分布结果';

CREATE TABLE ads_severity (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  disease_type  VARCHAR(30)  NOT NULL,
  severity      VARCHAR(10)  NOT NULL,
  record_count  INT          NOT NULL,
  percentage    DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_severity (disease_type, severity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病严重程度分布';

CREATE TABLE ads_comorbidity (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  disease_count INT          NOT NULL,
  patient_count INT          NOT NULL,
  percentage    DECIMAL(5,2) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_comorbidity_count (disease_count)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='共病数量分布';

CREATE TABLE ads_drug_by_disease (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  disease_type  VARCHAR(30)  NOT NULL,
  drug_name     VARCHAR(50)  NOT NULL,
  usage_count   INT          NOT NULL,
  rank_no       INT          NOT NULL,
  PRIMARY KEY (id),
  KEY idx_drug_disease (disease_type, rank_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='各疾病常用药 TOP3';

CREATE TABLE ads_risk_factor (
  id             BIGINT       NOT NULL AUTO_INCREMENT,
  factor_type    VARCHAR(30)  NOT NULL COMMENT 'smoking/drinking/bmi/exercise/diet',
  factor_value   VARCHAR(30)  NOT NULL,
  disease_type   VARCHAR(30)  NOT NULL,
  patient_count  INT          NOT NULL,
  exposure_rate  DECIMAL(5,2) NOT NULL,
  avg_sbp        DECIMAL(6,1) NULL,
  avg_glucose    DECIMAL(6,2) NULL,
  avg_bmi        DECIMAL(5,2) NULL,
  PRIMARY KEY (id),
  KEY idx_risk_factor (factor_type, factor_value, disease_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='风险因素关联结果';

CREATE TABLE ads_visit_analysis (
  id                    BIGINT       NOT NULL AUTO_INCREMENT,
  analysis_type         VARCHAR(30)  NOT NULL COMMENT 'type/cost/dept/year/insurance',
  dimension_value       VARCHAR(50)  NOT NULL,
  visit_count           INT          NOT NULL,
  patient_count         INT          NOT NULL,
  avg_cost              DECIMAL(10,2) NULL,
  total_cost            DECIMAL(14,2) NULL,
  avg_reimbursement_rate DECIMAL(5,2) NULL,
  avg_stay_days          DECIMAL(5,1) NULL,
  PRIMARY KEY (id),
  KEY idx_visit_analysis (analysis_type, dimension_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='就诊行为结果';

CREATE TABLE ads_medication_analysis (
  id              BIGINT       NOT NULL AUTO_INCREMENT,
  analysis_type   VARCHAR(30)  NOT NULL COMMENT 'top/type/effective/combo/disease',
  dimension_value VARCHAR(80)  NOT NULL,
  usage_count     INT          NOT NULL,
  patient_count   INT          NOT NULL,
  avg_cost        DECIMAL(10,2) NULL,
  effective_rate  DECIMAL(5,2) NULL,
  rank_no         INT          NULL,
  PRIMARY KEY (id),
  KEY idx_med_analysis (analysis_type, dimension_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用药分析结果';

CREATE TABLE ads_trend (
  id              BIGINT       NOT NULL AUTO_INCREMENT,
  grain           VARCHAR(20)  NOT NULL COMMENT 'year/month/year_disease',
  period          VARCHAR(10)  NOT NULL,
  disease_type    VARCHAR(30)  NOT NULL DEFAULT '全部',
  cases           INT          NOT NULL,
  predicted_cases DECIMAL(12,1) NULL,
  slope           DECIMAL(12,4) NULL,
  intercept       DECIMAL(14,4) NULL,
  r2              DECIMAL(6,4) NULL,
  trend           VARCHAR(10)  NULL,
  is_forecast     TINYINT      NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_trend_grain (grain, period)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='疾病趋势与线性预测结果';

CREATE TABLE ads_health_score (
  patient_id      INT          NOT NULL,
  gender          VARCHAR(4)   NOT NULL,
  age             INT          NOT NULL,
  age_group       VARCHAR(20)  NOT NULL,
  province        VARCHAR(20)  NOT NULL,
  bp_score        INT          NOT NULL,
  glucose_score   INT          NOT NULL,
  bmi_score       INT          NOT NULL,
  lipid_score     INT          NOT NULL,
  hr_score        INT          NOT NULL,
  smoking_score   INT          NOT NULL,
  drinking_score  INT          NOT NULL,
  exercise_score  INT          NOT NULL,
  health_score    DECIMAL(5,1) NOT NULL,
  health_level    VARCHAR(10)  NOT NULL,
  scored_at       DATETIME     NOT NULL,
  PRIMARY KEY (patient_id),
  KEY idx_hs_score (health_score),
  KEY idx_hs_level (health_level),
  CONSTRAINT fk_hs_patient FOREIGN KEY (patient_id) REFERENCES patient_info(patient_id)
    ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT chk_hs_range CHECK (health_score BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者健康评分（0-100）';

CREATE TABLE ads_health_level (
  level         VARCHAR(10)  NOT NULL,
  patient_count INT          NOT NULL,
  avg_score     DECIMAL(5,1) NOT NULL,
  percentage    DECIMAL(5,2) NOT NULL,
  sort_no       INT          NOT NULL,
  PRIMARY KEY (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康等级分布';

CREATE TABLE ads_data_quality (
  table_name    VARCHAR(40)  NOT NULL,
  before_count  BIGINT       NOT NULL,
  after_count   BIGINT       NOT NULL,
  removed_count BIGINT       NOT NULL,
  null_issues   BIGINT       NOT NULL DEFAULT 0,
  dup_issues    BIGINT       NOT NULL DEFAULT 0,
  orphan_issues BIGINT       NOT NULL DEFAULT 0,
  invalid_issues BIGINT      NOT NULL DEFAULT 0,
  status        VARCHAR(10)  NOT NULL,
  checked_at    DATETIME     NOT NULL,
  PRIMARY KEY (table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据质量结果';

CREATE TABLE ads_module_kpi (
  module_code VARCHAR(20)  NOT NULL,
  kpi_name    VARCHAR(50)  NOT NULL,
  kpi_value   DECIMAL(14,2) NULL,
  kpi_text    VARCHAR(100) NULL,
  updated_at  DATETIME     NOT NULL,
  PRIMARY KEY (module_code, kpi_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='模块 KPI 汇总';
