
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO = "utf-8"

$scriptPath = Join-Path $PSScriptRoot "run_test.py"
$pythonPath = "d:\ShuttleFlow\venv\Scripts\python.exe"
& $pythonPath $scriptPath

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
