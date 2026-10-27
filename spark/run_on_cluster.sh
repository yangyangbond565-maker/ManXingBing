#!/usr/bin/env bash
# ============================================================
# Linux/VM 集群运行 Spark 八模块（HDFS/Hive 目标环境）
# 前提: HDFS/Hive/Spark 正常；ODS 已同步到 /warehouse/chronic_disease/ods
# 用法: bash spark/run_on_cluster.sh
# ============================================================
set -euo pipefail

SPARK_HOME="${SPARK_HOME:-/opt/spark}"
HIVE_DB="${HIVE_DB:-chronic_disease_db}"
HDFS_BASE="${HDFS_BASE:-/warehouse/chronic_disease}"
export PYSPARK_PYTHON="${PYSPARK_PYTHON:-python3}"

echo "1) 创建 Hive ODS/DWD/ADS 表"
hive -f sql/hive/01_ods.sql
hive -f sql/hive/02_dwd.sql

echo "2) 运行 PySpark（HDFS 输入 + MySQL JDBC 输出）"
export CHRONIC_ODS_DIR="${HDFS_BASE}/ods"
export CHRONIC_ADS_HDFS="${HDFS_BASE}/ads"
"${SPARK_HOME}/bin/spark-submit" \
  --master "local[4]" \
  --driver-memory 4g \
  --conf "spark.sql.shuffle.partitions=8" \
  spark/chronic_disease_analysis.py

echo "3) 创建 ADS 外部表"
hive -f sql/hive/03_ads.sql

echo "4) 验证"
hive -f sql/hive/04_queries.sql
hdfs dfs -ls "${HDFS_BASE}/ods"