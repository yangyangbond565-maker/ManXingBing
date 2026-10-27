# Spark 目录

- chronic_disease_analysis.py：本地已验证的 PySpark 8 模块作业，读取 data/warehouse/ods 的 TSV，结果 JDBC 写 MySQL ADS。
- sql/01_clean.sql ~ 08_health_score.sql：Spark SQL 参考脚本（Hive 表名）。
- run_on_cluster.sh：Linux HDFS/Hive 目标环境的提交脚本。
- run_spark.ps1 在 scripts/ 下，Windows 本地运行入口。
