# Сборка SmartShellBridge.exe (один файл, без установки Python у пользователя)
# Запуск:  powershell -ExecutionPolicy Bypass -File build.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path .venv)) { python -m venv .venv }
$py = ".venv\Scripts\python.exe"
& $py -m pip install --upgrade pip -q
& $py -m pip install -r requirements-dev.txt -q

Write-Host "== Тесты" -ForegroundColor Cyan
& $py -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Тесты не прошли" }

Write-Host "== Иконка" -ForegroundColor Cyan
& $py build\make_icon.py

Write-Host "== Сборка exe" -ForegroundColor Cyan
& $py -m PyInstaller --noconfirm --clean --distpath dist --workpath build\work build\SmartShellBridge.spec
if ($LASTEXITCODE -ne 0) { throw "Сборка не удалась" }

Write-Host "Готово: dist\SmartShellBridge.exe" -ForegroundColor Green
