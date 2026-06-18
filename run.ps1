# CROWN & OAK - Lowsec Scout hourly recorder (PowerShell alternative to run.bat)
# Schedule with:
#   schtasks /Create /SC HOURLY /TN "EVE Lowsec Scout" /TR "powershell -NoProfile -ExecutionPolicy Bypass -File C:\Users\sales\eve-scout\run.ps1"
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
# Capture the child's output and append as UTF-8. Do NOT use `*>> file` here: in
# Windows PowerShell that re-encodes the child's UTF-8 stdout to UTF-16 LE and
# produces a garbled, mixed-encoding log.
Add-Content -LiteralPath "scout.log" -Value "==== $stamp ====" -Encoding utf8
$out = & $py lowsec_scout.py --no-threat 2>&1 | Out-String
Add-Content -LiteralPath "scout.log" -Value $out -Encoding utf8
# commit + push the page
$pub = & cmd /c "`"$PSScriptRoot\publish.bat`"" 2>&1 | Out-String
Add-Content -LiteralPath "scout.log" -Value $pub -Encoding utf8
