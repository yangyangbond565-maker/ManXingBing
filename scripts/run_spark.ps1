# 运行 PySpark 8 模块（Windows 本地模式）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$missing = @()
foreach ($name in 'SPARK_HOME','HADOOP_HOME','PYTHON310','MYSQL_JDBC_JAR','CHRONIC_DB_PASSWORD') {
  if (-not (Get-Item "Env:$name" -ErrorAction SilentlyContinue)) { $missing += $name }
}
if ($missing.Count -gt 0) {
  throw "缺少环境变量: $($missing -join ', ')。请按 README 4.3 设置。"
}
$env:SPARK_HOME = (Resolve-Path $env:SPARK_HOME).Path
$env:HADOOP_HOME = (Resolve-Path $env:HADOOP_HOME).Path
$env:MYSQL_JDBC_JAR = (Resolve-Path $env:MYSQL_JDBC_JAR).Path
$env:PYTHON310 = (Resolve-Path $env:PYTHON310).Path
$env:PYSPARK_PYTHON = $env:PYTHON310
$env:PYSPARK_DRIVER_PYTHON = $env:PYTHON310
$env:PYTHONIOENCODING = 'utf-8'
$jdbc = $env:MYSQL_JDBC_JAR
$cp = "$env:SPARK_HOME\jars\*;$jdbc"

Write-Host '运行 Spark SQL 八模块...' -ForegroundColor Cyan
$javaArgs = @(
  '-Xmx5g',
  '-Dfile.encoding=UTF-8',
  "-Djava.library.path=$env:HADOOP_HOME\bin",
  '-cp', $cp,
  'org.apache.spark.deploy.SparkSubmit',
  '--master', 'local[4]',
  '--conf', 'spark.ui.enabled=false',
  '--conf', 'spark.sql.shuffle.partitions=8',
  '--conf', "spark.driver.extraClassPath=$jdbc",
  '--conf', "spark.executor.extraClassPath=$jdbc",
  'spark\chronic_disease_analysis.py'
)
& java.exe @javaArgs *> 'logs\spark_run.log'

if ($LASTEXITCODE -ne 0) {
  Write-Host 'Spark 运行失败，最后 80 行日志：' -ForegroundColor Red
  Get-Content 'logs\spark_run.log' -Tail 80
  exit $LASTEXITCODE
}
Write-Host 'Spark 运行完成，结果已写入 MySQL ads_*。' -ForegroundColor Green
