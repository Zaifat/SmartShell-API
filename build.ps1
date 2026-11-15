﻿# Сборка SmartShell Bridge (папка с программой + zip-архив для раздачи)
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

Write-Host "== Сборка" -ForegroundColor Cyan
if (Test-Path dist\SmartShellBridge) { Remove-Item dist\SmartShellBridge -Recurse -Force }
Remove-Item dist\SmartShellBridge.exe, dist\SmartShellBridge.zip -Force -ErrorAction SilentlyContinue
& $py -m PyInstaller --noconfirm --clean --distpath dist --workpath build\work build\SmartShellBridge.spec
if ($LASTEXITCODE -ne 0) { throw "Сборка не удалась" }

Write-Host "== Архив" -ForegroundColor Cyan
Compress-Archive -Path dist\SmartShellBridge -DestinationPath dist\SmartShellBridge.zip -Force

Write-Host "Готово: dist\SmartShellBridge\SmartShellBridge.exe и dist\SmartShellBridge.zip" -ForegroundColor Green
