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
# программа собирается во временную папку build\dist, в dist\ кладутся только установщик и zip
if (Test-Path build\dist) { Remove-Item build\dist -Recurse -Force }
New-Item -ItemType Directory -Force dist | Out-Null
Remove-Item dist\SmartShellBridge.zip -Force -ErrorAction SilentlyContinue
& $py -m PyInstaller --noconfirm --clean --distpath build\dist --workpath build\work build\SmartShellBridge.spec
if ($LASTEXITCODE -ne 0) { throw "Сборка не удалась" }

Write-Host "== Архив" -ForegroundColor Cyan
Compress-Archive -Path build\dist\SmartShellBridge -DestinationPath dist\SmartShellBridge.zip -Force

Write-Host "== Установщик" -ForegroundColor Cyan
$version = (& $py -c "import sys; sys.path.insert(0,'src'); import ssbridge; print(ssbridge.__version__)").Trim()
$iscc = @("$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe", "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe") |
  Where-Object { Test-Path $_ } | Select-Object -First 1
if ($iscc) {
  Remove-Item dist\SmartShellBridge-Setup-*.exe -Force -ErrorAction SilentlyContinue
  & $iscc /Q "/DAppVersion=$version" build\installer.iss
  if ($LASTEXITCODE -ne 0) { throw "Сборка установщика не удалась" }
  Write-Host "Готово: dist\SmartShellBridge-Setup-$version.exe (установщик), dist\SmartShellBridge.zip (портативная версия)" -ForegroundColor Green
} else {
  Write-Host "Inno Setup не найден — установщик не собран (winget install JRSoftware.InnoSetup)" -ForegroundColor Yellow
  Write-Host "Готово: dist\SmartShellBridge.zip" -ForegroundColor Green
}
