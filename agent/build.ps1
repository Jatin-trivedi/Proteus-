param([switch]$Console, [switch]$SkipGarble)

$ErrorActionPreference = "Stop"

$GO_SDK = "C:\Users\HP\sdk\go1.26.5"
if (-not (Test-Path "$GO_SDK\bin\go.exe")) {
    Write-Host "[-] Go SDK missing at $GO_SDK"
    exit 1
}
$env:GOROOT = $GO_SDK
$env:GOTOOLCHAIN = "local"
$env:PATH = "$GO_SDK\bin;$env:PATH"
Write-Host "[+] Go: $(& go version)" -ForegroundColor Green

Set-Location $PSScriptRoot

if (-not (Test-Path "$PSScriptRoot\libjockey.enc")) {
    Write-Host "[-] libjockey.enc not found"
    exit 1
}
$encSize = (Get-Item "$PSScriptRoot\libjockey.enc").Length
Write-Host "[+] Encrypted DLL: libjockey.enc ($encSize bytes)" -ForegroundColor Green

$env:CGO_ENABLED = "0"

if ($Console) {
    $plain   = "agent_console.exe"
    $garbled = "agent_console_garbled.exe"
    $ldflags = "-s -w"
} else {
    $plain   = "agent.exe"
    $garbled = "agent_garbled.exe"
    $ldflags = "-s -w -H windowsgui"
}

Write-Host ""
Write-Host "=== [1/3] Plain build ===" -ForegroundColor Cyan
go build -trimpath -ldflags $ldflags -o $plain .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Plain build failed"
    exit 1
}
$sz = [math]::Round((Get-Item $plain).Length/1024,1)
Write-Host "[+] $plain ($sz KB)" -ForegroundColor Green

if (-not $SkipGarble) {
    Write-Host ""
    Write-Host "=== [2/3] Garbled build ===" -ForegroundColor Cyan

    $garbleExe = "$env:USERPROFILE\go\bin\garble.exe"
    if (-not (Test-Path $garbleExe)) {
        Write-Host "[-] garble not found: $garbleExe"
        exit 1
    }

    cmd /c "`"$garbleExe`" -literals -tiny -seed=random build -trimpath -ldflags `"$ldflags`" -o $garbled ."
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $garbled)) {
        Write-Host "[-] garble failed"
        exit 1
    }
    $sz2 = [math]::Round((Get-Item $garbled).Length/1024,1)
    Write-Host "[+] $garbled ($sz2 KB)" -ForegroundColor Green

    $h1 = (Get-FileHash $plain -Algorithm SHA256).Hash
    $h2 = (Get-FileHash $garbled -Algorithm SHA256).Hash
    Write-Host ""
    Write-Host "=== Hash comparison ===" -ForegroundColor Cyan
    Write-Host "  plain:   $h1"
    Write-Host "  garbled: $h2"
    if ($h1 -ne $h2) {
        Write-Host "  [+] Hashes differ - obfuscation applied" -ForegroundColor Green
    } else {
        Write-Host "  [!] Hashes identical" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "=== [3/3] Import table ===" -ForegroundColor Cyan
if ($SkipGarble) { $target = $plain } else { $target = $garbled }
objdump -p $target | Select-String "DLL Name"

Write-Host ""
Write-Host "[+] Build complete." -ForegroundColor Cyan