-- 社区慢性病大数据分析系统 - MySQL 业务库建表脚本
-- 版本: 1.0  适用: MySQL 8.0+
-- 说明: 7 张业务表，字段口径来自飞书需求文档；在原文档基础上补充主外键、检查约束与查询索引。
CREATE DATABASE IF NOT EXISTS chronic_disease
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE chronic_disease;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS follow_up;
DROP TABLE IF EXISTS medication_record;
DROP TABLE IF EXISTS visit_record;
DROP TABLE IF EXISTS lifestyle;
DROP TABLE IF EXISTS health_checkup;
DROP TABLE IF EXISTS disease_record;
DROP TABLE IF EXISTS patient_info;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. 患者基础信息表
CREATE TABLE patient_info (
  patient_id   INT          NOT NULL COMMENT '患者ID',
  gender       VARCHAR(4)   NOT NULL COMMENT '性别：男/女',
  age          INT          NOT NULL COMMENT '年龄（岁）',
  province     VARCHAR(20)  NOT NULL COMMENT '省份',
  city         VARCHAR(20)  NOT NULL COMMENT '城市/区县',
  id_number    VARCHAR(18)  NOT NULL COMMENT '模拟证件号（非真实个人信息）',
  phone        VARCHAR(11)  NOT NULL COMMENT '模拟手机号',
  create_time  DATETIME     NOT NULL COMMENT '建档时间',
  PRIMARY KEY (patient_id),
  UNIQUE KEY uk_patient_id_number (id_number),
  UNIQUE KEY uk_patient_phone (phone),
  KEY idx_patient_province (province, city),
  KEY idx_patient_create_time (create_time),
  CONSTRAINT chk_patient_gender CHECK (gender IN ('男','女')),
  CONSTRAINT chk_patient_age CHECK (age BETWEEN 0 AND 120)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='患者基础信息表';

-- 2. 慢性病记录表
CREATE TABLE disease_record (
  record_id     INT          NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  patient_id    INT          NOT NULL COMMENT '患者ID',
  disease_type  VARCHAR(30)  NOT NULL COMMENT '慢性病类型',
  disease_name  VARCHAR(50)  NOT NULL COMMENT '疾病名称',
  diagnose_date DATE         NOT NULL COMMENT '确诊日期',
  severity      VARCHAR(10)  NOT NULL COMMENT '严重程度：轻度/中度/重度',
  doctor_id     INT          NOT NULL COMMENT '主治医生ID',
  hospital      VARCHAR(64)  NOT NULL COMMENT '就诊医院',
  PRIMARY KEY (record_id),
  KEY idx_dr_patient (patient_id),
  KEY idx_dr_type_date (disease_type, diagnose_date),
  KEY idx_dr_date (diagnose_date),
  CONSTRAINT fk_dr_patient FOREIGN KEY (patient_id) REFERENCES patient_info(patient_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_dr_severity CHECK (severity IN ('轻度','中度','重度'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='慢性病记录表';

-- 3. 体检指标表
CREATE TABLE health_checkup (
  checkup_id      INT          NOT NULL AUTO_INCREMENT COMMENT '体检ID',
  patient_id      INT          NOT NULL COMMENT '患者ID',
  checkup_date    DATE         NOT NULL COMMENT '体检日期',
  sbp             INT          NOT NULL COMMENT '收缩压 mmHg',
  dbp             INT          NOT NULL COMMENT '舒张压 mmHg',
  fasting_glucose DECIMAL(5,2) NOT NULL COMMENT '空腹血糖 mmol/L',
  hba1c           DECIMAL(5,2) NOT NULL COMMENT '糖化血红蛋白 %',
  tc              DECIMAL(5,2) NOT NULL COMMENT '总胆固醇 mmol/L',
  tg              DECIMAL(5,2) NOT NULL COMMENT '甘油三酯 mmol/L',
  hdl             DECIMAL(5,2) NOT NULL COMMENT '高密度脂蛋白 mmol/L',
  ldl             DECIMAL(5,2) NOT NULL COMMENT '低密度脂蛋白 mmol/L',
  bmi             DECIMAL(5,2) NOT NULL COMMENT 'BMI 指数',
  heart_rate      INT          NOT NULL COMMENT '心率 次/分',
  creatinine      DECIMAL(7,2) NOT NULL COMMENT '肌酐 umol/L',
  uric_acid       DECIMAL(7,2) NOT NULL COMMENT '尿酸 umol/L',
  PRIMARY KEY (checkup_id),
  KEY idx_hc_patient (patient_id),
  KEY idx_hc_date (checkup_date),
  CONSTRAINT fk_hc_patient FOREIGN KEY (patient_id) REFERENCES patient_info(patient_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_hc_bp CHECK (sbp BETWEEN 60 AND 300 AND dbp BETWEEN 30 AND 200),
  CONSTRAINT chk_hc_glucose CHECK (fasting_glucose BETWEEN 1.0 AND 40.0),
  CONSTRAINT chk_hc_bmi CHECK (bmi BETWEEN 12.0 AND 50.0),
  CONSTRAINT chk_hc_hr CHECK (heart_rate BETWEEN 30 AND 220)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='体检指标表';

-- 4. 生活习惯表（每位患者一条）
CREATE TABLE lifestyle (
  lifestyle_id    INT          NOT NULL AUTO_INCREMENT COMMENT '习惯ID',
  patient_id      INT          NOT NULL COMMENT '患者ID',
  smoking_status  VARCHAR(10)  NOT NULL COMMENT '吸烟状态：从不/已戒/在吸',
  smoking_amount  INT          NOT NULL DEFAULT 0 COMMENT '每日吸烟量（支）',
  drinking_status VARCHAR(10)  NOT NULL COMMENT '饮酒状态：从不/已戒/在饮',
  exercise_freq   VARCHAR(10)  NOT NULL COMMENT '运动频率：无/偶尔/经常',
  sleep_hours     DECIMAL(3,1) NOT NULL COMMENT '平均睡眠时长（小时）',
  diet_pattern    VARCHAR(10)  NOT NULL COMMENT '饮食模式：清淡/正常/重口味',
  PRIMARY KEY (lifestyle_id),
  UNIQUE KEY uk_lifestyle_patient (patient_id),
  CONSTRAINT fk_ls_patient FOREIGN KEY (patient_id) REFERENCES patient_info(patient_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_ls_smoking CHECK (smoking_status IN ('从不','已戒','在吸')),
  CONSTRAINT chk_ls_drinking CHECK (drinking_status IN ('从不','已戒','在饮')),
  CONSTRAINT chk_ls_exercise CHECK (exercise_freq IN ('无','偶尔','经常')),
  CONSTRAINT chk_ls_diet CHECK (diet_pattern IN ('清淡','正常','重口味')),
  CONSTRAINT chk_ls_sleep CHECK (sleep_hours BETWEEN 0 AND 24),
  CONSTRAINT chk_ls_amount CHECK (smoking_amount BETWEEN 0 AND 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='生活习惯表';

-- 5. 就诊记录表
CREATE TABLE visit_record (
  visit_id      INT           NOT NULL AUTO_INCREMENT COMMENT '就诊ID',
  patient_id    INT           NOT NULL COMMENT '患者ID',
  visit_date    DATE          NOT NULL COMMENT '就诊日期',
  visit_type    VARCHAR(10)   NOT NULL COMMENT '门诊/急诊/住院',
  hospital      VARCHAR(64)   NOT NULL COMMENT '就诊医院',
  department    VARCHAR(20)   NOT NULL COMMENT '科室',
  diagnosis     VARCHAR(100)  NOT NULL COMMENT '诊断',
  cost          DECIMAL(10,2) NOT NULL COMMENT '费用（元）',
  insurance_pay DECIMAL(10,2) NOT NULL COMMENT '医保报销（元）',
  self_pay      DECIMAL(10,2) NOT NULL COMMENT '自付金额（元）',
  stay_days     INT           NOT NULL DEFAULT 0 COMMENT '住院天数',
  PRIMARY KEY (visit_id),
  KEY idx_vr_patient (patient_id),
  KEY idx_vr_date (visit_date),
  KEY idx_vr_type (visit_type),
  KEY idx_vr_dept (department),
  CONSTRAINT fk_vr_patient FOREIGN KEY (patient_id) REFERENCES patient_info(patient_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_vr_type CHECK (visit_type IN ('门诊','急诊','住院')),
  CONSTRAINT chk_vr_cost CHECK (cost >= 0 AND insurance_pay >= 0 AND self_pay >= 0),
  CONSTRAINT chk_vr_balance CHECK (ABS(cost - insurance_pay - self_pay) < 0.01),
  CONSTRAINT chk_vr_stay CHECK (stay_days BETWEEN 0 AND 365)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='就诊记录表';

-- 6. 用药记录表
CREATE TABLE medication_record (
  med_id       INT           NOT NULL AUTO_INCREMENT COMMENT '用药ID',
  patient_id   INT           NOT NULL COMMENT '患者ID',
  drug_name    VARCHAR(50)   NOT NULL COMMENT '药品名称',
  drug_type    VARCHAR(30)   NOT NULL COMMENT '药品类别',
  dosage       VARCHAR(30)   NOT NULL COMMENT '用法用量',
  start_date   DATE          NOT NULL COMMENT '开始日期',
  end_date     DATE          NOT NULL COMMENT '结束日期',
  cost         DECIMAL(10,2) NOT NULL COMMENT '药品费用（元）',
  is_effective VARCHAR(4)    NOT NULL COMMENT '是否有效：是/否',
  PRIMARY KEY (med_id),
  KEY idx_mr_patient (patient_id),
  KEY idx_mr_drug (drug_name),
  KEY idx_mr_type (drug_type),
  KEY idx_mr_date (start_date),
  CONSTRAINT fk_mr_patient FOREIGN KEY (patient_id) REFERENCES patient_info(patient_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_mr_dates CHECK (end_date >= start_date),
  CONSTRAINT chk_mr_cost CHECK (cost >= 0),
  CONSTRAINT chk_mr_effective CHECK (is_effective IN ('是','否'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用药记录表';

-- 7. 随访记录表
CREATE TABLE follow_up (
  follow_id            INT          NOT NULL AUTO_INCREMENT COMMENT '随访ID',
  patient_id           INT          NOT NULL COMMENT '患者ID',
  follow_date          DATE         NOT NULL COMMENT '随访日期',
  follow_type          VARCHAR(10)  NOT NULL COMMENT '电话/面访/线上',
  symptom_status       VARCHAR(10)  NOT NULL COMMENT '好转/稳定/加重',
  medication_adherence VARCHAR(10)  NOT NULL COMMENT '用药依从性：好/一般/差',
  doctor_advice        TEXT         NOT NULL COMMENT '医嘱建议',
  next_follow_date     DATE         NOT NULL COMMENT '下次随访日期',
  PRIMARY KEY (follow_id),
  KEY idx_fu_patient (patient_id),
  KEY idx_fu_date (follow_date),
  CONSTRAINT fk_fu_patient FOREIGN KEY (patient_id) REFERENCES patient_info(patient_id)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_fu_type CHECK (follow_type IN ('电话','面访','线上')),
  CONSTRAINT chk_fu_symptom CHECK (symptom_status IN ('好转','稳定','加重')),
  CONSTRAINT chk_fu_adherence CHECK (medication_adherence IN ('好','一般','差')),
  CONSTRAINT chk_fu_next CHECK (next_follow_date >= follow_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='随访记录表';
