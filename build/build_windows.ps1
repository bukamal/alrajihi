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
  --additional-hooks-dir build/hooks `
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
  --collect-submodules alrajhi_client.database `
  --collect-submodules alrajhi_client.database.repositories `
  --collect-submodules alrajhi_client.database.dao `
  --collect-submodules database `
  --collect-submodules database.repositories `
  --collect-submodules database.dao `
  --collect-submodules alrajhi_client.gateways.local `
  --collect-submodules gateways.local `
  --collect-data printing `
  --collect-data alrajhi_client.printing `
  --hidden-import printing._template_loader `
  --hidden-import printing.print_templates `
  --hidden-import printing.printing_service `
  --hidden-import printing.print_manager `
  --hidden-import printing.thermal_printer `
  --hidden-import printing.label_designer `
  --hidden-import alrajhi_client.printing._template_loader `
  --hidden-import alrajhi_client.printing.print_templates `
  --hidden-import alrajhi_client.printing.printing_service `
  --hidden-import alrajhi_client.printing.print_manager `
  --hidden-import database.repositories.audit_repo `
  --hidden-import database.repositories.base_repo `
  --hidden-import database.repositories.branch_repo `
  --hidden-import database.repositories.cashbox_repo `
  --hidden-import database.repositories.customer_repo `
  --hidden-import database.repositories.expense_repo `
  --hidden-import database.repositories.inventory_movement_repo `
  --hidden-import database.repositories.invoice_repo `
  --hidden-import database.repositories.item_repo `
  --hidden-import database.repositories.manufacturing_repo `
  --hidden-import database.repositories.reporting_repo `
  --hidden-import database.repositories.settings_repo `
  --hidden-import database.repositories.supplier_repo `
  --hidden-import database.repositories.user_repo `
  --hidden-import database.repositories.voucher_repo `
  --hidden-import database.repositories.warehouse_repo `
  --hidden-import alrajhi_client.database.repositories.audit_repo `
  --hidden-import alrajhi_client.database.repositories.base_repo `
  --hidden-import alrajhi_client.database.repositories.branch_repo `
  --hidden-import alrajhi_client.database.repositories.cashbox_repo `
  --hidden-import alrajhi_client.database.repositories.customer_repo `
  --hidden-import alrajhi_client.database.repositories.expense_repo `
  --hidden-import alrajhi_client.database.repositories.inventory_movement_repo `
  --hidden-import alrajhi_client.database.repositories.invoice_repo `
  --hidden-import alrajhi_client.database.repositories.item_repo `
  --hidden-import alrajhi_client.database.repositories.manufacturing_repo `
  --hidden-import alrajhi_client.database.repositories.reporting_repo `
  --hidden-import alrajhi_client.database.repositories.settings_repo `
  --hidden-import alrajhi_client.database.repositories.supplier_repo `
  --hidden-import alrajhi_client.database.repositories.user_repo `
  --hidden-import alrajhi_client.database.repositories.voucher_repo `
  --hidden-import alrajhi_client.database.repositories.warehouse_repo `
  --hidden-import database.dao.branch_dao `
  --hidden-import database.dao.cashbox_dao `
  --hidden-import database.dao.category_dao `
  --hidden-import database.dao.customer_dao `
  --hidden-import database.dao.expense_dao `
  --hidden-import database.dao.inventory_dao `
  --hidden-import database.dao.inventory_ledger_dao `
  --hidden-import database.dao.inventory_movement_dao `
  --hidden-import database.dao.invoice_dao `
  --hidden-import database.dao.item_dao `
  --hidden-import database.dao.manufacturing_dao `
  --hidden-import database.dao.reporting_dao `
  --hidden-import database.dao.supplier_dao `
  --hidden-import database.dao.voucher_dao `
  --hidden-import database.dao.warehouse_dao `
  --hidden-import alrajhi_client.database.dao.branch_dao `
  --hidden-import alrajhi_client.database.dao.cashbox_dao `
  --hidden-import alrajhi_client.database.dao.category_dao `
  --hidden-import alrajhi_client.database.dao.customer_dao `
  --hidden-import alrajhi_client.database.dao.expense_dao `
  --hidden-import alrajhi_client.database.dao.inventory_dao `
  --hidden-import alrajhi_client.database.dao.inventory_ledger_dao `
  --hidden-import alrajhi_client.database.dao.inventory_movement_dao `
  --hidden-import alrajhi_client.database.dao.invoice_dao `
  --hidden-import alrajhi_client.database.dao.item_dao `
  --hidden-import alrajhi_client.database.dao.manufacturing_dao `
  --hidden-import alrajhi_client.database.dao.reporting_dao `
  --hidden-import alrajhi_client.database.dao.supplier_dao `
  --hidden-import alrajhi_client.database.dao.voucher_dao `
  --hidden-import alrajhi_client.database.dao.warehouse_dao `
  --hidden-import database.connection `
  --hidden-import database.migrations `
  --hidden-import database.models `
  --hidden-import database.schema_manager `
  --hidden-import alrajhi_client.database.connection `
  --hidden-import alrajhi_client.database.migrations `
  --hidden-import alrajhi_client.database.models `
  --hidden-import alrajhi_client.database.schema_manager `
  --hidden-import gateways.local.user_gateway `
  --hidden-import alrajhi_client.gateways.local.user_gateway `
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
  --add-data "alrajhi_client\printing\print_templates.py;printing" `
  --add-data "alrajhi_client\printing\print_templates.py;alrajhi_client\printing" `
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
