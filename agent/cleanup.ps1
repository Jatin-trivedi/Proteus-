Write-Host "[+] Killing agent processes..." -ForegroundColor Cyan
Get-Process agent_console,agent_console_garbled,agent,agent_garbled,runtimebroker -EA SilentlyContinue | Stop-Process -Force

Write-Host "[+] Killing leftover test targets..." -ForegroundColor Cyan
Get-Process cmd -EA SilentlyContinue | Where-Object { $_.Id -ne $PID } | Stop-Process -Force

Write-Host "[+] Removing persistence..." -ForegroundColor Cyan
Remove-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name RuntimeBroker -EA SilentlyContinue
Remove-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name WindowsCacheStore -EA SilentlyContinue
Remove-Item "$env:APPDATA\Microsoft\Windows\RuntimeBroker" -Recurse -Force -EA SilentlyContinue

Write-Host "[+] Removing markers..." -ForegroundColor Cyan
Remove-Item "$env:TEMP\INJ_*.txt" -EA SilentlyContinue
Remove-Item "C:\Windows\Temp\INJ_*.txt" -EA SilentlyContinue

Write-Host "[+] Removing extracted DLLs..." -ForegroundColor Cyan
Get-ChildItem "$env:TEMP\tmp_*.dll" -EA SilentlyContinue | Remove-Item -Force
Get-ChildItem "$env:TEMP\winlogon_*.dll" -EA SilentlyContinue | Remove-Item -Force

Write-Host "[+] Removing test artifacts..." -ForegroundColor Cyan
Remove-Item "$env:TEMP\test_input.exe" -EA SilentlyContinue
Remove-Item "$env:TEMP\garbled_run.log" -EA SilentlyContinue

Write-Host ""
Write-Host "[+] Cleanup complete." -ForegroundColor Green