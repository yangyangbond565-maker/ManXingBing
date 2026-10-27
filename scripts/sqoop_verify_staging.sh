#!/usr/bin/env bash
# Sqoop 独立导入验证：patient_info 前 1000 行 -> HDFS staging -> Hive 外部表
# 不修改现有 ODS/ADS；不使用 --hive-import / --hive-overwrite。
set -euo pipefail

export JAVA_HOME=/opt/java
export HADOOP_HOME=/opt/hadoop
export HADOOP_COMMON_HOME=/opt/hadoop
export HADOOP_HDFS_HOME=/opt/hadoop
export HADOOP_MAPRED_HOME=/opt/hadoop
export YARN_HOME=/opt/hadoop
export HIVE_HOME=/opt/hive
export SQOOP_HOME=/opt/sqoop-1.4.7
export PATH="$SQOOP_HOME/bin:$HADOOP_HOME/bin:$PATH"

MYSQL_URL='jdbc:mysql://192.168.20.1:3306/chronic_disease?useSSL=false&allowPublicKeyRetrieval=true&serverTimezone=Asia/Shanghai'
MYSQL_USER='sqoop_verify'
PASSWORD_FILE='file:///root/.sqoop_mysql_pass'
HIVE_DB='chronic_disease_db'
HIVE_TABLE='ods_sqoop_patient_info_1000'
TARGET='/warehouse/chronic_disease/sqoop_staging/patient_info_1000'
WHERE_CLAUSE='patient_id <= 1000'

echo "=== PREFLIGHT ==="
if hdfs dfs -test -e "$TARGET"; then
  echo "TARGET_EXISTS: $TARGET"
  exit 3
fi
if hive --silent -e "USE $HIVE_DB; SHOW TABLES LIKE '$HIVE_TABLE';" 2>/dev/null | grep -q "$HIVE_TABLE"; then
  echo "HIVE_TABLE_EXISTS: $HIVE_DB.$HIVE_TABLE"
  exit 4
fi

echo "=== MYSQL COUNT ==="
EVAL_OUT=$(sqoop eval --connect "$MYSQL_URL" --username "$MYSQL_USER" \
  --password-file "$PASSWORD_FILE" \
  --query "SELECT COUNT(*) AS cnt FROM patient_info WHERE $WHERE_CLAUSE" 2>&1)
printf '%s\n' "$EVAL_OUT" | tail -12
MYSQL_COUNT=$(printf '%s\n' "$EVAL_OUT" | awk -F'|' '/^\| *[0-9]+/{gsub(/ /,"",$2); print $2; exit}')
if [ "$MYSQL_COUNT" != "1000" ]; then
  echo "UNEXPECTED_MYSQL_COUNT: $MYSQL_COUNT"
  exit 5
fi

echo "=== SQOOP IMPORT ==="
sqoop import --connect "$MYSQL_URL" --username "$MYSQL_USER" \
  --password-file "$PASSWORD_FILE" \
  --table patient_info --where "$WHERE_CLAUSE" \
  --target-dir "$TARGET" \
  --fields-terminated-by '\t' --lines-terminated-by '\n' \
  --null-string '\\N' --null-non-string '\\N' \
  --m 1

echo "=== HDFS FILES ==="
hdfs dfs -ls -h "$TARGET"
HDFS_COUNT=$(hdfs dfs -cat "$TARGET"/part-m-* | wc -l)
echo "HDFS_COUNT=$HDFS_COUNT"
if [ "$HDFS_COUNT" != "1000" ]; then
  echo "UNEXPECTED_HDFS_COUNT: $HDFS_COUNT"
  exit 6
fi

echo "=== HIVE CREATE EXTERNAL TABLE ==="
hive -e "USE $HIVE_DB;
CREATE EXTERNAL TABLE $HIVE_TABLE (
  patient_id INT, gender STRING, age INT, province STRING, city STRING,
  id_number STRING, phone STRING, create_time STRING
) ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '$TARGET';"

echo "=== HIVE COUNT ==="
HIVE_COUNT=$(hive --silent -e "USE $HIVE_DB; SELECT COUNT(*) FROM $HIVE_TABLE;" 2>/dev/null | tail -1)
echo "HIVE_COUNT=$HIVE_COUNT"
if [ "$HIVE_COUNT" != "1000" ]; then
  echo "UNEXPECTED_HIVE_COUNT: $HIVE_COUNT"
  exit 7
fi

echo "=== HIVE SAMPLE ==="
hive --silent -e "USE $HIVE_DB; SELECT patient_id,gender,age,province,city FROM $HIVE_TABLE ORDER BY patient_id LIMIT 3;" 2>/dev/null
echo "=== HIVE DESCRIBE ==="
hive --silent -e "USE $HIVE_DB; DESCRIBE $HIVE_TABLE;" 2>/dev/null

echo "=== PASS ==="
echo "MYSQL_COUNT=$MYSQL_COUNT HDFS_COUNT=$HDFS_COUNT HIVE_COUNT=$HIVE_COUNT"