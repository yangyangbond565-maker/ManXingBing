# 启动 Spring Boot 后端（Windows PowerShell）
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here
if (Test-Path '.env.local') {
  Get-Content '.env.local' | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith('#') -and $line.Contains('=')) {
      $k, $v = $line.Split('=', 2)
      [Environment]::SetEnvironmentVariable($k.Trim(), $v.Trim(), 'Process')
    }
  }
} else {
  Write-Host '未找到 backend/.env.local，请先复制 .env.example 并填写数据库口令。' -ForegroundColor Yellow
}
$jdk = 'C:\Program Files\Java\graalvm-jdk-21.0.7+8.1'
if (Test-Path $jdk) { $env:JAVA_HOME = $jdk; $env:Path = "$jdk\bin;$env:Path" }
$jar = Join-Path $here 'target\chronic-disease-backend.jar'
if (-not (Test-Path $jar)) {
  Write-Host '未找到 jar，先执行：mvn "-Dmaven.repo.local=D:\官方工作区\.tools\m2repo" -DskipTests package' -ForegroundColor Yellow
  exit 1
}
Write-Host "启动后端 http://127.0.0.1:$($env:SERVER_PORT) ..."
& java -jar $jar
