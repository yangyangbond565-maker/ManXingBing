# 停止端口 8080/4173 上的服务（按 PID，注意确认后再执行）
$ErrorActionPreference = 'Continue'
$ports = 8080, 4173
foreach ($port in $ports) {
  $lines = netstat -ano | Select-String ":$port\s"
  foreach ($line in $lines) {
    $parts = ($line.ToString().Trim() -split '\s+')
    if ($parts.Length -ge 5) {
      $procId = $parts[-1]
      if ($procId -match '^\d+$' -and $procId -ne '0') {
        Write-Host "停止端口 $port 的进程 PID=$procId" -ForegroundColor Yellow
        Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue
      }
    }
  }
}
Write-Host '完成。MySQL 服务未停止，如需停止请使用服务管理器。'