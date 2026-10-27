# 社区慢性病大数据分析系统

本科数据科学与大数据技术实训项目。项目从零重建，围绕 **100,000 名虚构患者**、**七张 MySQL 业务表**、**八个 Spark SQL 分析模块**，完成：

~~~text
Python 模拟数据 → MySQL（7 表 / 2,065,156 行） → WebHDFS → HDFS ODS
      → Hive ODS（7 表） → Spark SQL（8 模块） → MySQL ADS + HDFS ADS（12 表）
      → Spring Boot REST API → Vue 3 管理平台 + 数据可视化大屏
      → Matplotlib 静态图 / 测试报告 / 答辩材料
~~~

> 项目定位：教学与实训演示。健康评分、风险关联和趋势预测是统计/规则模型，**不是临床诊断工具**，不能替代医生判断。

## 1. 已实际验证的结果

| 项目 | 结果 | 证据 |
|---|---|---|
| 患者人数 | **100,000** | patient_info 实测；统计口径为患者人数 |
| 七表总行数 | **2,065,156** | reports/data_quality_report.json |
| 数据质量 | 7/7 表 PASS，0 关键问题 | reports/data_quality_report.md |
| HDFS | **PASS**：测试文件校验和一致，42.31 GB 可用 | reports/hdfs_hive_verification.md |
| Hive ODS | **PASS**：7 表，行数与 MySQL 完全一致 | logs/hive_counts.log |
| Spark 分析 | **PASS**：从 HDFS 读取，8 模块，124.74 秒 | reports/spark_run.json |
| ADS 结果 | MySQL 15 表 + HDFS 12 个结果目录；评分 100,000 行 | sql/mysql/02_ads_schema.sql、reports/hdfs_hive_verification.md |
| Sqoop | **PASS（仅 1000 行 staging）**；七表全量未执行 | reports/sqoop_verification.md |
| 趋势预测 | 线性回归，2018-2025 训练，2026-2029 预测，R²=0.7361 | ads_trend / /api/trend |
| 健康评分 | 平均 72.8；高危 1,718 人（1.72%） | ads_overview |
| 后端 | Spring Boot 2.7.18，接口 HTTP 200 | reports/api_test_report.md |
| 前端 | Vue 3 + Vite 构建成功，页面真实联调 | screenshots/ |
| 静态图 | Matplotlib 8 张真实结果图 | analysis/output/ |

## 2. 重要环境说明（必须阅读）

### 2.1 已完成并验证
- Windows 主机 + MySQL 8.0.42 + JDK 21（编译后端，源码目标 Java 17）+ Maven 3.6.3 + Node 24 + Python 3.13（生成）/3.10（PySpark）。
- **Spark 3.3.4 本地模式**：从 HDFS 读 ODS，8 模块真实产出写 MySQL ADS（15 表）与 HDFS ADS（12 目录）。
- 前端 Vue 3 构建和预览成功，Playwright 真实截图；后端接口真实返回 MySQL 数据。

### 2.2 HDFS / Hive 已实机验证

2026-10-20 20:05 起，VMware 虚拟机 Hadoop-CentOS7 已由用户手动启动，IP 192.168.20.135，SSH 密钥登录成功（不需要 root 密码）。

- **HDFS PASS**：NameNode/DataNode 正常，Live DataNode 1 个，容量 47.76 GB，剩余 42.31 GB；测试文件 106 bytes，本地与 HDFS SHA-256 均为 aaec11fc8b502819e91bc03e5f45117ba0e71e1b198675f6bff25ebe68381406。
- **MySQL → HDFS**：sync_mysql_to_hive.py --mode webhdfs，7 表 2,065,156 行，耗时 34.86 秒；HDFS 行数与 MySQL 完全一致。
- **Hive ODS PASS**：Hive 3.1.3，7 张外部表，COUNT(*) 全部一致；Metastore 9083、HiveServer2 10000 正在运行。
- **Spark HDFS PASS**：Spark 3.3.4 从 HDFS 读取 ODS，8 模块退出码 0，耗时 124.74 秒；12 张 ADS 结果写入 HDFS，同时写 MySQL ADS。
- **Hive ADS PASS**：12 张 ADS 外部表，overview / health_level / forecast / disease 查询值与 MySQL 一致。
- **Sqoop 已验证**：1.4.7 独立安装在 /opt/sqoop-1.4.7，用 Connector/J 8.0.33 连接 MySQL，完成 patient_info 前 1000 行 staging 导入；HDFS 1000 行、Hive 外部表 1000 行，字段与样例核对一致。仅验证独立导入，七表全量未执行。

详细证据：docs/15-未完成事项与限制.md、reports/hdfs_hive_verification.md、reports/sqoop_verification.md、logs/ 下 HDFS/Hive/Spark/Sqoop 日志。

### 2.3 Sqoop 独立验证

- Sqoop 1.4.7 安装在 **/opt/sqoop-1.4.7**，没有覆盖 Hadoop/Hive/Java。
- 使用 **mysql-connector-j-8.0.33.jar**；JDBC 探针返回 patient_info 总数 100000、patient_id <= 1000 为 1000。
- 只导入 patient_info 前 1000 行到：

  /warehouse/chronic_disease/sqoop_staging/patient_info_1000

- 未使用 --hive-import、未使用 --hive-overwrite，未删除现有 ODS/ADS。
- HDFS 1000 行、Hive 外部表 **ods_sqoop_patient_info_1000** 1000 行，字段与样例核对一致。
- **验证范围仅限 1000 行 staging；七张表全量导入没有执行。**

## 3. 目录

~~~text
chronic-disease/
├── backend/                 Spring Boot 2.7.18 后端（Java 17 编译）
├── frontend/                Vue 3 + Vite + ECharts + Element Plus
├── python/chronic_disease/  生成、入库、质量检查、Hive 同步、元数据
├── sql/mysql/               7 张业务表 + ADS 结果表
├── sql/hive/                Hive ODS / DWD / ADS DDL
├── spark/                   PySpark 8 模块 + 参考 SQL + 集群脚本
├── analysis/                Matplotlib 8 张图与底表
├── scripts/                 Windows 启动/检查/流水线脚本
├── tests/                   pytest + JUnit + API 冒烟
├── docs/                    需求、设计、数据字典、部署、测试等 17 份文档
├── reports/                 真实质量/运行/测试报告
├── presentation/            答辩 PPT、讲稿、演示手册
├── screenshots/             真实运行截图
├── data/                    生成数据、ODS TSV、ADS 导出（大文件已 gitignore）
└── README.md
~~~

## 4. 快速启动（Windows）

### 4.1 配置

复制 backend/.env.example 为 backend/.env.local，填入本机 MySQL 口令。**不要把 .env.local 提交或放进压缩包**。

Python 依赖：项目已内置 python/vendor/pymysql；如需重装：

~~~powershell
python -m pip install pymysql pandas matplotlib
~~~

### 4.2 建库、生成、入库、质量检查

~~~powershell
cd D:\官方工作区\chronic-disease
$env:PYTHONPATH="$PWD\python;$PWD\python\vendor"
$env:CHRONIC_DB_PASSWORD="你的MySQL口令"

# 建库建表
python -m chronic_disease.load_mysql --init

# 生成 100,000 名患者（约 37 秒，输出 data/generated）
python -m chronic_disease.generate --patients 100000 --seed 20261020

# 批量导入（约 100 秒，LOAD DATA LOCAL INFILE）
python -m chronic_disease.load_mysql --truncate

# 质量检查（应输出 PASS）
python -m chronic_disease.quality_check
~~~

### 4.3 导出 ODS 并运行 Spark

先确保已安装 Spark 3.3.4 / Hadoop 3.3.6 / Python 3.10 / MySQL Connector/J，并设置：

~~~powershell
$env:SPARK_HOME="D:\path\spark-3.3.4-bin-hadoop3"
$env:HADOOP_HOME="D:\path\hadoop-3.3.6"
$env:PYTHON310="D:\path\python-3.10\python.exe"
$env:MYSQL_JDBC_JAR="D:\path\mysql-connector-j-8.0.33.jar"
$env:CHRONIC_DB_PASSWORD="你的MySQL口令"
$env:CHRONIC_WEBHDFS="http://192.168.20.135:9870/webhdfs/v1"
$env:CHRONIC_HDFS_HOST="192.168.20.135"
~~~

~~~powershell
# 将 MySQL 七表通过 WebHDFS 同步到 HDFS
python -m chronic_disease.sync_mysql_to_hive --mode webhdfs

# 可选：用 Hive 创建 ODS/ADS 外部表
# 在 VM 上执行 sql/hive/01_ods.sql、03_ads.sql

# Spark 从 HDFS 读 ODS，写 MySQL ADS + HDFS ADS
$env:CHRONIC_ODS_DIR="hdfs://192.168.20.135:9000/warehouse/chronic_disease/ods"
$env:CHRONIC_ADS_HDFS="hdfs://192.168.20.135:9000/warehouse/chronic_disease/ads"
powershell -ExecutionPolicy Bypass -File .\scripts\run_spark.ps1
python -m chronic_disease.load_metadata
~~~

### 4.4 启动后端

~~~powershell
cd backend
mvn "-Dmaven.repo.local=$PWD\.mvnrepo" -DskipTests package
powershell -ExecutionPolicy Bypass -File .\run-backend.ps1
~~~

默认 http://127.0.0.1:8080，健康检查 GET /api/health。

### 4.5 启动前端

~~~powershell
cd frontend
npm install --ignore-scripts --cache ..\.npm-cache
npm run build
npm run preview
~~~

访问：

- 管理台：http://127.0.0.1:4173/#/home
- 可视化大屏：http://127.0.0.1:4173/#/screen
- 患者查询：http://127.0.0.1:4173/#/patients

如果本机 Node 环境允许 esbuild 正常 spawn，也可以使用 npm run dev（5173 端口）。本机沙箱环境使用 preview 方式完成了真实截图与前后端联调。

## 5. 八个模块

| 模块 | 主要内容 | 关键输出 |
|---|---|---|
| M1 数据清洗 | 去重、年龄/血压/血糖/BMI/心率范围过滤、缺失与异常报告 | 清洗前后计数 |
| M2 患者画像 | 性别、年龄、省份、年龄×性别 | 33 行画像结果 |
| M3 疾病分布 | 10 类疾病、严重程度、共病 | 10 + 30 + 3 行 |
| M4 风险因素 | 吸烟、饮酒、BMI、运动、饮食 | 70 行关联结果 |
| M5 就诊行为 | 类型、费用、医保、科室、年度 | 18 行 |
| M6 用药分析 | TOP20、类别、有效率、联合用药、疾病 TOP3 | 108 行 + TOP3 |
| M7 趋势预测 | 年度/月度 + 最小二乘线性回归 | 188 行（含 4 年预测） |
| M8 健康评分 | 8 维加权、五级分类、高危识别 | 100,000 行评分 |

健康评分公式与权重见 docs/06-分析模块算法说明.md；趋势模型评价与局限见 docs/06 和 spark/chronic_disease_analysis.py。

## 6. API 一览

统一响应：{"code":0,"message":"ok","data":...}。

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | /api/health | 服务健康状态 |
| GET | /api/dashboard/overview | 大屏总览指标 |
| GET | /api/patient-profile | 患者画像 |
| GET | /api/disease-distribution | 疾病分布/严重度/共病 |
| GET | /api/risk-factors?factor=smoking | 风险因素 |
| GET | /api/visits?type=type | 就诊分析 |
| GET | /api/medications?type=top | 用药分析 |
| GET | /api/trend?grain=year | 趋势/预测 |
| GET | /api/health-score/overview | 健康评分总览 |
| GET | /api/health-score/patients?page=1&size=10&level=优秀 | 评分分页 |
| GET | /api/patients?page=1&size=10&keyword=1 | 患者分页 |
| GET | /api/patients/{id} | 患者完整档案 |
| GET | /api/data-quality | 数据质量 |
| GET | /api/modules | 八模块运行状态 |

## 7. 测试与复现证据

~~~powershell
# Python 测试
$env:PYTHONPATH="$PWD\python;$PWD\python\vendor"
python -m pytest tests/python -q

# 后端集成测试（需要 MySQL 已导入数据）
cd backend
$env:CHRONIC_DB_PASSWORD="你的口令"
mvn test "-Dmaven.repo.local=D:\官方工作区\.tools\m2repo"
~~~

测试报告、质量报告、Spark 运行摘要和 API 验证结果在 reports/；真实页面截图在 screenshots/。

## 8. 数据与隐私

- 所有患者、证件号、手机号、医生 ID 均为程序生成的虚构数据，不对应真实个人。
- 模拟证件号仅用于演示 18 位格式，不是真实有效身份证号。
- 密码只通过环境变量/本地 .env.local 提供；仓库和压缩包不包含真实口令。
- 原始问卷/飞书文档未放入交付物；需求提取记录见 docs/01-需求来源与核对.md。

## 9. 许可与引用

- 项目代码用于课程实训，可自行修改。
- 需求来源：飞书公开文档《慢性病大数据项目》（2026-10-11 版本），通过浏览器访问并提取正文与代码块；详见 docs/01。
- 技术组件：Apache Spark 3.3.4、Hadoop 3.3.6、Hive 3.1.3、MySQL 8.0、Spring Boot 2.7.18、Vue 3。