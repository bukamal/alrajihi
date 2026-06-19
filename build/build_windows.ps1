$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$IconPath = Join-Path $Root "alrajhi_client\assets\brand\app.ico"
if (!(Test-Path $IconPath)) {
    throw "Missing application icon: $IconPath"
}

python tools\verify_branding_assets.py
python tools\phase32_windows_import_guard.py
python tools\release_packaging_guard.py
python tools\release_translations_guard.py
python tools\release_theme_guard.py
python tools\release_hidden_imports_guard.py
python tools\unified_printing_guard.py

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
  --collect-submodules alrajhi_client.features `
  --collect-submodules alrajhi_client.workspace `
  --collect-submodules alrajhi_client.shell `
  --collect-submodules alrajhi_client.ui `
  --collect-submodules alrajhi_client.views.restaurant `
  --collect-submodules alrajhi_client.printing `
  --collect-submodules features `
  --collect-submodules workspace `
  --collect-submodules shell `
  --collect-submodules ui `
  --collect-submodules views.restaurant `
  --collect-submodules printing `
  --hidden-import printing.print_templates `
  --hidden-import printing.printing_service `
  --hidden-import printing.print_manager `
  --hidden-import printing.thermal_printer `
  --hidden-import printing.label_designer `
  --hidden-import alrajhi_client.printing.print_templates `
  --hidden-import alrajhi_client.printing.printing_service `
  --hidden-import alrajhi_client.printing.print_manager `
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
  --hidden-import features.items.item_editor_tab `
  --hidden-import features.categories.category_editor_tab `
  --hidden-import features.invoices.invoice_editor_tab `
  --hidden-import features.returns.return_editor_tabs `
  --hidden-import features.parties.party_editor_tab `
  --hidden-import features.vouchers.voucher_editor_tab `
  --hidden-import features.finance.documents.cashbox_document_tab `
  --hidden-import features.finance.documents.bank_account_document_tab `
  --hidden-import features.finance.documents.expense_document_tab `
  --hidden-import features.branches.documents.branch_document_tab `
  --hidden-import features.inventory.documents.warehouse_document_tab `
  --hidden-import features.inventory.documents.inventory_transfer_document_tab `
  --hidden-import features.users.documents.user_document_tab `
  --hidden-import features.transactions.transaction_document_tab `
  --hidden-import features.transactions.documents.sales_invoice_tab `
  --hidden-import features.transactions.documents.purchase_invoice_tab `
  --hidden-import features.transactions.documents.sales_return_tab `
  --hidden-import features.transactions.documents.purchase_return_tab `
  --hidden-import features.manufacturing.bom_document_tab `
  --hidden-import features.manufacturing.production_order_document_tab `
  --hidden-import features.settings.settings_document_tabs `
  --hidden-import features.transactions.components.transaction_document_layout `
  --hidden-import features.transactions.grids.transaction_line_grid `
  --hidden-import workspace.documents.base_document_tab `
  --hidden-import shell.tab_workspace `
  --hidden-import shell.quick_open_dialog `
  --hidden-import flask_jwt_extended `
  --add-data "$QtPlatforms;platforms" `
  --add-data "alrajhi_client\assets;assets" `
  --add-data "alrajhi_client\assets;alrajhi_client\assets" `
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
