#!/usr/bin/env bash
# ============================================================
# Sqoop: MySQL -> Hive ODS（Linux 集群备选方案）
# 用法:
#   export MYSQL_PASS='***'
#   bash scripts/sqoop_sync.sh
# 说明: 本机没有 Sqoop/Hive，未实际执行；脚本保留为目标环境方案。
# ============================================================
set -euo pipefail

MYSQL_HOST="${MYSQL_HOST:-127.0.0.1}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASS="${MYSQL_PASS:?请通过环境变量 MYSQL_PASS 提供口令}"
MYSQL_DB="${MYSQL_DB:-chronic_disease}"
HIVE_DB="${HIVE_DB:-chronic_disease_db}"

TABLES=(patient_info disease_record health_checkup lifestyle visit_record medication_record follow_up)

for TABLE in "${TABLES[@]}"; do
  echo "============================================"
  echo "同步 ${TABLE} -> ${HIVE_DB}.ods_${TABLE}"
  echo "============================================"
  sqoop import \
    --connect "jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}?useSSL=false&characterEncoding=utf8" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PASS}" \
    --table "${TABLE}" \
    --hive-import \
    --hive-database "${HIVE_DB}" \
    --hive-table "ods_${TABLE}" \
    --hive-overwrite \
    --fields-terminated-by '\t' \
    --lines-terminated-by '\n' \
    --null-string '\\N' \
    --null-non-string '\\N' \
    --m 1 \
    --delete-target-dir
  echo "[OK] ${TABLE}"
done

echo "全部同步完成。请执行 sql/hive/04_queries.sql 验证行数。"
