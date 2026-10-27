# 初始化 MySQL 七张业务表 + ADS 结果表
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PYTHONPATH = "$root\python;$root\python\vendor"
if (-not (Get-Item Env:CHRONIC_DB_PASSWORD -ErrorAction SilentlyContinue)) {
  throw '请先设置 CHRONIC_DB_PASSWORD（或通过 backend/.env.local 注入）。'
}
& python -m chronic_disease.load_mysql --init
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host '数据库建表完成。' -ForegroundColor Green
