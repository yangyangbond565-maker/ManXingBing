# 启动前端 preview（需先 npm run build）
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location "$root\frontend"
if (-not (Test-Path 'dist\index.html')) {
  Write-Host '未找到 dist，先执行 npm run build...' -ForegroundColor Yellow
  npm run build
}
npm run preview
