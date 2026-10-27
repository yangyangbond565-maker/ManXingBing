# -*- coding: utf-8 -*-
"""社区慢性病大数据分析 - PySpark 8 模块作业。

本地运行模式（Windows，已验证）：
  - 直接读取 data/warehouse/ods/*/data.tsv（单文件读取，规避 Windows 目录 ACL 问题）
  - Spark SQL 完成 8 个模块
  - 结果通过 JDBC 写入 MySQL ADS 表（后端与前端读取真实结果）

集群运行模式：
  - 将 ODS 路径改为 HDFS，或先用 scripts/sync_mysql_to_hive.py --mode hdfs 同步
  - 结果可改为 df.write.parquet(HDFS路径) 保存
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, IntegerType, LongType, StringType, StructField, StructType, TimestampType,
)

ROOT = Path(__file__).resolve().parents[1]
ODS_SPEC = os.getenv("CHRONIC_ODS_DIR", str(ROOT / "data" / "warehouse" / "ods")).rstrip("/")
ODS_IS_URI = "://" in ODS_SPEC
ODS_DIR = None if ODS_IS_URI else Path(ODS_SPEC)
ODS_BASE = ODS_SPEC if ODS_IS_URI else None
ADS_HDFS = os.getenv("CHRONIC_ADS_HDFS", "").rstrip("/")
REPORT = ROOT / "reports" / "spark_run.json"
JDBC_URL = os.getenv(
    "CHRONIC_JDBC_URL",
    "jdbc:mysql://127.0.0.1:3306/chronic_disease?useSSL=false&allowPublicKeyRetrieval=true"
    "&serverTimezone=Asia/Shanghai&characterEncoding=utf8",
)
DB_USER = os.getenv("CHRONIC_DB_USER", "root")
DB_PASSWORD = os.getenv("CHRONIC_DB_PASSWORD", "")
JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"

ADS_PATH_MAP = {
    "ads_patient_profile": "patient_profile",
    "ads_disease_dist": "disease_dist",
    "ads_severity": "severity",
    "ads_comorbidity": "comorbidity",
    "ads_risk_factor": "risk_factor",
    "ads_visit_analysis": "visit_analysis",
    "ads_medication_analysis": "medication_analysis",
    "ads_drug_by_disease": "drug_by_disease",
    "ads_trend": "trend",
    "ads_health_score": "health_score",
    "ads_health_level": "health_level",
    "ads_overview": "overview",
}

SCHEMAS = {
    "patient_info": "patient_id int, gender string, age int, province string, city string, id_number string, phone string, create_time string",
    "disease_record": "record_id int, patient_id int, disease_type string, disease_name string, diagnose_date string, severity string, doctor_id int, hospital string",
    "health_checkup": "checkup_id int, patient_id int, checkup_date string, sbp int, dbp int, fasting_glucose double, hba1c double, tc double, tg double, hdl double, ldl double, bmi double, heart_rate int, creatinine double, uric_acid double",
    "lifestyle": "lifestyle_id int, patient_id int, smoking_status string, smoking_amount int, drinking_status string, exercise_freq string, sleep_hours double, diet_pattern string",
    "visit_record": "visit_id int, patient_id int, visit_date string, visit_type string, hospital string, department string, diagnosis string, cost double, insurance_pay double, self_pay double, stay_days int",
    "medication_record": "med_id int, patient_id int, drug_name string, drug_type string, dosage string, start_date string, end_date string, cost double, is_effective string",
    "follow_up": "follow_id int, patient_id int, follow_date string, follow_type string, symptom_status string, medication_adherence string, doctor_advice string, next_follow_date string",
}


def parse_schema(text: str) -> StructType:
    mapping = {"int": IntegerType(), "string": StringType(), "double": DoubleType()}
    fields = []
    for part in text.split(","):
        name, typ = part.strip().split()
        fields.append(StructField(name, mapping[typ], True))
    return StructType(fields)


def build_spark() -> SparkSession:
    spark = (SparkSession.builder
             .appName("ChronicDiseaseAnalysis")
             .master(os.getenv("CHRONIC_SPARK_MASTER", "local[4]"))
             .config("spark.sql.catalogImplementation", "in-memory")
             .config("spark.ui.enabled", "false")
             .config("spark.sql.shuffle.partitions", "8")
             .config("spark.driver.memory", "3g")
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    return spark


def ods_uri(name: str) -> str:
    if ODS_IS_URI:
        uri = f"{ODS_BASE}/{name}/data.tsv"
        print(f"  [HDFS] {uri}", flush=True)
        return uri
    path = ODS_DIR / name / "data.tsv"
    if not path.exists():
        raise FileNotFoundError(f"ODS 文件不存在: {path}")
    return "file:///" + path.as_posix()


def load_ods(spark: SparkSession) -> dict:
    data = {}
    for name, schema in SCHEMAS.items():
        df = (spark.read
              .option("sep", "\t")
              .option("header", "false")
              .option("nullValue", "\\N")
              .option("mode", "PERMISSIVE")
              .schema(parse_schema(schema))
              .csv(ods_uri(name)))
        data[name] = df
        df.createOrReplaceTempView(f"ods_{name}")
        print(f"  loaded ods_{name}: {df.count():,}", flush=True)
    return data


def write_mysql(df, table: str) -> None:
    import pymysql
    row_count = df.count()
    conn = pymysql.connect(host=os.getenv("CHRONIC_DB_HOST", "127.0.0.1"),
                           port=int(os.getenv("CHRONIC_DB_PORT", "3306")),
                           user=DB_USER, password=DB_PASSWORD,
                           database=os.getenv("CHRONIC_DB_NAME", "chronic_disease"),
                           charset="utf8mb4", autocommit=True)
    try:
        with conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {table}")
    finally:
        conn.close()
    (df.write.format("jdbc")
     .option("url", JDBC_URL)
     .option("dbtable", table)
     .option("user", DB_USER)
     .option("password", DB_PASSWORD)
     .option("driver", JDBC_DRIVER)
     .option("batchsize", "5000")
     .mode("append")
     .save())
    print(f"  -> MySQL {table}: {row_count:,} rows", flush=True)
    if ADS_HDFS and table in ADS_PATH_MAP:
        hdfs_path = f"{ADS_HDFS}/{ADS_PATH_MAP[table]}"
        (df.coalesce(1).write.mode("overwrite")
         .option("header", "true").option("sep", "\t")
         .csv(hdfs_path))
        print(f"  -> HDFS  {hdfs_path}", flush=True)


def clean(data: dict, spark: SparkSession):
    latest = Window.partitionBy("patient_id").orderBy(F.col("create_time").desc())
    patient = (data["patient_info"]
               .filter((F.col("patient_id").isNotNull())
                       & (F.col("gender").isin("男", "女"))
                       & (F.col("age").between(0, 120)))
               .withColumn("rn", F.row_number().over(latest))
               .filter("rn = 1").drop("rn")
               .withColumn("age_group", F.when(F.col("age") < 30, "青年(<30)")
                           .when(F.col("age") < 45, "中青年(30-44)")
                           .when(F.col("age") < 60, "中年(45-59)")
                           .when(F.col("age") < 75, "中老年(60-74)")
                           .otherwise("老年(75+)")))
    checkup = (data["health_checkup"]
               .filter((F.col("patient_id").isNotNull())
                       & F.col("sbp").between(60, 300) & F.col("dbp").between(30, 200)
                       & F.col("fasting_glucose").between(1.0, 40.0)
                       & F.col("bmi").between(12.0, 50.0)
                       & F.col("heart_rate").between(30, 220)
                       & (F.col("sbp") > F.col("dbp")))
               .withColumn("bp_level", F.when((F.col("sbp") < 120) & (F.col("dbp") < 80), "正常")
                           .when((F.col("sbp") < 140) & (F.col("dbp") < 90), "正常高值")
                           .when((F.col("sbp") < 160) | (F.col("dbp") < 100), "1级高血压")
                           .when((F.col("sbp") < 180) | (F.col("dbp") < 110), "2级高血压")
                           .otherwise("3级高血压"))
               .withColumn("glucose_level", F.when(F.col("fasting_glucose") < 6.1, "正常")
                           .when(F.col("fasting_glucose") < 7.0, "空腹血糖受损")
                           .otherwise("糖尿病"))
               .withColumn("bmi_level", F.when(F.col("bmi") < 18.5, "偏瘦")
                           .when(F.col("bmi") < 24.0, "正常")
                           .when(F.col("bmi") < 28.0, "超重")
                           .otherwise("肥胖")))
    disease = data["disease_record"].filter(F.col("patient_id").isNotNull())
    lifestyle = data["lifestyle"].filter(F.col("patient_id").isNotNull())
    visit = data["visit_record"].filter(
        F.col("patient_id").isNotNull() & (F.col("cost") >= 0))
    med = data["medication_record"].filter(F.col("patient_id").isNotNull())
    follow = data["follow_up"].filter(F.col("patient_id").isNotNull())
    for name, df in [("patient_clean", patient), ("checkup_clean", checkup),
                     ("disease_clean", disease), ("lifestyle_clean", lifestyle),
                     ("visit_clean", visit), ("medication_clean", med),
                     ("followup_clean", follow)]:
        df.createOrReplaceTempView(name)

    report = {
        "patient_info": {"before": data["patient_info"].count(), "after": patient.count()},
        "health_checkup": {"before": data["health_checkup"].count(), "after": checkup.count()},
        "disease_record": {"before": data["disease_record"].count(), "after": disease.count()},
        "visit_record": {"before": data["visit_record"].count(), "after": visit.count()},
        "medication_record": {"before": data["medication_record"].count(), "after": med.count()},
        "follow_up": {"before": data["follow_up"].count(), "after": follow.count()},
    }
    print("  clean report:", report, flush=True)
    return report


def module2(spark):
    total = spark.sql("SELECT COUNT(*) c FROM patient_clean").first()["c"]
    gender = spark.sql(f"""SELECT 'gender' dimension_type, gender dimension_value, COUNT(*) patient_count,
        ROUND(COUNT(*)*100.0/{total},2) percentage, ROUND(AVG(age),1) avg_age, CAST(NULL AS STRING) extra_value
        FROM patient_clean GROUP BY gender""")
    age = spark.sql(f"""SELECT 'age' AS dimension_type, age_group AS dimension_value,
        COUNT(*) AS patient_count, ROUND(COUNT(*)*100.0/{total},2) AS percentage,
        ROUND(AVG(age),1) AS avg_age, CAST(NULL AS STRING) AS extra_value
        FROM patient_clean GROUP BY age_group""")
    province = spark.sql(f"""SELECT 'province' AS dimension_type, province AS dimension_value,
        COUNT(*) AS patient_count, ROUND(COUNT(*)*100.0/{total},2) AS percentage,
        ROUND(AVG(age),1) AS avg_age, CAST(NULL AS STRING) AS extra_value
        FROM patient_clean GROUP BY province""")
    age_gender = spark.sql(f"""SELECT 'age_gender' AS dimension_type, age_group AS dimension_value,
        COUNT(*) AS patient_count, ROUND(COUNT(*)*100.0/{total},2) AS percentage,
        ROUND(AVG(age),1) AS avg_age, gender AS extra_value
        FROM patient_clean GROUP BY age_group, gender""")
    result = gender.unionByName(age).unionByName(province).unionByName(age_gender)
    write_mysql(result, "ads_patient_profile")


def module3(spark):
    total = spark.sql("SELECT COUNT(DISTINCT patient_id) c FROM disease_clean").first()["c"]
    disease = spark.sql(f"""SELECT disease_type, COUNT(*) record_count,
        COUNT(DISTINCT patient_id) patient_count,
        ROUND(COUNT(DISTINCT patient_id)*100.0/{total},2) percentage,
        SUM(CASE WHEN severity='重度' THEN 1 ELSE 0 END) severe_count,
        ROUND(SUM(CASE WHEN severity='重度' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) severe_rate
        FROM disease_clean GROUP BY disease_type""")
    write_mysql(disease, "ads_disease_dist")

    severity = spark.sql("""SELECT disease_type, severity, COUNT(*) record_count,
        ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (PARTITION BY disease_type),2) percentage
        FROM disease_clean GROUP BY disease_type, severity""")
    write_mysql(severity, "ads_severity")

    comorb = spark.sql("""SELECT disease_count, COUNT(*) patient_count,
        ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),2) percentage
        FROM (SELECT patient_id, COUNT(DISTINCT disease_type) disease_count
              FROM disease_clean GROUP BY patient_id) t
        GROUP BY disease_count""")
    write_mysql(comorb, "ads_comorbidity")


def module4(spark):
    smoking = spark.sql("""SELECT 'smoking' factor_type, factor_value, disease_type, patient_count,
        ROUND(patient_count*100.0/SUM(patient_count) OVER (PARTITION BY disease_type),2) exposure_rate,
        CAST(NULL AS DOUBLE) avg_sbp, CAST(NULL AS DOUBLE) avg_glucose, CAST(NULL AS DOUBLE) avg_bmi
        FROM (SELECT l.smoking_status factor_value, d.disease_type,
                     COUNT(DISTINCT l.patient_id) patient_count
              FROM lifestyle_clean l JOIN disease_clean d ON l.patient_id=d.patient_id
              GROUP BY l.smoking_status, d.disease_type) t""")
    drinking = spark.sql("""SELECT 'drinking' AS factor_type, factor_value, disease_type,
        patient_count,
        ROUND(patient_count*100.0/SUM(patient_count) OVER (PARTITION BY disease_type),2) AS exposure_rate,
        CAST(NULL AS DOUBLE) AS avg_sbp, CAST(NULL AS DOUBLE) AS avg_glucose,
        CAST(NULL AS DOUBLE) AS avg_bmi
        FROM (SELECT l.drinking_status factor_value, d.disease_type,
                     COUNT(DISTINCT l.patient_id) patient_count
              FROM lifestyle_clean l JOIN disease_clean d ON l.patient_id=d.patient_id
              GROUP BY l.drinking_status, d.disease_type) t""")
    bmi = spark.sql("""SELECT 'bmi' AS factor_type, c.bmi_level AS factor_value,
        '全部' AS disease_type, COUNT(*) AS patient_count,
        ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),2) AS exposure_rate,
        ROUND(AVG(c.sbp),1) AS avg_sbp, ROUND(AVG(c.fasting_glucose),2) AS avg_glucose,
        ROUND(AVG(c.bmi),2) AS avg_bmi
        FROM checkup_clean c GROUP BY c.bmi_level""")
    exercise = spark.sql("""SELECT 'exercise' AS factor_type, l.exercise_freq AS factor_value,
        '全部' AS disease_type, COUNT(*) AS patient_count,
        ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),2) AS exposure_rate,
        ROUND(AVG(c.sbp),1) AS avg_sbp, ROUND(AVG(c.fasting_glucose),2) AS avg_glucose,
        ROUND(AVG(c.bmi),2) AS avg_bmi
        FROM lifestyle_clean l JOIN checkup_clean c ON l.patient_id=c.patient_id
        GROUP BY l.exercise_freq""")
    diet = spark.sql("""SELECT 'diet' AS factor_type, l.diet_pattern AS factor_value,
        '全部' AS disease_type, COUNT(*) AS patient_count,
        ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),2) AS exposure_rate,
        ROUND(AVG(c.sbp),1) AS avg_sbp, ROUND(AVG(c.fasting_glucose),2) AS avg_glucose,
        ROUND(AVG(c.bmi),2) AS avg_bmi
        FROM lifestyle_clean l JOIN checkup_clean c ON l.patient_id=c.patient_id
        GROUP BY l.diet_pattern""")
    result = smoking.unionByName(drinking).unionByName(bmi).unionByName(exercise).unionByName(diet)
    write_mysql(result, "ads_risk_factor")


def module5(spark):
    typ = spark.sql("""SELECT 'type' analysis_type, visit_type dimension_value, COUNT(*) visit_count,
        COUNT(DISTINCT patient_id) patient_count, ROUND(AVG(cost),2) avg_cost,
        ROUND(SUM(cost),2) total_cost,
        ROUND(AVG(CASE WHEN cost>0 THEN insurance_pay*100.0/cost ELSE 0 END),2) avg_reimbursement_rate,
        ROUND(AVG(stay_days),1) avg_stay_days
        FROM visit_clean GROUP BY visit_type""")
    dept = spark.sql("""SELECT 'department' AS analysis_type, department AS dimension_value,
        COUNT(*) AS visit_count, COUNT(DISTINCT patient_id) AS patient_count,
        ROUND(AVG(cost),2) AS avg_cost, ROUND(SUM(cost),2) AS total_cost,
        ROUND(AVG(CASE WHEN cost>0 THEN insurance_pay*100.0/cost ELSE 0 END),2) AS avg_reimbursement_rate,
        ROUND(AVG(stay_days),1) AS avg_stay_days FROM visit_clean GROUP BY department""")
    year = spark.sql("""SELECT 'year' AS analysis_type,
        CAST(YEAR(TO_DATE(visit_date)) AS STRING) AS dimension_value,
        COUNT(*) AS visit_count, COUNT(DISTINCT patient_id) AS patient_count,
        ROUND(AVG(cost),2) AS avg_cost, ROUND(SUM(cost),2) AS total_cost,
        ROUND(AVG(CASE WHEN cost>0 THEN insurance_pay*100.0/cost ELSE 0 END),2) AS avg_reimbursement_rate,
        ROUND(AVG(stay_days),1) AS avg_stay_days FROM visit_clean GROUP BY YEAR(TO_DATE(visit_date))""")
    write_mysql(typ.unionByName(dept).unionByName(year), "ads_visit_analysis")


def module6(spark):
    top = spark.sql("""SELECT 'top' analysis_type, drug_name dimension_value, usage_count, patient_count,
        avg_cost, effective_rate, CAST(rank_no AS INT) rank_no FROM (
          SELECT drug_name, COUNT(*) usage_count, COUNT(DISTINCT patient_id) patient_count,
                 ROUND(AVG(cost),2) avg_cost,
                 ROUND(SUM(CASE WHEN is_effective='是' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) effective_rate,
                 ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) rank_no
          FROM medication_clean GROUP BY drug_name) t WHERE rank_no <= 20""")
    typ = spark.sql("""SELECT 'type' AS analysis_type, drug_type AS dimension_value,
        COUNT(*) AS usage_count, COUNT(DISTINCT patient_id) AS patient_count,
        ROUND(AVG(cost),2) AS avg_cost,
        ROUND(SUM(CASE WHEN is_effective='是' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS effective_rate,
        CAST(NULL AS INT) AS rank_no FROM medication_clean GROUP BY drug_type""")
    effective = spark.sql("""SELECT 'effective' AS analysis_type, drug_name AS dimension_value,
        COUNT(*) AS usage_count, COUNT(DISTINCT patient_id) AS patient_count,
        ROUND(AVG(cost),2) AS avg_cost,
        ROUND(SUM(CASE WHEN is_effective='是' THEN 1 ELSE 0 END)*100.0/COUNT(*),2) AS effective_rate,
        CAST(NULL AS INT) AS rank_no FROM medication_clean GROUP BY drug_name HAVING COUNT(*) >= 100""")
    combo = spark.sql("""SELECT 'combo' AS analysis_type, CAST(type_count AS STRING) AS dimension_value,
        SUM(1) AS usage_count, SUM(1) AS patient_count,
        CAST(NULL AS DOUBLE) AS avg_cost, CAST(NULL AS DOUBLE) AS effective_rate,
        CAST(NULL AS INT) AS rank_no
        FROM (SELECT patient_id, COUNT(DISTINCT drug_type) type_count
              FROM medication_clean GROUP BY patient_id) t GROUP BY type_count""")
    write_mysql(top.unionByName(typ).unionByName(effective).unionByName(combo), "ads_medication_analysis")

    by_disease = spark.sql("""SELECT disease_type, drug_name, usage_count, rank_no FROM (
        SELECT d.disease_type, m.drug_name, COUNT(*) usage_count,
               ROW_NUMBER() OVER (PARTITION BY d.disease_type ORDER BY COUNT(*) DESC) rank_no
        FROM medication_clean m JOIN disease_clean d ON m.patient_id=d.patient_id
        GROUP BY d.disease_type, m.drug_name) t WHERE rank_no <= 3""")
    write_mysql(by_disease, "ads_drug_by_disease")


def module7(spark):
    yearly = spark.sql("""SELECT YEAR(TO_DATE(diagnose_date)) year, COUNT(*) cases
        FROM disease_clean GROUP BY YEAR(TO_DATE(diagnose_date)) ORDER BY year""")
    rows = [(int(r["year"]), int(r["cases"])) for r in yearly.collect()]
    n = len(rows)
    if n < 2:
        raise RuntimeError("年度数据不足，无法回归")
    sx = sum(x for x, _ in rows); sy = sum(y for _, y in rows)
    sxy = sum(x * y for x, y in rows); sx2 = sum(x * x for x, _ in rows)
    denom = n * sx2 - sx * sx
    slope = (n * sxy - sx * sy) / denom
    intercept = (sy - slope * sx) / n
    ymean = sy / n
    ss_tot = sum((y - ymean) ** 2 for _, y in rows)
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in rows)
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    trend = "上升" if slope > 0 else "下降"
    print(f"  regression: n={n}, slope={slope:.4f}, intercept={intercept:.4f}, R2={r2:.4f}", flush=True)

    schema = StructType([
        StructField("grain", StringType()), StructField("period", StringType()),
        StructField("disease_type", StringType()), StructField("cases", IntegerType()),
        StructField("predicted_cases", DoubleType()), StructField("slope", DoubleType()),
        StructField("intercept", DoubleType()), StructField("r2", DoubleType()),
        StructField("trend", StringType()), StructField("is_forecast", IntegerType()),
    ])
    out = []
    for x, y in rows:
        out.append(("year", str(x), "全部", int(y), round(slope * x + intercept, 1),
                    round(slope, 4), round(intercept, 4), round(r2, 4), trend, 0))
    for yr in range(2026, 2030):
        out.append(("year", str(yr), "全部", 0, round(slope * yr + intercept, 1),
                    round(slope, 4), round(intercept, 4), round(r2, 4), trend, 1))
    for r in spark.sql("""SELECT DATE_FORMAT(TO_DATE(diagnose_date),'yyyy-MM') ym, COUNT(*) c
                          FROM disease_clean GROUP BY DATE_FORMAT(TO_DATE(diagnose_date),'yyyy-MM')
                          ORDER BY ym""").collect():
        out.append(("month", r["ym"], "全部", int(r["c"]), None, None, None, None, None, 0))
    for r in spark.sql("""SELECT YEAR(TO_DATE(diagnose_date)) y, disease_type, COUNT(*) c
                          FROM disease_clean GROUP BY YEAR(TO_DATE(diagnose_date)), disease_type""").collect():
        out.append(("year_disease", str(r["y"]), r["disease_type"], int(r["c"]), None, None, None, None, None, 0))
    df = spark.createDataFrame(out, schema)
    write_mysql(df, "ads_trend")
    return {"slope": round(slope, 4), "intercept": round(intercept, 4), "r2": round(r2, 4),
            "years": [x for x, _ in rows], "cases": [y for _, y in rows]}


def module8(spark):
    spark.sql("""CREATE OR REPLACE TEMPORARY VIEW latest_checkup AS
        SELECT * FROM (SELECT c.*, ROW_NUMBER() OVER (PARTITION BY patient_id ORDER BY checkup_date DESC) rn
                       FROM checkup_clean c) t WHERE rn=1""")
    scores = spark.sql("""
        SELECT pl.patient_id, pc.gender, pc.age, pc.age_group, pc.province,
          CASE WHEN pl.bp_level='正常' THEN 100 WHEN pl.bp_level='正常高值' THEN 75
               WHEN pl.bp_level='1级高血压' THEN 50 WHEN pl.bp_level='2级高血压' THEN 30 ELSE 10 END bp_score,
          CASE WHEN pl.glucose_level='正常' THEN 100 WHEN pl.glucose_level='空腹血糖受损' THEN 60 ELSE 25 END glucose_score,
          CASE WHEN pl.bmi_level='正常' THEN 100 WHEN pl.bmi_level='偏瘦' THEN 70
               WHEN pl.bmi_level='超重' THEN 60 ELSE 30 END bmi_score,
          CASE WHEN pl.tc < 5.2 THEN 100 WHEN pl.tc < 6.2 THEN 70 WHEN pl.tc < 7.2 THEN 40 ELSE 20 END lipid_score,
          CASE WHEN pl.heart_rate BETWEEN 60 AND 80 THEN 100
               WHEN pl.heart_rate BETWEEN 50 AND 100 THEN 75 ELSE 40 END hr_score,
          CASE WHEN ls.smoking_status='从不' THEN 100 WHEN ls.smoking_status='已戒' THEN 80 ELSE 30 END smoking_score,
          CASE WHEN ls.drinking_status='从不' THEN 100 WHEN ls.drinking_status='已戒' THEN 80 ELSE 40 END drinking_score,
          CASE WHEN ls.exercise_freq='经常' THEN 100 WHEN ls.exercise_freq='偶尔' THEN 70 ELSE 40 END exercise_score,
          ROUND(
            (CASE WHEN pl.bp_level='正常' THEN 100 WHEN pl.bp_level='正常高值' THEN 75
                  WHEN pl.bp_level='1级高血压' THEN 50 WHEN pl.bp_level='2级高血压' THEN 30 ELSE 10 END)*0.20 +
            (CASE WHEN pl.glucose_level='正常' THEN 100 WHEN pl.glucose_level='空腹血糖受损' THEN 60 ELSE 25 END)*0.20 +
            (CASE WHEN pl.bmi_level='正常' THEN 100 WHEN pl.bmi_level='偏瘦' THEN 70
                  WHEN pl.bmi_level='超重' THEN 60 ELSE 30 END)*0.15 +
            (CASE WHEN pl.tc < 5.2 THEN 100 WHEN pl.tc < 6.2 THEN 70 WHEN pl.tc < 7.2 THEN 40 ELSE 20 END)*0.15 +
            (CASE WHEN pl.heart_rate BETWEEN 60 AND 80 THEN 100
                  WHEN pl.heart_rate BETWEEN 50 AND 100 THEN 75 ELSE 40 END)*0.10 +
            (CASE WHEN ls.smoking_status='从不' THEN 100 WHEN ls.smoking_status='已戒' THEN 80 ELSE 30 END)*0.08 +
            (CASE WHEN ls.drinking_status='从不' THEN 100 WHEN ls.drinking_status='已戒' THEN 80 ELSE 40 END)*0.07 +
            (CASE WHEN ls.exercise_freq='经常' THEN 100 WHEN ls.exercise_freq='偶尔' THEN 70 ELSE 40 END)*0.05, 1) health_score
        FROM latest_checkup pl
        JOIN patient_clean pc ON pl.patient_id=pc.patient_id
        JOIN lifestyle_clean ls ON pl.patient_id=ls.patient_id""")
    scores = scores.withColumn("health_level", F.when(F.col("health_score") >= 85, "优秀")
                               .when(F.col("health_score") >= 70, "良好")
                               .when(F.col("health_score") >= 55, "一般")
                               .when(F.col("health_score") >= 40, "较差").otherwise("危险"))
    scores = scores.withColumn("scored_at", F.current_timestamp())
    scores.createOrReplaceTempView("health_scores")
    write_mysql(scores, "ads_health_score")

    levels = spark.sql("""SELECT health_level level, COUNT(*) patient_count,
        ROUND(AVG(health_score),1) avg_score,
        ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER (),2) percentage,
        CASE health_level WHEN '优秀' THEN 1 WHEN '良好' THEN 2 WHEN '一般' THEN 3
                          WHEN '较差' THEN 4 ELSE 5 END sort_no
        FROM health_scores GROUP BY health_level""")
    write_mysql(levels, "ads_health_level")

    total = scores.count()
    avg_score = scores.agg(F.round(F.avg("health_score"), 1)).first()[0]
    high = scores.filter(F.col("health_score") < 50).count()
    visits = spark.sql("SELECT COUNT(*) c, ROUND(SUM(cost),2) s, ROUND(AVG(cost),2) a FROM visit_clean").first()
    start_end = spark.sql("SELECT MIN(YEAR(TO_DATE(diagnose_date))) s, MAX(YEAR(TO_DATE(diagnose_date))) e FROM disease_clean").first()
    counts = {t: spark.table(t).count() for t in ["patient_clean", "disease_clean", "visit_clean",
                                                   "medication_clean", "followup_clean"]}
    overview = spark.createDataFrame([(
        total, counts["disease_clean"], counts["visit_clean"], counts["medication_clean"],
        counts["followup_clean"], float(avg_score), high, round(high * 100.0 / total, 2),
        float(visits["s"] or 0), float(visits["a"] or 0), int(start_end["s"]), int(start_end["e"]),
        datetime.now(),
    )], StructType([
        StructField("total_patients", IntegerType()), StructField("total_disease_records", LongType()),
        StructField("total_visits", LongType()), StructField("total_medications", LongType()),
        StructField("total_followups", LongType()), StructField("avg_health_score", DoubleType()),
        StructField("high_risk_count", IntegerType()), StructField("high_risk_rate", DoubleType()),
        StructField("total_cost", DoubleType()), StructField("avg_cost", DoubleType()),
        StructField("data_start_year", IntegerType()), StructField("data_end_year", IntegerType()),
        StructField("updated_at", TimestampType()),
    ]))
    write_mysql(overview, "ads_overview")
    print("  health levels:", [r.asDict() for r in levels.collect()], flush=True)
    return {"patients": total, "avg_score": float(avg_score), "high_risk": high,
            "high_risk_rate": round(high * 100.0 / total, 2)}


def main() -> None:
    t0 = time.time()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    spark = build_spark()
    print("=" * 64, flush=True)
    print("社区慢性病大数据分析 - Spark SQL 8 模块", flush=True)
    print("=" * 64, flush=True)
    data = load_ods(spark)
    clean_report = clean(data, spark)

    print("[M2] 患者画像", flush=True); module2(spark)
    print("[M3] 疾病分布", flush=True); module3(spark)
    print("[M4] 风险因素", flush=True); module4(spark)
    print("[M5] 就诊行为", flush=True); module5(spark)
    print("[M6] 用药分析", flush=True); module6(spark)
    print("[M7] 趋势预测", flush=True); metrics = module7(spark)
    print("[M8] 健康评分", flush=True); health = module8(spark)

    report = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": round(time.time() - t0, 2),
        "clean_report": clean_report,
        "prediction": metrics,
        "health_score": health,
        "ods_dir": ODS_SPEC,
        "mysql_ads": "chronic_disease.ads_*",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    spark.stop()


if __name__ == "__main__":
    main()