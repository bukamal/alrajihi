$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$IconPath = Join-Path $Root "alrajhi_client\assets\brand\app.ico"
if (!(Test-Path $IconPath)) {
    throw "Missing application icon: $IconPath"
}

python tools\verify_branding_assets.py
python tools\phase32_windows_import_guard.py

python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install pyinstaller

$extra = @()
foreach ($dll in @("libiconv.dll", "libzbar-64.dll", "libzbar-32.dll")) {
    if (Test-Path $dll) {
        $extra += "--add-binary"
        $extra += "$dll;."
    }
}

$QtPlatforms = python -c "import PyQt5, os; print(os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins', 'platforms'))"

pyinstaller `
  --clean `
  --noconfirm `
  --onedir `
  --windowed `
  --name AlrajhiAccounting `
  --icon "$IconPath" `
  --paths alrajhi_client `
  --paths . `
  --collect-all PyQt5 `
  --collect-all pyzbar `
  --collect-all cv2 `
  --collect-all qrcode `
  --collect-all barcode `
  --collect-all qtawesome `
  --collect-all pyqtgraph `
  --hidden-import pyzbar.pyzbar `
  --hidden-import cv2 `
  --hidden-import qrcode `
  --hidden-import barcode `
  --hidden-import decimal `
  --hidden-import sqlite3 `
  --hidden-import requests `
  --hidden-import cryptography `
  --hidden-import openpyxl `
  --hidden-import reportlab `
  --hidden-import waitress `
  --hidden-import flask `
  --hidden-import views.restaurant `
  --hidden-import views.restaurant.restaurant_dashboard `
  --hidden-import views.restaurant.table_map_widget `
  --hidden-import views.restaurant.restaurant_pos_widget `
  --hidden-import views.restaurant.kitchen_display_widget `
  --hidden-import views.restaurant.restaurant_analytics_widget `
  --hidden-import core.services.restaurant_service `
  --hidden-import gateways.restaurant_gateway `
  --hidden-import gateways.local.restaurant_gateway `
  --hidden-import gateways.remote.restaurant_gateway `
  --hidden-import flask_jwt_extended `
  --add-data "$QtPlatforms;platforms" `
  --add-data "alrajhi_client\assets\brand;assets\brand" `
  @extra `
  alrajhi_client\main.py

if (!(Test-Path "dist\AlrajhiAccounting\AlrajhiAccounting.exe")) {
    throw "PyInstaller build failed: missing EXE"
}

New-Item -ItemType Directory -Force -Path output | Out-Null
$Inno = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if (Test-Path $Inno) {
    & $Inno build\setup.iss
} else {
    Write-Warning "Inno Setup not found. Portable EXE was built, installer was not built."
}
