# HDFS / Hive 实机验证报告

验证时间：2026-10-20 20:05–21:21
虚拟机：Hadoop-CentOS7，IP 192.168.20.135，CentOS 7，Java 1.8.0_371
结论：**HDFS PASS；Hive ODS/ADS PASS；Sqoop 1000 行 staging PASS（七表全量未执行）。**

## 1. HDFS

- NameNode：hdfs://hadoop:9000，Live DataNode 1 个
- 容量 47.76 GB，剩余 42.31 GB
- 测试路径：/warehouse/chronic_disease/ods/_verification/hdfs_test.txt
- 文件大小：106 bytes
- 本地 SHA-256：aaec11fc8b502819e91bc03e5f45117ba0e71e1b198675f6bff25ebe68381406
- HDFS SHA-256：aaec11fc8b502819e91bc03e5f45117ba0e71e1b198675f6bff25ebe68381406
- 已通过 hdfs dfs -ls -h、-stat、-cat 与校验和验证。

## 2. MySQL → HDFS ODS

通过项目 sync_mysql_to_hive.py --mode webhdfs 实际同步，耗时 34.86 秒：

| 表 | MySQL 行数 | HDFS 行数 |
|---|---:|---:|
| patient_info | 100,000 | 100,000 |
| disease_record | 165,087 | 165,087 |
| health_checkup | 300,022 | 300,022 |
| lifestyle | 100,000 | 100,000 |
| visit_record | 550,070 | 550,070 |
| medication_record | 549,587 | 549,587 |
| follow_up | 300,390 | 300,390 |
| **合计** | **2,065,156** | **2,065,156** |

HDFS 路径：/warehouse/chronic_disease/ods/<table>/data.tsv。

## 3. Hive ODS

- Hive 3.1.3；Metastore 9083；HiveServer2 10000。
- 数据库：chronic_disease_db。
- 建立 7 张外部表，实际 COUNT(*) 与 MySQL/HDFS 完全一致（见上表）。
- 样例字段：patient_id int、checkup_date string、fasting_glucose double、bmi double。
- 疾病 TOP：高血压 40,912、糖尿病 31,890、冠心病 23,620。

## 4. Spark HDFS 输入与 ADS 输出

- Spark 3.3.4，本地 Windows 驱动，HDFS client 3.3.6。
- 输入：hdfs://192.168.20.135:9000/warehouse/chronic_disease/ods/*/data.tsv。
- 八模块退出码 0，耗时 124.74 秒。
- 12 张 ADS 结果写入 HDFS：/warehouse/chronic_disease/ads/<name>。
- 同时写入 MySQL ADS，后端仍读取 MySQL。
- 关键结果：平均健康评分 72.8；高危 1,718（1.72%）；R²=0.7361；2026 预测 38,197.8；2029 预测 49,905.8。

## 5. Hive ADS

建立 12 张 ADS 外部表，实际查询：

| 表 | 行数 |
|---|---:|
| ads_overview | 1 |
| ads_patient_profile | 33 |
| ads_disease_dist | 10 |
| ads_severity | 30 |
| ads_comorbidity | 3 |
| ads_risk_factor | 70 |
| ads_visit_analysis | 18 |
| ads_medication_analysis | 108 |
| ads_drug_by_disease | 30 |
| ads_trend | 188 |
| ads_health_score | 100,000 |
| ads_health_level | 5 |

Hive 的 overview、health_level、forecast、disease TOP 查询结果与 MySQL 一致。

## 6. Sqoop

- Sqoop 1.4.7 已独立安装在 /opt/sqoop-1.4.7，使用 Connector/J 8.0.33。
- patient_info 的 patient_id <= 1000 已导入：
  /warehouse/chronic_disease/sqoop_staging/patient_info_1000
- HDFS 1000 行、Hive 外部表 ods_sqoop_patient_info_1000 1000 行。
- 未使用 --hive-import / --hive-overwrite，未覆盖现有 ODS/ADS。
- 七张表全量导入未执行；详见 reports/sqoop_verification.md。

## 7. 证据文件

- logs/hdfs_inspection.txt
- logs/hdfs_verification.log
- logs/webhdfs_sync.log
- logs/hive_inspection.txt
- logs/hive_ddl.log
- logs/hive_counts.log
- logs/hive_ads.log
- logs/hive_ads_queries.log
- logs/spark_hdfs_smoke.log
- logs/spark_hdfs_run.log
- reports/hdfs_hive_verification.json
- logs/sqoop_install.log
- logs/sqoop_jdbc.log
- logs/sqoop_eval.log
- logs/sqoop_import.log
- logs/sqoop_content_check.log
- reports/sqoop_verification.json
- reports/sqoop_verification.md