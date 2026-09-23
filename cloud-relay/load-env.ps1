Get-Content "C:\Users\HP\Desktop\Proteus 2.0\Proteus-\cloud-relay\.env" | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2].Trim(), "Process")
    }
}