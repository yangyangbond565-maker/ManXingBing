# API 冒烟测试并保存 JSON 证据
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot
$base = 'http://127.0.0.1:8080/api'
$endpoints = @(
  'health','dashboard/overview','patient-profile','disease-distribution',
  'risk-factors?factor=smoking','visits?type=type','medications?type=top',
  'trend?grain=year','health-score/overview','health-score/patients?page=1&size=2',
  'data-quality','modules','patients?page=1&size=2','patients/1'
)
$results = @()
foreach ($e in $endpoints) {
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $r = Invoke-RestMethod -Uri "$base/$e" -TimeoutSec 20
    $sw.Stop()
    $results += [pscustomobject]@{ endpoint=$e; http=200; code=$r.code; ms=$sw.ElapsedMilliseconds; ok=($r.code -eq 0) }
    Write-Host ("OK  {0,-55} {1}ms" -f $e, $sw.ElapsedMilliseconds) -ForegroundColor Green
  } catch {
    $sw.Stop()
    $results += [pscustomobject]@{ endpoint=$e; http=0; code=-1; ms=$sw.ElapsedMilliseconds; ok=$false; error=$_.Exception.Message }
    Write-Host ("ERR {0,-55} {1}" -f $e, $_.Exception.Message) -ForegroundColor Red
  }
}
$out = Join-Path $root 'reports\api_test_report.json'
$json = $results | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($out, $json, (New-Object System.Text.UTF8Encoding($false)))
$failed = @($results | Where-Object { -not $_.ok }).Count
Write-Host "结果: $($results.Count) 个接口, 失败 $failed, 报告 $out"
if ($failed -gt 0) { exit 1 }
