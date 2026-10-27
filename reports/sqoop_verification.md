# Sqoop 独立导入验证报告

验证时间：2026-10-20 21:19—21:21
结论：**PASS（仅 1000 行 staging 验证；七表全量导入未执行）**

## 1. 环境

| 项 | 值 |
|---|---|
| Sqoop | 1.4.7，/opt/sqoop-1.4.7 |
| 安装包 | sqoop-1.4.7.bin__hadoop-2.6.0.tar.gz |
| Java | 1.8.0_371 |
| Hadoop client | 3.3.6 |
| MySQL Connector/J | 8.0.33 |
| MySQL | 8.0.42 |
| Hive | 3.1.3 |

安装过程未覆盖 Hadoop、Hive、Java；Sqoop 使用独立目录。Sqoop 1.4.7 的 lib 缺少 commons-lang 2.6，已从 /opt/hive/lib 复制到 Sqoop lib；未替换 Hadoop/Hive 核心依赖。

## 2. JDBC-only 探针

Java 8 最小程序通过 Connector/J 8.0.33 连接宿主机 MySQL：

- 数据库：MySQL 8.0.42；
- 用户：sqoop_verify；
- 权限：仅 SELECT ON chronic_disease.*；
- patient_info 总数：100000；
- patient_id <= 1000：1000；
- 样例：1|女|61|湖北|荆州；
- 结果：JDBC_OK。

密码通过 root-only 文件 /root/.sqoop_mysql_pass（0600）提供，未写入源码、命令日志或项目。

## 3. Sqoop 连接

sqoop list-databases 成功返回：

- information_schema
- performance_schema
- chronic_disease

## 4. 1000 行 staging 导入

- 表：patient_info
- 条件：patient_id <= 1000
- 目标：/warehouse/chronic_disease/sqoop_staging/patient_info_1000
- 导入前 MySQL COUNT(*)：1000
- YARN 应用：application_1792497795828_0029
- Map input records：1000
- Map output records：1000
- HDFS 文件：part-m-00000，78,592 bytes
- HDFS 行数：1000
- HDFS SHA-256：cadbe42385662b847f12337f5791fd2031bef2b7e605bb71df39a95d6a387852
- 未使用 --hive-import，未使用 --hive-overwrite，未删除现有 ODS/ADS。

## 5. Hive 验证

新建独立外部表：

chronic_disease_db.ods_sqoop_patient_info_1000

位置：

/warehouse/chronic_disease/sqoop_staging/patient_info_1000

字段：

| 字段 | 类型 |
|---|---|
| patient_id | int |
| gender | string |
| age | int |
| province | string |
| city | string |
| id_number | string |
| phone | string |
| create_time | string |

MySQL 与 Hive 聚合核对：n=1000、SUM(patient_id)=500500、SUM(age)=61527、COUNT(DISTINCT patient_id)=1000，双方一致。

Hive 查询：

- COUNT(*)：1000
- MIN(patient_id)：1
- MAX(patient_id)：1000
- COUNT(DISTINCT patient_id)：1000

样例与 MySQL 一致：1|女|61|湖北|荆州；2|男|77|江苏|无锡；3|女|39|四川|绵阳。

## 6. 未执行项

- 七张业务表全量 Sqoop 导入；
- --hive-import / --hive-overwrite；
- 覆盖现有 ODS/ADS；
- 修改 /etc/profile 或重启 Hadoop/Hive 服务。

## 7. 结论

Sqoop 的独立 JDBC 连接、list-databases、1000 行导入、HDFS 落盘、Hive 外部表查询均已实际通过；但验证范围仅限这张 staging 表，不等于七表全量同步完成。

## 8. 证据

- logs/sqoop_install.log
- logs/sqoop_jdbc.log
- logs/sqoop_eval.log
- logs/sqoop_import.log
- logs/sqoop_content_check.log
- reports/sqoop_verification.json
