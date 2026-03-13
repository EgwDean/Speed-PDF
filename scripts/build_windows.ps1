$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Could not find Python in .venv."
}

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt -r requirements-dev.txt
& $python scripts/generate_icon.py

if (-not (Test-Path "assets\app.ico")) {
    throw "Icon not found at assets\app.ico"
}

if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }

& $python -m PyInstaller --noconfirm --clean --windowed --onefile --name "Speed-PDF" --icon "assets\app.ico" app.py

$iscc = Get-Command "iscc" -ErrorAction SilentlyContinue
if ($null -eq $iscc) {
    Write-Host "PyInstaller build complete. Inno Setup Compiler (iscc) not found on PATH."
    Write-Host "Install Inno Setup 6 and run: iscc installer\SpeedPDF.iss"
    exit 0
}

& iscc "installer\SpeedPDF.iss"
Write-Host "Installer created in dist\installer"
