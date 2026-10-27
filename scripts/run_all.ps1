# 端到端流水线：生成 -> 入库 -> 质量 -> ODS -> Spark -> 元数据
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = "$root\python;$root\python\vendor"
if (-not (Get-Item Env:CHRONIC_DB_PASSWORD -ErrorAction SilentlyContinue)) {
  throw '请先设置 CHRONIC_DB_PASSWORD。'
}
if (-not (Get-Item Env:CHRONIC_WEBHDFS -ErrorAction SilentlyContinue)) { $env:CHRONIC_WEBHDFS = 'http://192.168.20.135:9870/webhdfs/v1' }
if (-not (Get-Item Env:CHRONIC_HDFS_HOST -ErrorAction SilentlyContinue)) { $env:CHRONIC_HDFS_HOST = '192.168.20.135' }
if (-not (Get-Item Env:CHRONIC_ODS_DIR -ErrorAction SilentlyContinue)) { $env:CHRONIC_ODS_DIR = 'hdfs://192.168.20.135:9000/warehouse/chronic_disease/ods' }
if (-not (Get-Item Env:CHRONIC_ADS_HDFS -ErrorAction SilentlyContinue)) { $env:CHRONIC_ADS_HDFS = 'hdfs://192.168.20.135:9000/warehouse/chronic_disease/ads' }

Write-Host '[1/6] 生成 100,000 名患者...' -ForegroundColor Cyan
& python -m chronic_disease.generate --patients 100000 --seed 20261020
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '[2/6] 批量导入 MySQL...' -ForegroundColor Cyan
& python -m chronic_disease.load_mysql --truncate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '[3/6] 数据质量检查...' -ForegroundColor Cyan
& python -m chronic_disease.quality_check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '[4/6] 通过 WebHDFS 导出 ODS 到 HDFS...' -ForegroundColor Cyan
& python -m chronic_disease.sync_mysql_to_hive --mode webhdfs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '[5/6] Spark SQL 八模块（HDFS 输入 + MySQL/HDFS 输出）...' -ForegroundColor Cyan
& powershell -ExecutionPolicy Bypass -File "$PSScriptRoot\run_spark.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '[6/6] 写入模块 KPI 元数据...' -ForegroundColor Cyan
& python -m chronic_disease.load_metadata
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host '流水线完成。Hive ODS/ADS DDL 请在 VM 上执行 sql/hive/01_ods.sql、03_ads.sql。' -ForegroundColor Green